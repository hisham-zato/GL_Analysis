# CSV Output Column Reference Guide

## Complete Column List and Descriptions

The output CSV contains 130+ columns. This guide explains each column type.

---

## Core Identification Columns (2 columns)

| Column | Description | Example |
|--------|-------------|---------|
| `Account Code` | Unique account identifier | "180/001" |
| `Account Name` | Account description | "Sales - Labour" |

---

## For Each Metric: 32 Columns

The following columns exist for each metric (Credit, Debit, Running Balance, GST).
Pattern: `{METRIC}_{STAT}`

### 1. Previous Year (LY) Descriptive Statistics (5 columns)

| Column | Description | Interpretation |
|--------|-------------|----------------|
| `{Metric}_LY_Mean` | Average value last year | Central tendency LY |
| `{Metric}_LY_Std` | Standard deviation LY | Variability LY |
| `{Metric}_LY_Min` | Minimum value LY | Lowest point LY |
| `{Metric}_LY_Max` | Maximum value LY | Highest point LY |
| `{Metric}_LY_Median` | Median value LY | Middle value LY |

### 2. Current Year (CY) Descriptive Statistics (5 columns)

| Column | Description | Interpretation |
|--------|-------------|----------------|
| `{Metric}_CY_Mean` | Average value current year | Central tendency CY |
| `{Metric}_CY_Std` | Standard deviation CY | Variability CY |
| `{Metric}_CY_Min` | Minimum value CY | Lowest point CY |
| `{Metric}_CY_Max` | Maximum value CY | Highest point CY |
| `{Metric}_CY_Median` | Median value CY | Middle value CY |

### 3. Year-over-Year Differences (5 columns)

| Column | Description | Formula |
|--------|-------------|---------|
| `{Metric}_Mean_Diff` | Change in average | CY_Mean - LY_Mean |
| `{Metric}_Std_Diff` | Change in variability | CY_Std - LY_Std |
| `{Metric}_Min_Diff` | Change in minimum | CY_Min - LY_Min |
| `{Metric}_Max_Diff` | Change in maximum | CY_Max - LY_Max |
| `{Metric}_Median_Diff` | Change in median | CY_Median - LY_Median |

### 4. T-Test Results (3 columns)

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_TTest_Statistic` | T-statistic value | Float |
| `{Metric}_TTest_PValue` | Probability value | 0.0 to 1.0 |
| `{Metric}_TTest_Significant` | Is significant? | True/False |

**Interpretation**:
- P-Value < 0.05 → Significant = True → Means are different
- P-Value ≥ 0.05 → Significant = False → No evidence of difference

### 5. Mann-Whitney U Test Results (3 columns)

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_MannWhitney_Statistic` | U-statistic value | Float |
| `{Metric}_MannWhitney_PValue` | Probability value | 0.0 to 1.0 |
| `{Metric}_MannWhitney_Significant` | Is significant? | True/False |

**Interpretation**:
- Non-parametric alternative to t-test
- Tests if distributions differ
- More robust to outliers

### 6. ANOVA F-Test Results (3 columns)

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_ANOVA_FStatistic` | F-statistic value | Float |
| `{Metric}_ANOVA_PValue` | Probability value | 0.0 to 1.0 |
| `{Metric}_ANOVA_Significant` | Is significant? | True/False |

**Interpretation**:
- Tests variance between groups
- Significant = Different group means

### 7. Kolmogorov-Smirnov Test Results (3 columns)

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_KS_Statistic` | KS-statistic value | 0.0 to 1.0 |
| `{Metric}_KS_PValue` | Probability value | 0.0 to 1.0 |
| `{Metric}_KS_Significant` | Is significant? | True/False |

**Interpretation**:
- Tests if distributions are the same
- Significant = Distributions differ

### 8. Effect Size Analysis (2 columns)

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_Cohens_D` | Standardized difference | Float (typically -3 to +3) |
| `{Metric}_Effect_Size` | Magnitude category | "small", "medium", "large", "none" |

**Cohen's D Interpretation**:
- |d| < 0.2: small effect (minor difference)
- 0.2 ≤ |d| < 0.8: medium effect (moderate difference)
- |d| ≥ 0.8: large effect (substantial difference)
- Sign indicates direction: + means increase, - means decrease

### 9. Correlation Analysis (4 columns)

*Note: Only present when both years have equal periods*

| Column | Description | Values |
|--------|-------------|--------|
| `{Metric}_Correlation` | Pearson r coefficient | -1.0 to +1.0 |
| `{Metric}_Correlation_PValue` | Probability value | 0.0 to 1.0 |
| `{Metric}_Correlation_Significant` | Is significant? | True/False |
| `{Metric}_Correlation_Strength` | Relationship strength | "weak", "moderate", "strong", "none" |

**Correlation Interpretation**:
- +1.0: Perfect positive relationship
- 0.0: No relationship
- -1.0: Perfect negative relationship

**Strength Thresholds**:
- 0.1 < |r| < 0.3: weak
- 0.3 ≤ |r| < 0.5: moderate
- |r| ≥ 0.5: strong

---

## Column Count by Metric

For a standard configuration with 4 metrics (Credit, Debit, Running Balance, GST):

| Category | Columns per Metric | Total Columns |
|----------|-------------------|---------------|
| Identification | - | 2 |
| LY Descriptive | 5 | 20 |
| CY Descriptive | 5 | 20 |
| Differences | 5 | 20 |
| T-Test | 3 | 12 |
| Mann-Whitney | 3 | 12 |
| ANOVA | 3 | 12 |
| K-S Test | 3 | 12 |
| Effect Size | 2 | 8 |
| Correlation* | 4 | 16 |
| **TOTAL** | **33** | **134** |

*Correlation columns may be empty for some accounts if period counts don't match

---

## Example Column Names

### For Credit Metric:
```
Credit_LY_Mean
Credit_LY_Std
Credit_LY_Min
Credit_LY_Max
Credit_LY_Median
Credit_CY_Mean
Credit_CY_Std
Credit_CY_Min
Credit_CY_Max
Credit_CY_Median
Credit_Mean_Diff
Credit_Std_Diff
Credit_Min_Diff
Credit_Max_Diff
Credit_Median_Diff
Credit_TTest_Statistic
Credit_TTest_PValue
Credit_TTest_Significant
Credit_MannWhitney_Statistic
Credit_MannWhitney_PValue
Credit_MannWhitney_Significant
Credit_ANOVA_FStatistic
Credit_ANOVA_PValue
Credit_ANOVA_Significant
Credit_KS_Statistic
Credit_KS_PValue
Credit_KS_Significant
Credit_Cohens_D
Credit_Effect_Size
Credit_Correlation
Credit_Correlation_PValue
Credit_Correlation_Significant
Credit_Correlation_Strength
```

---

## Usage Examples

### Find Significant Changes
```python
import pandas as pd
df = pd.read_csv('gl_analysis_results_monthly.csv')

