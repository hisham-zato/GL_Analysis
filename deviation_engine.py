"""
Deviation Engine (GL Monthly Analysis)
--------------------------------------

Public API:
  - build_deviation_report(results_df, cfg=None) -> pd.DataFrame
  - DeviationConfig()   # editable config
  - default_config_dict() / config_from_dict() helpers
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple
import math
import re

import numpy as np
import pandas as pd


# -----------------------------
# Safe parsing helpers
# -----------------------------
def to_float(x: Any) -> float:
    """Convert to float, returning NaN on blanks / errors."""
    try:
        if x is None:
            return float("nan")
        if isinstance(x, (bool, np.bool_)):
            return float("nan")
        return float(x)
    except Exception:
        return float("nan")


def to_bool(x: Any) -> Optional[bool]:
    """Convert common truthy/falsey values to bool; returns None when unknown."""
    if x is None:
        return None
    if isinstance(x, (float, np.floating)) and math.isnan(x):
        return None
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, str):
        s = x.strip().lower()
        if s in {"true", "t", "1", "yes", "y"}:
            return True
        if s in {"false", "f", "0", "no", "n"}:
            return False
    return None


# -----------------------------
# Metric detection + percentiles
# -----------------------------
def detect_metrics(columns: List[str]) -> List[str]:
    """Detect metric prefixes like Credit/Debit/Running_Balance/GST from '<Metric>_CY_Mean' columns."""
    metrics = set()
    for c in columns:
        m = re.match(r"^(.*)_CY_Mean$", c)
        if m:
            metrics.add(m.group(1))
    pref = ["Credit", "Debit", "Running_Balance", "GST"]
    return sorted(metrics, key=lambda x: (pref.index(x) if x in pref else 999, x))


def percentile_rank_abs(df: pd.DataFrame, metric: str, suffix: str) -> pd.Series:
    """Percentile rank (0..1) of abs(metric_suffix) within the dataset. NaNs stay NaN."""
    col = f"{metric}_{suffix}"
    if col not in df.columns:
        return pd.Series(np.nan, index=df.index)

    vals = pd.to_numeric(df[col], errors="coerce").abs().replace([np.inf, -np.inf], np.nan)
    non_null = vals.dropna()
    if non_null.empty:
        return pd.Series(np.nan, index=df.index)

    ranks = non_null.rank(pct=True)
    out = pd.Series(np.nan, index=df.index)
    out.loc[ranks.index] = ranks
    return out


# -----------------------------
# Config (thresholds, weights, tiers, language)
# -----------------------------
@dataclass
class Thresholds:
    # volatility
    high_cv: float = 1.0
    moderate_cv: float = 0.7

    # skew proxy (mean vs median)
    mean_median_gap_ratio: float = 0.38

    # Pearson skew proxy: 3*(mean-median)/std
    pearson_skew_abs: float = 1.2

    # relative movement (fallback when significance isn't present)
    rel_mean_shift: float = 0.75
    rel_std_jump: float = 0.80

    # effect size (Cohen's d)
    cohens_d_large: float = 0.8
    cohens_d_medium: float = 0.5

    # sign reversal gate
    sign_reversal_min_mean_pct: float = 0.60

    # new activity
    new_activity_factor: float = 10.0


@dataclass
class Weights:
    distribution_change: int = 5
    mean_shift: int = 5
    effect_large: int = 4
    effect_medium: int = 2
    high_cv: int = 2
    moderate_cv: int = 1
    mean_median_gap: int = 2
    pearson_skew: int = 1
    volatility_jump: int = 2
    low_mean_high_variance: int = 2
    new_activity: int = 2
    sign_reversal: int = 3


@dataclass
class MetricProfile:
    """
    Profiles let you treat metrics differently.
    Example: Running_Balance tends to look "large" a lot, so gate it harder.
    """
    name: str

    # materiality gates (percentiles of abs(CY mean))
    min_mean_pct_for_cv: float = 0.60
    min_mean_pct_for_effect: float = 0.30

    # per-metric weight multipliers
    effect_weight_mult: float = 1.0
    cv_weight_mult: float = 1.0

    # low-mean/high-variance trigger
    low_mean_pct: float = 0.30
    high_std_pct: float = 0.70


def default_profiles() -> Dict[str, MetricProfile]:
    return {
        "Credit": MetricProfile("Credit", min_mean_pct_for_cv=0.60, min_mean_pct_for_effect=0.60),
        "Debit": MetricProfile("Debit", min_mean_pct_for_cv=0.30, min_mean_pct_for_effect=0.30),
        "Running_Balance": MetricProfile(
            "Running_Balance",
            min_mean_pct_for_cv=0.75,
            min_mean_pct_for_effect=0.78,
            effect_weight_mult=0.7,
            cv_weight_mult=0.8,
        ),
        "GST": MetricProfile(
            "GST",
            min_mean_pct_for_cv=0.40,
            min_mean_pct_for_effect=0.45,
            effect_weight_mult=0.9,
            cv_weight_mult=0.9,
        ),
    }


@dataclass
class Tiering:
    tier1_min_score: int = 14
    tier2_min_score: int = 7
    tier3_min_score: int = 5

    include_tier3: bool = False
    max_tier1: int = 10

    tier1_materiality_pct: float = 0.75
    tier1_override_score: int = 28

    drop_pure_volatility_below_mean_pct: float = 0.80

    require_any_of_triggers: Tuple[str, ...] = (
        "Distribution Change",
        "Mean Shift",
        "Large Effect Size",
        "Low Mean with High Variance",
        "New Activity / Re-start",
        "Sign Reversal",
        "High CV",
        "Mean-Median Gap",
    )


@dataclass
class Language:
    bucket_finish: Dict[str, str] = field(default_factory=lambda: {
        "revenue": "Check cut-off, pricing/mix changes, and recognition timing.",
        "cash": "Often driven by batch journals, timing, bank rule changes, or missed automation.",
        "timing": "Common causes are accruals vs prepaids, one-offs, or timing corrections.",
        "clearing": "Usually points to reconciliation gaps, clearing discipline, or mis-postings into control accounts.",
        "tax": "Validate coding, rate mapping, and whether supply classification changed.",
        "rounding": "Unexpected activity can mask systemic posting issues or forced balancing journals.",
        "general": "Often a mix of reclasses, one-offs, or process changes.",
    })


@dataclass
class DeviationConfig:
    thresholds: Thresholds = field(default_factory=Thresholds)
    weights: Weights = field(default_factory=Weights)
    tiers: Tiering = field(default_factory=Tiering)
    profiles: Dict[str, MetricProfile] = field(default_factory=default_profiles)
    language: Language = field(default_factory=Language)

    enabled_checks: Dict[str, bool] = field(default_factory=lambda: {
        "distribution_change": True,
        "mean_shift": True,
        "effect_size": True,
        "cv": True,
        "mean_median_gap": True,
        "pearson_skew": True,
        "volatility_jump": True,
        "low_mean_high_variance": True,
        "new_activity": True,
        "sign_reversal": True,
    })


# -----------------------------
# Config helpers (UI / API)
# -----------------------------
def default_config_dict() -> Dict[str, Any]:
    return asdict(DeviationConfig())


def config_from_dict(d: Dict[str, Any]) -> DeviationConfig:
    cfg = DeviationConfig()

    if "thresholds" in d:
        for k, v in d["thresholds"].items():
            if hasattr(cfg.thresholds, k):
                setattr(cfg.thresholds, k, v)

    if "weights" in d:
        for k, v in d["weights"].items():
            if hasattr(cfg.weights, k):
                setattr(cfg.weights, k, v)

    if "tiers" in d:
        for k, v in d["tiers"].items():
            if hasattr(cfg.tiers, k):
                if k == "require_any_of_triggers":
                    setattr(cfg.tiers, k, tuple(v))
                else:
                    setattr(cfg.tiers, k, v)

    if "enabled_checks" in d:
        for k, v in d["enabled_checks"].items():
            if k in cfg.enabled_checks:
                cfg.enabled_checks[k] = bool(v)

    if "profiles" in d and isinstance(d["profiles"], dict):
        for metric, profd in d["profiles"].items():
            if metric in cfg.profiles:
                for k, v in profd.items():
                    if hasattr(cfg.profiles[metric], k):
                        setattr(cfg.profiles[metric], k, v)
            else:
                mp = MetricProfile(name=str(metric))
                for k, v in profd.items():
                    if hasattr(mp, k):
                        setattr(mp, k, v)
                cfg.profiles[str(metric)] = mp

    if "language" in d and isinstance(d["language"], dict):
        bf = d["language"].get("bucket_finish")
        if isinstance(bf, dict):
            cfg.language.bucket_finish.update({str(k): str(v) for k, v in bf.items()})

    return cfg


# -----------------------------
# Interpretation
# -----------------------------
def bucketize(account_name: str) -> str:
    n = (account_name or "").lower()
    if any(k in n for k in ["sales", "revenue", "income"]):
        return "revenue"
    if any(k in n for k in ["bank", "merchant", "eftpos", "stripe", "fees", "interest"]):
        return "cash"
    if any(k in n for k in ["insurance", "subscription", "subscriptions", "prepaid", "licence", "license", "annual"]):
        return "timing"
    if any(k in n for k in ["payable", "receivable", "deposit", "clearing", "suspense", "control", "intercompany", "loan", "hire purchase", "hp"]):
        return "clearing"
    if any(k in n for k in ["gst", "vat", "tax", "rwt"]):
        return "tax"
    if any(k in n for k in ["rounding", "round off", "round-off"]):
        return "rounding"
    return "general"


def interpret(account_name: str, dominant_metric: str, triggers: List[str], lang: Language) -> str:
    bucket = bucketize(account_name)

    subject = {
        "Credit": "Credit postings",
        "Debit": "Debit postings",
        "Running_Balance": "Balance movements",
        "GST": "GST behaviour",
    }.get(dominant_metric, f"{dominant_metric} behaviour")

    tset = set(triggers)
    bits: List[str] = []
    if "Distribution Change" in tset:
        bits.append("posting pattern changed versus last year")
    if "Mean Shift" in tset:
        bits.append("average level moved materially")
    if "Large Effect Size" in tset:
        bits.append("change looks practically large, not just noise")
    if "High CV" in tset:
        bits.append("volatility is lumpy and irregular")
    if "Low Mean with High Variance" in tset:
        bits.append("small average with outsized variability suggests batching or timing noise")
    if "Mean-Median Gap" in tset:
        bits.append("skew suggests outliers or one-offs")
    if "Pearson Skew" in tset:
        bits.append("outliers likely dominate the movement")
    if "New Activity / Re-start" in tset:
        bits.append("activity appears newly introduced or restarted")
    if "Sign Reversal" in tset:
        bits.append("direction flipped (possible reclass/contra entries)")

    middle = "; ".join(bits) if bits else "shows unusual movement versus last year"
    return f"{subject}: {middle}. {lang.bucket_finish.get(bucket, lang.bucket_finish['general'])}"


# -----------------------------
# Core scoring
# -----------------------------
def build_deviation_report(results_df: pd.DataFrame, cfg: Optional[DeviationConfig] = None) -> pd.DataFrame:
    if cfg is None:
        cfg = DeviationConfig()

    df = results_df.copy()
    if "Account Code" not in df.columns or "Account Name" not in df.columns:
        raise ValueError("Expected columns: 'Account Code', 'Account Name'")

    metrics = detect_metrics(list(df.columns))
    if not metrics:
        raise ValueError("No metrics detected. Expected '<Metric>_CY_Mean' columns.")

    mean_pct = {m: percentile_rank_abs(df, m, "CY_Mean") for m in metrics}
    std_pct = {m: percentile_rank_abs(df, m, "CY_Std") for m in metrics}

    def prof(m: str) -> MetricProfile:
        return cfg.profiles.get(m, MetricProfile(m))

    def pct_ok(series: pd.Series, idx: Any, threshold: float) -> bool:
        p = series.loc[idx]
        return (not pd.isna(p)) and p >= threshold

    rows: List[Dict[str, Any]] = []

    for idx, r in df.iterrows():
        metric_scores: Dict[str, int] = {}
        metric_triggers: Dict[str, List[str]] = {}
        metric_values: Dict[str, str] = {}

        for m in metrics:
            p = prof(m)
            trig: List[str] = []
            score = 0

            ly_mean = to_float(r.get(f"{m}_LY_Mean"))
            cy_mean = to_float(r.get(f"{m}_CY_Mean"))
            ly_std = to_float(r.get(f"{m}_LY_Std"))
            cy_std = to_float(r.get(f"{m}_CY_Std"))
            cy_med = to_float(r.get(f"{m}_CY_Median"))
            mean_diff = to_float(r.get(f"{m}_Mean_Diff"))
            std_diff = to_float(r.get(f"{m}_Std_Diff"))

            t_sig = to_bool(r.get(f"{m}_TTest_Significant"))
            mw_sig = to_bool(r.get(f"{m}_MannWhitney_Significant"))
            ks_sig = to_bool(r.get(f"{m}_KS_Significant"))
            anova_sig = to_bool(r.get(f"{m}_ANOVA_Significant"))

            eff_raw = r.get(f"{m}_Effect_Size")
            eff = str(eff_raw).strip().lower() if eff_raw is not None and not (isinstance(eff_raw, float) and math.isnan(eff_raw)) else ""
            cohens_d = to_float(r.get(f"{m}_Cohens_D"))

            mean_mat = pct_ok(mean_pct[m], idx, p.min_mean_pct_for_cv)
            eff_mat = pct_ok(mean_pct[m], idx, p.min_mean_pct_for_effect)

            cv = float("nan")
            if not (math.isnan(cy_std) or math.isnan(cy_mean)):
                cv = abs(cy_std) / max(abs(cy_mean), 1e-9)

            gap_ratio = float("nan")
            if not (math.isnan(cy_mean) or math.isnan(cy_med)):
                gap_ratio = abs(cy_mean - cy_med) / max(abs(cy_mean), 1e-9)

            pearson_skew = float("nan")
            if not (math.isnan(cy_mean) or math.isnan(cy_med) or math.isnan(cy_std)) and abs(cy_std) > 1e-12:
                pearson_skew = abs(3.0 * (cy_mean - cy_med) / cy_std)

            dist_change = (ks_sig is True) or (mw_sig is True)
            mean_change = (t_sig is True) or (anova_sig is True)

            eff_large = (eff == "large") or (not math.isnan(cohens_d) and abs(cohens_d) >= cfg.thresholds.cohens_d_large)
            eff_med = (eff == "medium") or (not math.isnan(cohens_d) and abs(cohens_d) >= cfg.thresholds.cohens_d_medium)

            if cfg.enabled_checks["distribution_change"] and dist_change:
                if eff_mat or mean_change or eff_large:
                    trig.append("Distribution Change")
                    score += cfg.weights.distribution_change
                else:
                    trig.append("Distribution Change")
                    score += int(cfg.weights.distribution_change * 0.4)

            if cfg.enabled_checks["mean_shift"] and mean_change:
                if eff_mat or eff_large:
                    trig.append("Mean Shift")
                    score += cfg.weights.mean_shift
                else:
                    trig.append("Mean Shift")
                    score += int(cfg.weights.mean_shift * 0.5)
            elif cfg.enabled_checks["mean_shift"]:
                if not (math.isnan(mean_diff) or math.isnan(ly_mean) or math.isnan(cy_mean)):
                    rel = abs(mean_diff) / max(abs(ly_mean), 1e-9)
                    if rel >= cfg.thresholds.rel_mean_shift and eff_mat:
                        trig.append("Mean Shift")
                        score += int(cfg.weights.mean_shift * 0.5)

            if cfg.enabled_checks["effect_size"]:
                big_move = False
                if not (math.isnan(mean_diff) or math.isnan(ly_mean)):
                    big_move = abs(mean_diff) > max(abs(ly_mean), 1e-9) * cfg.thresholds.rel_mean_shift

                if eff_large and (dist_change or mean_change or big_move) and eff_mat:
                    trig.append("Large Effect Size")
                    score += int(cfg.weights.effect_large * p.effect_weight_mult)
                elif eff_med and (dist_change or mean_change) and eff_mat:
                    trig.append("Medium Effect Size")
                    score += int(cfg.weights.effect_medium * p.effect_weight_mult)

            if cfg.enabled_checks["cv"] and not math.isnan(cv):
                if cv >= cfg.thresholds.high_cv and mean_mat:
                    trig.append("High CV")
                    score += int(cfg.weights.high_cv * p.cv_weight_mult)
                elif cv >= cfg.thresholds.moderate_cv and mean_mat:
                    trig.append("Moderate CV")
                    score += int(cfg.weights.moderate_cv * p.cv_weight_mult)

            if cfg.enabled_checks["low_mean_high_variance"] and not math.isnan(cv):
                mp = mean_pct[m].loc[idx]
                if (not pd.isna(mp)) and mp <= p.low_mean_pct and pct_ok(std_pct[m], idx, p.high_std_pct) and cv >= cfg.thresholds.high_cv:
                    trig.append("Low Mean with High Variance")
                    score += cfg.weights.low_mean_high_variance

            if cfg.enabled_checks["mean_median_gap"] and not math.isnan(gap_ratio):
                if gap_ratio >= cfg.thresholds.mean_median_gap_ratio and mean_mat:
                    trig.append("Mean-Median Gap")
                    score += cfg.weights.mean_median_gap

            if cfg.enabled_checks["pearson_skew"] and not math.isnan(pearson_skew):
                if pearson_skew >= cfg.thresholds.pearson_skew_abs and mean_mat:
                    trig.append("Pearson Skew")
                    score += cfg.weights.pearson_skew

            if cfg.enabled_checks["volatility_jump"] and not (math.isnan(std_diff) or math.isnan(ly_std)):
                rel_std = abs(std_diff) / max(abs(ly_std), 1e-9)
                if rel_std >= cfg.thresholds.rel_std_jump and mean_mat:
                    trig.append("Volatility Jump")
                    score += int(cfg.weights.volatility_jump * p.cv_weight_mult)

            if cfg.enabled_checks["new_activity"] and not (math.isnan(ly_mean) or math.isnan(cy_mean)):
                if abs(ly_mean) < 1e-9 and eff_mat and abs(cy_mean) > cfg.thresholds.new_activity_factor * 1e-9:
                    trig.append("New Activity / Re-start")
                    score += cfg.weights.new_activity

            if cfg.enabled_checks["sign_reversal"] and not (math.isnan(ly_mean) or math.isnan(cy_mean)):
                if (ly_mean * cy_mean) < 0 and pct_ok(mean_pct[m], idx, cfg.thresholds.sign_reversal_min_mean_pct):
                    trig.append("Sign Reversal")
                    score += cfg.weights.sign_reversal

            if score > 0:
                metric_scores[m] = score
                metric_triggers[m] = list(dict.fromkeys(trig))

                # store compact numeric evidence for this metric stream
                metric_values[m] = format_metric_values_blob(
                    metric=m,
                    ly_mean=ly_mean,
                    cy_mean=cy_mean,
                    mean_diff=mean_diff,
                    ly_std=ly_std,
                    cy_std=cy_std,
                    cv=cv if not math.isnan(cv) else float("nan"),
                    gap_ratio=gap_ratio if "gap_ratio" in locals() else float("nan"),
                    pearson_skew=pearson_skew if "pearson_skew" in locals() else float("nan"),
                    cohens_d=cohens_d,
                    sig_flags={"t": t_sig, "anova": anova_sig, "mw": mw_sig, "ks": ks_sig},
                    triggers=list(dict.fromkeys(trig)),
                )


        if not metric_scores:
            continue

        total = sum(metric_scores.values())
        if len(metric_scores) >= 2:
            total += 2
        if len(metric_scores) >= 3:
            total += 2

        all_triggers: List[str] = []
        for t in metric_triggers.values():
            all_triggers.extend(t)
        uniq_triggers = list(dict.fromkeys(all_triggers))

        vol_set = {"High CV", "Moderate CV", "Mean-Median Gap", "Volatility Jump", "Pearson Skew"}
        max_mean_pct = max([mean_pct[m].loc[idx] for m in metric_scores.keys() if not pd.isna(mean_pct[m].loc[idx])] or [np.nan])
        if uniq_triggers and all(t in vol_set for t in uniq_triggers):
            if pd.isna(max_mean_pct) or max_mean_pct < cfg.tiers.drop_pure_volatility_below_mean_pct:
                continue

        if cfg.tiers.require_any_of_triggers:
            if not any(t in uniq_triggers for t in cfg.tiers.require_any_of_triggers):
                continue

        dominant_metric = max(metric_scores.items(), key=lambda kv: kv[1])[0]

        if total >= cfg.tiers.tier1_min_score and (
            ((not pd.isna(max_mean_pct)) and max_mean_pct >= cfg.tiers.tier1_materiality_pct)
            or total >= cfg.tiers.tier1_override_score
        ):
            tier = "Tier-1"
        elif total >= cfg.tiers.tier2_min_score:
            tier = "Tier-2"
        elif total >= cfg.tiers.tier3_min_score and cfg.tiers.include_tier3:
            tier = "Tier-3"
        else:
            continue

        priority = [
            "Distribution Change",
            "Mean Shift",
            "Large Effect Size",
            "Low Mean with High Variance",
            "High CV",
            "Mean-Median Gap",
            "Pearson Skew",
            "Volatility Jump",
            "Sign Reversal",
            "New Activity / Re-start",
            "Medium Effect Size",
            "Moderate CV",
        ]
        seen = set()
        ordered: List[str] = []
        for p in priority:
            if p in uniq_triggers and p not in seen:
                ordered.append(p)
                seen.add(p)
        for t in uniq_triggers:
            if t not in seen:
                ordered.append(t)
                seen.add(t)

        # dominant first, then others by score
        metric_order = sorted(metric_scores.items(), key=lambda kv: kv[1], reverse=True)
        ordered_metrics = [m for m, _ in metric_order]

        # limit how many metric streams we print (prevents the string getting too long)
        MAX_METRICS_IN_BLOB = 3
        blob_metrics = ordered_metrics[:MAX_METRICS_IN_BLOB]
        extra = len(ordered_metrics) - len(blob_metrics)

        metric_blob = " | ".join([metric_values.get(m, f"{m}: (no evidence)") for m in blob_metrics])
        if extra > 0:
            metric_blob += f" | +{extra} more"


        rows.append({
            "Tier": tier,
            "Account Code": r.get("Account Code", ""),
            "Account Name": r.get("Account Name", ""),
            "Key Metrics Triggered": ", ".join(ordered[:6]),
            "Metric Values": metric_blob,
            "Accounting Interpretation": interpret(str(r.get("Account Name", "")), dominant_metric, ordered, cfg.language),
            "Score": int(total),
            "Dominant Metric": dominant_metric,
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    tier_rank = {"Tier-1": 1, "Tier-2": 2, "Tier-3": 3}
    out["_tr"] = out["Tier"].map(tier_rank).fillna(9).astype(int)
    out = out.sort_values(["_tr", "Score"], ascending=[True, False]).drop(columns=["_tr"])

    if cfg.tiers.max_tier1 and (out["Tier"] == "Tier-1").sum() > cfg.tiers.max_tier1:
        t1_idxs = out.index[out["Tier"] == "Tier-1"].tolist()
        demote = t1_idxs[cfg.tiers.max_tier1:]
        out.loc[demote, "Tier"] = "Tier-2"
        out["_tr"] = out["Tier"].map(tier_rank).fillna(9).astype(int)
        out = out.sort_values(["_tr", "Score"], ascending=[True, False]).drop(columns=["_tr"])

    return out[[
        "Tier", "Account Code", "Account Name",
        "Key Metrics Triggered",
        "Metric Values",
        "Accounting Interpretation",
        "Score", "Dominant Metric"
    ]]



def validate_input_df(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    issues: List[str] = []
    if df is None or df.empty:
        return False, ["CSV looks empty."]

    for col in ["Account Code", "Account Name"]:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")

    metrics = detect_metrics(list(df.columns))
    if not metrics:
        issues.append("No '<Metric>_CY_Mean' columns found. Input doesn't look like gl_analysis_results_monthly.csv.")

    return len(issues) == 0, issues

def _fmt_num(x: float, max_dec: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    ax = abs(x)
    if ax >= 1e9:
        return f"{x/1e9:.{max_dec}f}b"
    if ax >= 1e6:
        return f"{x/1e6:.{max_dec}f}m"
    if ax >= 1e3:
        return f"{x/1e3:.{max_dec}f}k"
    return f"{x:.{max_dec}f}"


def _fmt_pct(x: float, max_dec: int = 0) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return f"{x*100:.{max_dec}f}%"


def _fmt_rel_change(cy: float, ly: float) -> str:
    if any((ly is None, cy is None)) or (isinstance(ly, float) and math.isnan(ly)) or (isinstance(cy, float) and math.isnan(cy)):
        return ""
    denom = max(abs(ly), 1e-9)
    return f"{(cy - ly)/denom:+.0%}"


def _sig_pack(**flags: Optional[bool]) -> str:
    """
    Packs significance flags into short tokens.
    Only includes known True flags.
    """
    m = {
        "T": flags.get("t"),
        "A": flags.get("anova"),
        "MW": flags.get("mw"),
        "KS": flags.get("ks"),
    }
    hits = [k for k, v in m.items() if v is True]
    return ",".join(hits)


def format_metric_values_blob(
    metric: str,
    ly_mean: float,
    cy_mean: float,
    mean_diff: float,
    ly_std: float,
    cy_std: float,
    cv: float,
    gap_ratio: float,
    pearson_skew: float,
    cohens_d: float,
    sig_flags: Dict[str, Optional[bool]],
    triggers: List[str],
) -> str:
    """
    Single compact string for one metric stream.
    Keeps it readable for accountants, but still dense.
    """

    parts: List[str] = []

    # means (most important)
    if not math.isnan(ly_mean) or not math.isnan(cy_mean):
        s = f"LYμ:{_fmt_num(ly_mean)}" if not math.isnan(ly_mean) else ""
        s2 = f"CYμ:{_fmt_num(cy_mean)}" if not math.isnan(cy_mean) else ""
        rel = _fmt_rel_change(cy_mean, ly_mean)
        if rel:
            rel = f"({rel})"
        means = " ".join([x for x in [s, s2, rel] if x])
        if means:
            parts.append(means)

    # std / cv
    if not math.isnan(cy_std) or not math.isnan(cv):
        stds = []
        if not math.isnan(cy_std):
            stds.append(f"CYσ:{_fmt_num(cy_std)}")
        if not math.isnan(cv):
            stds.append(f"CV:{cv:.2f}")
        parts.append(" ".join(stds))

    # skew proxies (only if relevant / present)
    if not math.isnan(gap_ratio):
        parts.append(f"μ~med:{gap_ratio:.2f}")
    if not math.isnan(pearson_skew):
        parts.append(f"skew:{pearson_skew:.2f}")

    # effect size
    if not math.isnan(cohens_d):
        parts.append(f"d:{cohens_d:.2f}")

    # tests (only show if anything is significant)
    sig = _sig_pack(**sig_flags)
    if sig:
        parts.append(f"sig[{sig}]")

    # keep triggers as short tag hints (optional, helps tie numbers to why it fired)
    # only include the top 2-3 so this doesn't blow up
    if triggers:
        t = []
        for x in triggers:
            if x in {"Distribution Change", "Mean Shift", "Large Effect Size", "High CV", "Low Mean with High Variance", "Mean-Median Gap", "Pearson Skew", "Volatility Jump", "Sign Reversal", "New Activity / Re-start"}:
                t.append(x)
            if len(t) >= 3:
                break
        if t:
            parts.append("tag[" + ",".join(t) + "]")

    core = "; ".join([p for p in parts if p])
    return f"{metric}: {core}" if core else f"{metric}: (no numeric evidence)"
