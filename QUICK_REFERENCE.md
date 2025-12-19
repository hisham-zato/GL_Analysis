# Quick Reference Guide

## 🚀 Getting Started in 30 Seconds

### Option 1: Run Directly
```bash
python main.py
```
*Assumes JSON files are named `gl_current_year_data.json` and `gl_last_year_data.json`*

### Option 2: From Your Python Code
```python
from main import analyze_from_json_objects

# Your JSON objects
current_year_data = {...}
previous_year_data = {...}

# Run and get CSV
analyze_from_json_objects(current_year_data, previous_year_data)
```

---

## 📊 What You Get

**Input**: JSON with account codes and transactions

**Output**: CSV file with one row per account code

**Metrics per Account**: 130+ including:
- Descriptive stats (mean, median, std, min, max)
- Statistical tests (T-test, Mann-Whitney, ANOVA, K-S)
- Effect sizes (Cohen's d)
- Correlations

---

## 📋 JSON Format Required

```json
{
    "ACCOUNT_CODE": {
        "account_code": "ACCOUNT_CODE",
        "account_name": "Account Name",
        "transactions": [
            {
                "Date": "2024-01-15",
                "Debit": 0.0,
                "Credit": 1000.0,
                "Running Balance": -1000.0,
                "GST": -150.0
            }
        ]
    }
}
```

---

## 🎯 Key Output Columns

| Column Pattern | Meaning |
|----------------|---------|
| `Credit_LY_Mean` | Last year average credit |
| `Credit_CY_Mean` | Current year average credit |
| `Credit_Mean_Diff` | Change in average |
| `Credit_TTest_Significant` | Is change significant? (True/False) |
| `Credit_Cohens_D` | Effect size magnitude |
| `Credit_Effect_Size` | Practical significance (small/medium/large) |

*Same pattern for: Debit, Running Balance, GST*

---

## 🔧 Quick Configurations

### Change Analysis Period
```python
# In main.py
results = analyzer.run_analysis_for_all_accounts(period='quarterly')
# Options: 'weekly', 'bi-weekly', 'monthly', 'quarterly'
```

### Analyze Different Metrics
```python
# In config.py
COLUMNS_OF_INTEREST = [
    'Debit',
    'Credit',
    'Your_Custom_Column'
]
```

---

## 📈 Reading Results

### Focus on These Columns:
1. **Account Code** - Which account
2. **{Metric}_Mean_Diff** - How much changed
3. **{Metric}_TTest_Significant** - Is it real? (True = Yes)
4. **{Metric}_Effect_Size** - How important? (large > medium > small)

### Quick Filtering in Excel/Python:
```python
import pandas as pd
df = pd.read_csv('gl_analysis_results_monthly.csv')

# Show only significant credit changes
df[df['Credit_TTest_Significant'] == True]

# Show only large effects
df[df['Credit_Effect_Size'] == 'large']
```

---

## ⚡ Common Tasks

### 1. Generate Multiple Period Reports
```python
for period in ['weekly', 'monthly', 'quarterly']:
    results = analyzer.run_analysis_for_all_accounts(period=period)
    results.to_csv(f'analysis_{period}.csv', index=False)
```

### 2. Find Top Changes
```python
df = pd.read_csv('gl_analysis_results_monthly.csv')

# Top 10 credit increases
df.nlargest(10, 'Credit_Mean_Diff')[['Account Code', 'Account Name', 'Credit_Mean_Diff']]

# Top 10 credit decreases
df.nsmallest(10, 'Credit_Mean_Diff')[['Account Code', 'Account Name', 'Credit_Mean_Diff']]
```

### 3. Export Specific Accounts
```python
df = pd.read_csv('gl_analysis_results_monthly.csv')

# Get specific account codes
accounts_of_interest = ['180/001', '180/002', '220']
filtered = df[df['Account Code'].isin(accounts_of_interest)]
filtered.to_csv('selected_accounts.csv', index=False)
```

---

## 🎨 Interpretation Guide

### Statistical Significance
- ✅ **True**: Change is real (not random) with 95% confidence
- ❌ **False**: Change might be random variation

### Effect Size
- 🔴 **large**: Major practical difference (|Cohen's d| ≥ 0.8)
- 🟡 **medium**: Moderate difference (0.2 ≤ |d| < 0.8)
- 🟢 **small**: Minor difference (|d| < 0.2)

### Correlation Strength
- **strong**: |r| > 0.5
- **moderate**: 0.3 < |r| ≤ 0.5
- **weak**: 0.1 < |r| ≤ 0.3

---

## 💡 Pro Tips

1. **Monthly is usually best** - Good balance of data points
2. **Look at effect size first** - Statistical significance ≠ practical importance
3. **Compare multiple periods** - Spot trends vs one-time changes
4. **Focus on your KPIs** - Don't analyze every column, pick what matters
5. **Keep the CSV** - Easy to re-filter and analyze later

---

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "Insufficient data" message | Normal - account needs more transactions for stats |
| Missing columns in output | Check account has data in both years |
| Empty CSV | Verify JSON structure matches format |
| Takes too long | Normal for 100+ accounts (~1-2 min) |

---

## 📦 File Outputs

| File | Content |
|------|---------|
| `gl_analysis_results_monthly.csv` | Main output - all account codes |
| Account rows | 69 (example - varies by data) |
| Metric columns | 134 (example - varies by config) |

---

## 🔄 Typical Workflow

```
1. Prepare JSON files/objects
   ↓
2. Run: python main.py
   ↓
3. Open: gl_analysis_results_monthly.csv
   ↓
4. Filter: significant changes only
   ↓
5. Review: top increases/decreases
   ↓
6. Deep dive: specific accounts of interest
```

---

## 🎓 Example Analysis Session

```python
import pandas as pd

# Load results
df = pd.read_csv('gl_analysis_results_monthly.csv')

# 1. Overview
print(f"Analyzed {len(df)} account codes")

# 2. Find significant changes
sig_credit = df[df['Credit_TTest_Significant'] == True]
print(f"{len(sig_credit)} accounts with significant credit changes")

# 3. Top movers
print("\nTop 5 Credit Increases:")
print(df.nlargest(5, 'Credit_Mean_Diff')[
    ['Account Code', 'Account Name', 'Credit_Mean_Diff']
])

# 4. Large effects
large_fx = df[df['Credit_Effect_Size'] == 'large']
print(f"\n{len(large_fx)} accounts with large effect sizes")

# 5. Export for review
sig_credit.to_csv('review_these_accounts.csv', index=False)
```

---

## 📞 Need Help?

1. Check JSON format matches specification
2. Review console output for error messages
3. Verify dates are valid
4. Ensure required columns exist in transactions

---

**Remember**: This tool processes EVERY account code independently. You get detailed, account-specific insights for your entire GL!
