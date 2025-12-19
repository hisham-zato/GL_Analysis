
HELP_MD = """
## What this app does

Create GL analysis CSV and ranked watchlist of account codes that look unusual versus last year.
Each flagged account shows the signals that triggered and a short accounting interpretation to guide review.

## How the flagging works (high level)

1) For each account, the engine evaluates multiple “signals” (tests + behaviour metrics) across each metric stream (Credit, Debit, Running Balance, GST if present).
2) Each triggered signal adds points to a score (weighted). Multiple metric streams triggering adds a small bonus.
3) Accounts are put into Tier-1 / Tier-2 / (optional Tier-3) based on score and a materiality gate.
4) Pure volatility-only flags are dropped unless the account is materially large (to reduce noise).
5) Empty cells never trigger anything by themselves. Missing values are treated as “no evidence”.

## Signals (what you might see in the report)

**Distribution Change**
- Posting pattern changed versus last year (based on non-parametric / distribution tests like KS or Mann-Whitney when present).
- Useful for catching changes in transaction “shape” even if the mean didn't move much.

**Mean Shift**
- The average level moved versus last year (based on t-test / ANOVA when present, or fallback to a large relative change).

**Large / Medium Effect Size**
- The change is practically meaningful (Cohen's d or Effect_Size label), not just statistically significant.

**High CV / Moderate CV**
- CV is volatility relative to the mean (Std / Mean).
- High CV = lumpy, irregular postings. Moderate CV = noticeable but less extreme.

**Mean-Median Gap**
- Mean is far from median, suggesting outliers or one-offs dominate the behaviour.

**Pearson Skew (proxy)**
- Extra outlier proxy based on 3*(Mean-Median)/Std. Lower weight, meant as a supporting signal.

**Volatility Jump**
- The standard deviation increased materially versus last year (CY vs LY).

**Low Mean with High Variance**
- Small average value but big spread. Common in batching, sporadic journals, or timing corrections.

**New Activity / Re-start**
- Little or no activity last year, but meaningful activity this year.

**Sign Reversal**
- Direction flipped (e.g., positive to negative). Often points to reclass/contra entries or posting sign changes.

## Controls (what each setting means)

### Checks to include
Turn signals on/off. This changes both score and which accounts appear.
Example: turning off CV will remove volatility-only reasons from scoring.

### Volatility + skew thresholds

**High CV threshold**
- Minimum CV required to label “High CV”.
- Higher = fewer volatility flags. Lower = more sensitivity.

**Moderate CV threshold**
- Minimum CV required to label “Moderate CV”.
- Should generally be lower than High CV.

**Mean-median gap ratio**
- Minimum |Mean - Median| / |Mean| required to flag skew.
- Higher = fewer skew flags. Lower = more skew sensitivity.

**Pearson skew (abs)**
- Minimum absolute Pearson skew proxy required to flag.
- Keep this relatively high unless wanting extra outlier sensitivity.

### Change thresholds

**Relative mean shift fallback**
- Used when significance flags are missing/blank.
- If |Mean_Diff| / |LY_Mean| exceeds this (and the account is material), “Mean Shift” can still trigger.

**Relative std jump**
- Flags “Volatility Jump” when |Std_Diff| / |LY_Std| exceeds this.

**New activity factor**
- Controls how aggressively “New Activity / Re-start” triggers when LY mean is near zero.

**Sign reversal materiality (pct)**
- A percentile-based gate: sign reversal is only flagged if the account is materially large enough.
- Higher = fewer sign-reversal flags on small accounts.

### Effect size thresholds

**Cohen's d (large / medium)**
- Interprets effect size numerically when Effect_Size labels are missing.
- Larger thresholds = stricter effect-size triggering.

### Tiering

**Tier-1 min score / Tier-2 min score / Tier-3 min score**
- Minimum score to qualify for each tier.
- Higher = shorter list, but more selective.

**Include Tier-3**
- Shows lower-confidence items (useful for tuning).

**Max Tier-1 rows**
- Caps Tier-1 length; overflow is demoted to Tier-2.

**Tier-1 materiality gate (pct)**
- Tier-1 usually expects the account to be materially large (based on CY mean percentile),
  unless the score is extremely high.
- Higher = Tier-1 becomes “big-ticket only”.

**Tier-1 override score**
- If score exceeds this, Tier-1 can be assigned even if the materiality gate isn't met.

**Drop pure volatility below mean pct**
- If an account only has volatility-type signals (CV/skew/vol-jump), it will be dropped
  unless its materiality percentile exceeds this threshold.
- Raising this reduces noisy volatility-only flags.

## Reading the report

Each flagged account includes a compact evidence strip so the reason is visible without adding many columns.
It is grouped by metric stream (for example: Debit, Credit, Running_Balance, GST). Example:

Debit: LYμ:301.28 CYμ:773.04 (+157%); CYσ:615.98 CV:0.80; μ~med:0.33; skew:1.23; d:1.02; sig[T,A,MW]; tag[Distribution Change,Mean Shift,Large Effect Size]

### Symbols and fields (plain meaning)

**Debit / Credit / Running_Balance / GST**
- The metric stream being analysed for the account. Many accounts trigger on more than one stream.

**LYμ**
- Last Year mean (average). “μ” means mean/average.

**CYμ**
- Current Year mean (average).

**(+157%)**
- Approximate relative change from LY mean to CY mean.
- Positive = increase, negative = decrease.

**CYσ**
- Current Year standard deviation (spread/variability). “σ” means standard deviation.

**CV**
- Coefficient of Variation = CYσ / |CYμ|.
- Higher CV usually means lumpy/batched posting behaviour (irregular months).

**μ~med**
- Mean-median gap ratio (a skew/outlier proxy).
- Higher value suggests a few large journals or one-offs are pulling the mean away from the “typical” month.

**skew**
- Pearson skew proxy (another outlier proxy). Higher absolute values suggest more asymmetry/outliers.

**d**
- Cohen's d (effect size). Bigger means the change is practically meaningful, not just small noise.

**sig[...]**
- Which statistical tests were significant (when available):
  - T = t-test (mean difference)
  - A = ANOVA (mean difference across groups)
  - MW = Mann-Whitney (distribution shift)
  - KS = Kolmogorov-Smirnov (distribution shift)
- If sig[] is missing, it usually means the test fields were blank/unavailable or not significant.

**tag[...]**
- The main signals that contributed to the score for that metric stream.


### Quick reading tip

When scanning Metric Values:
- Start with **CYμ vs LYμ** (is it actually big and changed?)
- Then check **d** and **sig[...]** (is the change strong evidence?)
- Then check **CV / μ~med / skew** (is it lumpy or driven by outliers?)


## Quick tuning moves

If too many accounts are flagged:
- Increase Tier-2 min score
- Increase High CV threshold
- Increase Drop pure volatility below mean pct
- Increase Tier-1 materiality gate

If too few accounts are flagged:
- Decrease Tier-2 min score
- Decrease High CV threshold
- Enable Tier-3 temporarily to see “near misses”

## Recommended tuning process
To get a clean, useful shortlist:
1) Run with default settings and check if the flags look too noisy or too quiet.
2) Adjust thresholds until the watchlist matches real review intuition.
3) Once the thresholds look right, export the config JSON and share it.


""".strip()
