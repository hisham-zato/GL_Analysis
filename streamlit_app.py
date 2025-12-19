import json
import hashlib
from dataclasses import asdict
import pandas as pd
import streamlit as st

from deviation_engine import DeviationConfig, build_deviation_report, validate_input_df
from abc_main import analyze_from_gl_file
from help_md import HELP_MD


# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="GL Deviation Watchlist",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.25rem; padding-bottom: 2.5rem; }
      .stMetric { background: rgba(255,255,255,0.03); padding: 0.8rem; border-radius: 14px; }
      .hint { color: rgba(255,255,255,0.72); font-size: 0.92rem; }
      .pill { display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px;
              background: rgba(255,255,255,0.06); margin-right: 0.35rem; }
      .warn { color: #f5c36a; }
      .ok { color: #7ee787; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Session state init
# -----------------------------
def init_state():
    ss = st.session_state

    ss.setdefault("cur_file_sig", None)
    ss.setdefault("prev_file_sig", None)

    ss.setdefault("analysis_df", None)
    ss.setdefault("analysis_ok", False)
    ss.setdefault("analysis_error", None)

    ss.setdefault("report_df", None)
    ss.setdefault("report_error", None)
    ss.setdefault("report_ready", False)

    ss.setdefault("cfg_sig_last_run", None)
    ss.setdefault("cfg_sig_current", None)

    ss.setdefault("results_stale", True)  # until first run


init_state()


# -----------------------------
# Helpers
# -----------------------------
def jsonable(x):
    if isinstance(x, tuple):
        return list(x)
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    return x


def sig_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sig_cfg(cfg: DeviationConfig) -> str:
    d = jsonable(asdict(cfg))
    s = json.dumps(d, sort_keys=True)
    return sig_bytes(s.encode("utf-8"))


def clear_results(reason: str | None = None):
    st.session_state["analysis_df"] = None
    st.session_state["analysis_ok"] = False
    st.session_state["analysis_error"] = reason

    st.session_state["report_df"] = None
    st.session_state["report_error"] = None
    st.session_state["report_ready"] = False

    st.session_state["cfg_sig_last_run"] = None
    st.session_state["results_stale"] = True


def tier_style(df: pd.DataFrame):
    def row_style(r):
        t = str(r.get("Tier", ""))
        if t == "Tier-1":
            return ["font-weight: 700;"] * len(r)
        if t == "Tier-3":
            return ["opacity: 0.85;"] * len(r)
        return [""] * len(r)
    return df.style.apply(row_style, axis=1)


# -----------------------------
# Sidebar config (NO auto compute)
# -----------------------------
def sidebar_config_ui() -> DeviationConfig:
    cfg = DeviationConfig()

    st.sidebar.header("Settings")
    st.sidebar.caption("Tune sensitivity. Blank/NaN cells never trigger by themselves.")

    with st.sidebar.expander("Checks to include", expanded=False):
        cfg.enabled_checks["distribution_change"] = st.checkbox("Distribution change", value=cfg.enabled_checks["distribution_change"], key="chk_distribution_change")
        cfg.enabled_checks["mean_shift"] = st.checkbox("Mean shift", value=cfg.enabled_checks["mean_shift"], key="chk_mean_shift")
        cfg.enabled_checks["effect_size"] = st.checkbox("Effect size", value=cfg.enabled_checks["effect_size"], key="chk_effect_size")
        cfg.enabled_checks["cv"] = st.checkbox("Volatility (CV)", value=cfg.enabled_checks["cv"], key="chk_cv")
        cfg.enabled_checks["mean_median_gap"] = st.checkbox("Mean–median gap", value=cfg.enabled_checks["mean_median_gap"], key="chk_mean_median_gap")
        cfg.enabled_checks["pearson_skew"] = st.checkbox("Pearson skew proxy", value=cfg.enabled_checks["pearson_skew"], key="chk_pearson_skew")
        cfg.enabled_checks["volatility_jump"] = st.checkbox("Volatility jump vs last year", value=cfg.enabled_checks["volatility_jump"], key="chk_vol_jump")
        cfg.enabled_checks["low_mean_high_variance"] = st.checkbox("Low mean + high variance", value=cfg.enabled_checks["low_mean_high_variance"], key="chk_low_mean_high_var")
        cfg.enabled_checks["new_activity"] = st.checkbox("New activity / restart", value=cfg.enabled_checks["new_activity"], key="chk_new_activity")
        cfg.enabled_checks["sign_reversal"] = st.checkbox("Sign reversal", value=cfg.enabled_checks["sign_reversal"], key="chk_sign_reversal")

    with st.sidebar.expander("Volatility + skew thresholds", expanded=True):
        st.write("<span class='hint'>Higher thresholds = fewer flags. Lower = more sensitive.</span>", unsafe_allow_html=True)
        cfg.thresholds.high_cv = st.slider("High CV threshold", 0.2, 3.0, float(cfg.thresholds.high_cv), 0.05, key="thr_high_cv")
        cfg.thresholds.moderate_cv = st.slider("Moderate CV threshold", 0.2, 2.0, float(cfg.thresholds.moderate_cv), 0.05, key="thr_mod_cv")
        cfg.thresholds.mean_median_gap_ratio = st.slider("Mean–median gap ratio", 0.05, 1.5, float(cfg.thresholds.mean_median_gap_ratio), 0.01, key="thr_mean_median_gap")
        cfg.thresholds.pearson_skew_abs = st.slider("Pearson skew (abs)", 0.2, 5.0, float(cfg.thresholds.pearson_skew_abs), 0.05, key="thr_pearson_skew")

    with st.sidebar.expander("Change thresholds", expanded=False):
        cfg.thresholds.rel_mean_shift = st.slider("Relative mean shift fallback", 0.1, 3.0, float(cfg.thresholds.rel_mean_shift), 0.05, key="thr_rel_mean_shift")
        cfg.thresholds.rel_std_jump = st.slider("Relative std jump", 0.1, 3.0, float(cfg.thresholds.rel_std_jump), 0.05, key="thr_rel_std_jump")
        cfg.thresholds.new_activity_factor = st.slider("New activity factor", 2.0, 50.0, float(cfg.thresholds.new_activity_factor), 1.0, key="thr_new_activity")
        cfg.thresholds.sign_reversal_min_mean_pct = st.slider("Sign reversal materiality (pct)", 0.0, 1.0, float(cfg.thresholds.sign_reversal_min_mean_pct), 0.01, key="thr_sign_rev_pct")

    with st.sidebar.expander("Effect size thresholds", expanded=False):
        cfg.thresholds.cohens_d_large = st.slider("Cohen's d (large)", 0.2, 2.5, float(cfg.thresholds.cohens_d_large), 0.05, key="thr_d_large")
        cfg.thresholds.cohens_d_medium = st.slider("Cohen's d (medium)", 0.1, 2.0, float(cfg.thresholds.cohens_d_medium), 0.05, key="thr_d_medium")

    with st.sidebar.expander("Tiering", expanded=False):
        cfg.tiers.tier1_min_score = st.slider("Tier-1 min score", 4, 40, int(cfg.tiers.tier1_min_score), 1, key="tier1_min")
        cfg.tiers.tier2_min_score = st.slider("Tier-2 min score", 2, 30, int(cfg.tiers.tier2_min_score), 1, key="tier2_min")
        cfg.tiers.tier3_min_score = st.slider("Tier-3 min score", 1, 20, int(cfg.tiers.tier3_min_score), 1, key="tier3_min")
        cfg.tiers.include_tier3 = st.checkbox("Include Tier-3", value=cfg.tiers.include_tier3, key="tier3_inc")
        cfg.tiers.max_tier1 = st.slider("Max Tier-1 rows", 1, 50, int(cfg.tiers.max_tier1), 1, key="tier1_cap")
        cfg.tiers.tier1_materiality_pct = st.slider("Tier-1 materiality gate (pct)", 0.0, 1.0, float(cfg.tiers.tier1_materiality_pct), 0.01, key="tier1_mat")
        cfg.tiers.tier1_override_score = st.slider("Tier-1 override score", 10, 80, int(cfg.tiers.tier1_override_score), 1, key="tier1_override")
        cfg.tiers.drop_pure_volatility_below_mean_pct = st.slider("Drop pure volatility below mean pct", 0.0, 1.0, float(cfg.tiers.drop_pure_volatility_below_mean_pct), 0.01, key="drop_vol_pct")

    return cfg


# -----------------------------R
# Main UI
# -----------------------------
st.title("GL Analysis")
st.caption("Upload current + previous GL files → generate deviation watchlist")

cfg = sidebar_config_ui()

# Detect config changes → mark results stale (but do NOT recompute)
cfg_sig = sig_cfg(cfg)
st.session_state["cfg_sig_current"] = cfg_sig
if st.session_state["cfg_sig_last_run"] and st.session_state["cfg_sig_last_run"] != cfg_sig:
    st.session_state["results_stale"] = True

tabs = st.tabs(["Upload", "Results", "Help", "Export config"])

# Help tab always available
with tabs[2]:
    st.subheader("Help")
    st.markdown(HELP_MD)

# Export config always available
with tabs[3]:
    st.subheader("Export config")
    cfg_dict = jsonable(asdict(cfg))
    cfg_json = json.dumps(cfg_dict, indent=2)
    st.code(cfg_json, language="json")
    st.download_button(
        "Download config JSON",
        data=cfg_json.encode("utf-8"),
        file_name="deviation_config.json",
        mime="application/json",
    )

# Upload tab
with tabs[0]:
    st.subheader("Upload GL files")

    up_current = st.file_uploader("Choose current year GL file", type=["csv", "xlsx"], key="uploader_cur")
    up_previous = st.file_uploader("Choose previous year GL file", type=["csv", "xlsx"], key="uploader_prev")

    cur_ready = up_current is not None
    prev_ready = up_previous is not None

    # If file(s) changed, clear results and mark stale
    if cur_ready:
        cur_sig = sig_bytes(up_current.getbuffer().tobytes())
        if st.session_state["cur_file_sig"] and st.session_state["cur_file_sig"] != cur_sig:
            clear_results("Current year file changed.")
        st.session_state["cur_file_sig"] = cur_sig

    if prev_ready:
        prev_sig = sig_bytes(up_previous.getbuffer().tobytes())
        if st.session_state["prev_file_sig"] and st.session_state["prev_file_sig"] != prev_sig:
            clear_results("Previous year file changed.")
        st.session_state["prev_file_sig"] = prev_sig

    if not (cur_ready and prev_ready):
        st.info("Upload both current and previous year files to run.")
    else:
        st.success("Files ready.")

    if st.session_state["analysis_error"]:
        st.error(st.session_state["analysis_error"])

    # One single RUN button for both steps
    run_disabled = not (cur_ready and prev_ready) or not st.session_state["results_stale"]

    st.write(
        f"<span class='pill'>Status</span>"
        f"<span class='hint'>{'Changes detected. Ready to run.' if st.session_state['results_stale'] else 'Up to date.'}</span>",
        unsafe_allow_html=True,
    )

    run_all = st.button(
        "Run Analysis",
        type="primary",
        disabled=run_disabled,
        help="Runs GL analysis and produces the deviation report using the current settings.",
    )

    if run_all:
        # Save to temp paths for your existing analyzer
        cur_path = f"/tmp/{up_current.name}"
        prev_path = f"/tmp/{up_previous.name}"

        with open(cur_path, "wb") as f:
            f.write(up_current.getbuffer())
        with open(prev_path, "wb") as f:
            f.write(up_previous.getbuffer())

        try:
            with st.spinner("Running GL analysis..."):
                try:
                    results_df = analyze_from_gl_file(cur_path, prev_path)
                except Exception as e:
                    raise RuntimeError(f"GL analysis failed: {e}")

            ok, issues = validate_input_df(results_df)
            if not ok:
                st.session_state["analysis_ok"] = False
                st.session_state["analysis_df"] = None
                st.session_state["analysis_error"] = "GL analysis output failed validation:\n" + "\n".join(issues)
                st.error("GL analysis failed validation.")
                st.stop()

            st.session_state["analysis_ok"] = True
            st.session_state["analysis_df"] = results_df
            st.session_state["analysis_error"] = None

            with st.spinner("Building deviation watchlist..."):
                out = build_deviation_report(results_df, cfg=cfg)

            st.session_state["report_df"] = out
            st.session_state["report_error"] = None
            st.session_state["report_ready"] = True

            st.session_state["cfg_sig_last_run"] = cfg_sig
            st.session_state["results_stale"] = False

            st.rerun()



        except Exception as e:
            st.session_state["report_df"] = None
            st.session_state["report_ready"] = False
            st.session_state["report_error"] = str(e)
            st.error("Run failed.")

    if not st.session_state["results_stale"]:
        st.success(f"Processed {len(st.session_state['analysis_df'])} accounts. Flagged {len(st.session_state['report_df'])} accounts.")


# Results tab
with tabs[1]:
    st.subheader("Deviation watchlist")

    if st.session_state.get("report_error"):
        st.error(st.session_state["report_error"])

    if not st.session_state.get("report_ready") or st.session_state.get("report_df") is None:
        st.info("Run analysis from the Upload tab to generate the watchlist.")
        st.stop()

    out = st.session_state["report_df"]

    if out.empty:
        st.warning("No accounts were flagged with the current settings. Try lowering Tier thresholds or High CV.")
        st.stop()

    # Filters
    c1, c2, c3 = st.columns([1.2, 1.2, 2.0])
    tier_pick = c1.multiselect("Tiers", ["Tier-1", "Tier-2", "Tier-3"], default=sorted(out["Tier"].unique().tolist()))
    top_n = c2.slider("Show top N", 10, min(500, len(out)), min(100, len(out)), 10)
    q = c3.text_input("Search account code / name", value="").strip().lower()

    view = out[out["Tier"].isin(tier_pick)].copy()
    if q:
        view = view[
            view["Account Code"].astype(str).str.lower().str.contains(q, na=False)
            | view["Account Name"].astype(str).str.lower().str.contains(q, na=False)
        ]
    view = view.head(top_n)

    # KPIs
    t1 = int((out["Tier"] == "Tier-1").sum())
    t2 = int((out["Tier"] == "Tier-2").sum())
    t3 = int((out["Tier"] == "Tier-3").sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Flagged accounts", f"{len(out):,}")
    m2.metric("Tier-1", f"{t1:,}")
    m3.metric("Tier-2", f"{t2:,}")
    m4.metric("Tier-3", f"{t3:,}")

    st.dataframe(tier_style(view), use_container_width=True, height=560)

    st.download_button(
        "Download full deviation report CSV",
        data=out.to_csv(index=False).encode("utf-8"),
        file_name="gl_deviation_report.csv",
        mime="text/csv",
    )
