
# GL Deviation Watchlist Guide

## Goal
Convert the monthly GL analysis results into a short, ranked list of account codes that deserve review, with:
- Key reasons the account is being flagged
- A plain-English accounting interpretation

## What the engine expects
Input is the **monthly analysis output CSV** with one row per account, including columns like:
- `Account Code`, `Account Name`
- `Credit_LY_Mean`, `Credit_CY_Mean`, `Credit_CY_Std`, `Credit_CY_Median`, …
- `*_TTest_Significant`, `*_MannWhitney_Significant`, `*_KS_Significant`, `*_ANOVA_Significant`
- `*_Effect_Size` and/or `*_Cohens_D`

This matches what your current analyzer exports.

## Output columns
- Tier (Tier-1 / Tier-2 / optional Tier-3)
- Account Code
- Account Name
- Key Metrics Triggered (top reasons, kept readable)
- Accounting Interpretation
- Score (internal ranking)
- Dominant Metric (which metric drove the score most)

## Why blank cells won’t cause false flags
The engine treats empty cells as “no evidence”.
A trigger only fires if the required inputs exist and pass thresholds.
So missing test results or missing effect size does **not** create flags by accident.

## How tiers are decided (human logic, not math-only)
Tier-1 is reserved for accounts that are either:
- material (relative to your dataset) **and** show strong change signals, or
- show extremely strong evidence even if smaller (override by score)

Tier-2 is a meaningful “review queue”.

Tier-3 is optional and off by default.

## Running it
```python
import pandas as pd
from deviation_engine import build_deviation_report, DeviationConfig

df = pd.read_csv("gl_analysis_results_monthly.csv")
report = build_deviation_report(df)     # uses default config
report.to_csv("gl_deviation_report.csv", index=False)
print(report.head(20))
```

## Tuning the output size (the practical knobs)
Open `DeviationConfig()` and edit:

### 1) Tier cutoffs
- `cfg.tiers.tier1_min_score`
- `cfg.tiers.tier2_min_score`

Higher = fewer flags.

### 2) Cap Tier-1 to keep it reviewable
- `cfg.tiers.max_tier1 = 10`

### 3) Reduce noise from small accounts
- `cfg.tiers.drop_pure_volatility_below_mean_pct`

### 4) Tighten or loosen detection thresholds
- `cfg.thresholds.high_cv`
- `cfg.thresholds.mean_median_gap_ratio`
- `cfg.thresholds.rel_mean_shift`

### 5) Metric profiles (recommended)
Running_Balance tends to dominate. Its profile gates it harder:
- `cfg.profiles["Running_Balance"].min_mean_pct_for_effect`
- `cfg.profiles["Running_Balance"].effect_weight_mult`

## Customising interpretation wording
Edit the language map:
- `cfg.language.bucket_finish`

Or change the bucket rules in `bucketize()`.

## Adding/removing checks
Toggle checks in:
- `cfg.enabled_checks`

Examples:
- disable mean–median skew proxy:
  `cfg.enabled_checks["mean_median_gap"] = False`
- disable low-mean high-variance:
  `cfg.enabled_checks["low_mean_high_variance"] = False`

## Extending with new metrics
If your analyzer later exports more metric prefixes (e.g. `Quantity_CY_Mean`),
the engine will automatically pick them up as long as `*_CY_Mean` exists.


## Why the current thresholds and configs look the way they do

### The real problem being solved
Monthly GLs are noisy. A simple “CV is high” rule flags half the chart of accounts, especially for small accounts. The config is trying to keep the watchlist small by rewarding only changes that are both meaningful and explainable.

### What counts as “real deviation”
The model gives most weight to evidence that the account’s behaviour *changed*, not just that it’s messy:
- **Distribution Change** and **Mean Shift** are treated as the strongest signals, so they carry the biggest weights.
- **Effect Size** matters only when it supports an actual change signal (tests or big relative move), so “large” labels alone don’t dominate the ranking.

### Why materiality is percentile-based (not absolute ₹ thresholds)
Different clients have different scales. Using **percentile gates** (abs(CY mean) relative to the dataset) avoids hardcoding “₹X is material” and prevents tiny accounts from becoming Tier-1 just because they have wild percentage swings.

### Why Running_Balance is gated harder
Running Balance naturally produces “large” effect sizes and volatility even when nothing is wrong (repayment schedules, financing, clearing movements). The profile forces higher materiality requirements and slightly down-weights effect/CV so it doesn’t hijack the report.

### Why CV and mean–median gap have stricter gates
High CV and skew are common in low-activity accounts (one invoice in a month looks like an “anomaly”). That’s why:
- CV/Skew triggers require the account to be material enough (by percentile) before they score.
- Pure volatility signals are dropped unless the account is very material, otherwise the list becomes a “small account noise report”.

### Why Tier-1 is hard to get
Tier-1 is intended for “review now” items, so it requires:
- a high total score, and
- either strong materiality or an extremely high override score.
This prevents Tier-1 being filled with small, technical outliers.

### How missing/empty values are handled
Empty cells are treated as **no evidence**, not evidence of deviation:
- Any rule that needs a value checks for NaN and simply doesn’t trigger if data is missing.
- This avoids false positives caused by blanks, but it can reduce sensitivity if many key test outputs are absent.

### What to adjust depending on the goal
- If the goal is “audit risk shortlist”: keep the current strict materiality gates and high Tier-1 thresholds.
- If the goal is “expense hygiene watchlist”: relax Debit CV/Skew gates and allow Tier-2 for volatility-driven signals, accepting a longer list.