# Accounts with significant credit changes
sig_accounts = df[df['Credit_TTest_Significant'] == True]

# Show account code, name, and change
print(sig_accounts[['Account Code', 'Account Name', 'Credit_Mean_Diff']])
```

### Filter by Effect Size
```python
# Large credit effects only
large_effects = df[df['Credit_Effect_Size'] == 'large']

# Medium or large effects
medium_large = df[df['Credit_Effect_Size'].isin(['medium', 'large'])]
```

### Sort by Magnitude of Change
```python
# Top 10 increases
top_increases = df.nlargest(10, 'Credit_Mean_Diff')

# Top 10 decreases
top_decreases = df.nsmallest(10, 'Credit_Mean_Diff')
```

### Multi-Metric Analysis
```python
# Accounts with significant changes in ANY metric
significant_any = df[
    (df['Credit_TTest_Significant'] == True) |
    (df['Debit_TTest_Significant'] == True) |
    (df['Running_Balance_TTest_Significant'] == True) |
    (df['GST_TTest_Significant'] == True)
]

# Accounts with large effects in ANY metric
large_any = df[
    (df['Credit_Effect_Size'] == 'large') |
    (df['Debit_Effect_Size'] == 'large') |
    (df['Running_Balance_Effect_Size'] == 'large') |
    (df['GST_Effect_Size'] == 'large')
]
```

---

## Column Selection for Reports

### Executive Summary Columns
```python
summary_cols = [
    'Account Code',
    'Account Name',
    'Credit_Mean_Diff',
    'Credit_TTest_Significant',
    'Credit_Effect_Size'
]
df[summary_cols]
```

### Detailed Analysis Columns
```python
detailed_cols = [
    'Account Code',
    'Account Name',
    'Credit_LY_Mean',
    'Credit_CY_Mean',
    'Credit_Mean_Diff',
    'Credit_TTest_PValue',
    'Credit_MannWhitney_PValue',
    'Credit_Cohens_D',
    'Credit_Effect_Size'
]
df[detailed_cols]
```

### Year-over-Year Comparison
```python
yoy_cols = [
    'Account Code',
    'Account Name',
    'Credit_LY_Mean',
    'Credit_CY_Mean',
    'Debit_LY_Mean',
    'Debit_CY_Mean',
    'GST_LY_Mean',
    'GST_CY_Mean'
]
df[yoy_cols]
```

---

## Null/Empty Values

**When columns might be empty**:
- Correlation columns: When period counts don't match between years
- All metrics: When account has insufficient data (<2 unique values per period)

**Handling in Python**:
```python
# Check for missing values
df['Credit_Correlation'].isna().sum()

# Fill missing with default
df['Credit_Correlation'].fillna(0)

# Drop rows with missing key metrics
df.dropna(subset=['Credit_TTest_Significant'])
```

---

## Quick Reference Table

| What You Want | Column to Check |
|---------------|-----------------|
| How much changed? | `{Metric}_Mean_Diff` |
| Is it significant? | `{Metric}_TTest_Significant` |
| How important? | `{Metric}_Effect_Size` |
| Direction of change? | Sign of `{Metric}_Mean_Diff` |
| Variability changed? | `{Metric}_Std_Diff` |
| Last year average? | `{Metric}_LY_Mean` |
| This year average? | `{Metric}_CY_Mean` |
| Years correlated? | `{Metric}_Correlation` |

---

## Tips for Excel Users

1. **Freeze first 2 columns**: Account Code and Name
2. **Filter by Significant = TRUE**: Find real changes
3. **Conditional formatting**: Highlight large effect sizes
4. **Sort by Mean_Diff**: See biggest changes first
5. **Pivot tables**: Summarize by effect size categories

---

**Remember**: Each account code gets its own row with all 134 metrics. Perfect for filtering, sorting, and targeted analysis!
