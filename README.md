# GL Statistical Analysis Tool - JSON Version

A powerful tool for analyzing General Ledger (GL) data account-code-wise from JSON input. Processes each account code separately and generates comprehensive statistical analysis in CSV format.

## Overview

This tool:
- ✅ Accepts JSON objects (not CSV files)
- ✅ Processes each account code independently
- ✅ Performs comprehensive statistical analysis
- ✅ Outputs results in a single CSV file with account codes in rows
- ✅ Includes 130+ metrics per account code

## Quick Start

### Method 1: Using JSON Files

```python
from data_loader import DataLoader
from analyzer import GLAnalyzer
import config

# Load JSON files
current_year_json = DataLoader.load_json_from_file('gl_current_year_data.json')
previous_year_json = DataLoader.load_json_from_file('gl_last_year_data.json')

# Process and analyze
loader = DataLoader(current_year_json, previous_year_json)
account_data = loader.load_from_json()

analyzer = GLAnalyzer(account_data)
results_df = analyzer.run_analysis_for_all_accounts(period='monthly')

# Save results
results_df.to_csv('gl_analysis_results_monthly.csv', index=False)
```

Or simply run:
```bash
python main.py
```

### Method 2: Using JSON Objects in Memory

```python
from main import analyze_from_json_objects

# Assuming you already have JSON objects loaded
current_year_data = {...}  # Your JSON object
previous_year_data = {...}  # Your JSON object

# Run analysis
output_file = analyze_from_json_objects(
    current_year_data,
    previous_year_data,
    period='monthly',
    output_filename='results.csv'
)
```

## JSON Input Format

Your JSON must follow this structure:

```json
{
    "account_code_1": {
        "account_code": "account_code_1",
        "account_name": "Account Name Here",
        "transactions": [
            {
                "Date": "2024-01-15",
                "Account Code": "account_code_1",
                "Debit": 0.0,
                "Credit": 1000.0,
                "Running Balance": -1000.0,
                "GST": -150.0,
                "GST Rate": 15.0,
                "GST Rate Name": "15% GST on Income"
            },
            ...
        ]
    },
    "account_code_2": {
        ...
    }
}
```

### Required Fields in Transactions:
- `Date` - Transaction date
- `Debit` - Debit amount
- `Credit` - Credit amount
- `Running Balance` - Running balance
- `GST` - GST amount

## Output Format

The tool generates a CSV file with:
- **Rows**: One row per account code
- **Columns**: 130+ metrics including:

### Column Categories:

1. **Account Information**
   - Account Code
   - Account Name

2. **Previous Year (LY) Descriptive Statistics** (per metric)
   - Mean, Std, Min, Max, Median

3. **Current Year (CY) Descriptive Statistics** (per metric)
   - Mean, Std, Min, Max, Median

4. **Differences** (per metric)
   - Mean_Diff, Std_Diff, Min_Diff, Max_Diff, Median_Diff

5. **Statistical Tests** (per metric)
   - T-Test: Statistic, P-Value, Significant (True/False)
   - Mann-Whitney U: Statistic, P-Value, Significant
   - ANOVA: F-Statistic, P-Value, Significant
   - Kolmogorov-Smirnov: Statistic, P-Value, Significant

6. **Effect Size Analysis** (per metric)
   - Cohen's D
   - Effect Size Category (small/medium/large)

7. **Correlation Analysis** (per metric, when applicable)
   - Correlation Coefficient
   - P-Value
   - Significant (True/False)
   - Strength (weak/moderate/strong)

### Metrics Analyzed:
By default, the tool analyzes these columns from your transactions:
- Credit
- Debit  
- Running Balance
- GST

Each metric gets ~30 columns in the output, totaling 130+ columns.

## Configuration

Edit `config.py` to customize:

```python
# Columns to analyze from transactions
COLUMNS_OF_INTEREST = [
    'Debit',
    'Credit',
    'Running Balance',
    'GST'
]

# Default analysis period
DEFAULT_PERIOD = 'monthly'  # Options: 'weekly', 'bi-weekly', 'monthly', 'quarterly'

# Statistical significance threshold
SIGNIFICANCE_LEVEL = 0.05
```

## Analysis Periods

Choose how to aggregate data:

- **weekly**: Week-by-week comparison
- **bi-weekly**: Every two weeks
- **monthly**: Month-by-month (default, recommended)
- **quarterly**: Quarter-by-quarter

Change in main.py:
```python
results_df = analyzer.run_analysis_for_all_accounts(period='quarterly')
```

## Understanding the Output

### Example Row (simplified):

| Account Code | Account Name | Credit_LY_Mean | Credit_CY_Mean | Credit_Mean_Diff | Credit_TTest_Significant |
|--------------|--------------|----------------|----------------|------------------|-------------------------|
| 180/001 | Sales - Labour | 39477.31 | 41409.17 | 1931.86 | False |

This shows:
- Account 180/001 (Sales - Labour)
- Average monthly credit last year: $39,477.31
- Average monthly credit current year: $41,409.17  
- Increase of $1,931.86
- Change is not statistically significant

### Key Metrics to Focus On:

1. **Mean_Diff**: Shows absolute change
2. **TTest_Significant**: True = statistically significant change
3. **Cohens_D**: Effect size magnitude
4. **Effect_Size**: Practical significance (small/medium/large)

### Interpreting Statistical Significance:

- **Significant = True**: High confidence the change is real (p < 0.05)
- **Significant = False**: Change could be due to random variation

### Effect Size Categories:

- **small**: Minor practical difference (|Cohen's d| < 0.2)
- **medium**: Moderate practical difference (0.2 ≤ |d| < 0.8)
- **large**: Substantial practical difference (|d| ≥ 0.8)

## Project Structure

```
.
├── main.py                        # Main entry point
├── config.py                      # Configuration settings
├── data_loader.py                 # JSON data loading and processing
├── analyzer.py                    # Account-wise analysis orchestration
├── statisticsal_inferences.py     # Statistical analysis engine
├── output_formatter.py            # Console output formatting (optional)
├── computation_methods.py         # Additional computation methods (optional)
├── gl_current_year_data.json     # Your current year data
├── gl_last_year_data.json        # Your previous year data
└── gl_analysis_results_monthly.csv  # Output file
```

## Workflow

```
JSON Files
    ↓
Data Loader (converts to account-structured data)
    ↓
Analyzer (processes each account code)
    ↓
Statistical Inferences (runs tests per account)
    ↓
CSV Output (one row per account code)
```

## Example Usage in Your Code

```python
import json
from main import analyze_from_json_objects

# Option 1: Load from files
with open('current_year.json', 'r') as f:
    current_year = json.load(f)
with open('previous_year.json', 'r') as f:
    previous_year = json.load(f)

# Option 2: Use objects you already have
# current_year = your_json_object
# previous_year = your_json_object

# Run analysis
output_file = analyze_from_json_objects(
    current_year,
    previous_year,
    period='monthly',
    output_filename='my_results.csv'
)

print(f"Results saved to: {output_file}")
```

## Advanced Features

### Multiple Analysis Periods

Generate reports for different time aggregations:

```python
for period in ['weekly', 'monthly', 'quarterly']:
    results = analyzer.run_analysis_for_all_accounts(period=period)
    results.to_csv(f'analysis_{period}.csv', index=False)
```

### Filter Significant Changes Only

```python
import pandas as pd

# Load results
df = pd.read_csv('gl_analysis_results_monthly.csv')

# Filter for significant credit changes
significant_credit = df[df['Credit_TTest_Significant'] == True]

# Filter for large effect sizes
large_effects = df[df['Credit_Effect_Size'] == 'large']

# Save filtered results
significant_credit.to_csv('significant_changes.csv', index=False)
```

### Custom Metrics

Add more transaction columns to analyze:

1. Edit `config.py`:
```python
COLUMNS_OF_INTEREST = [
    'Debit',
    'Credit',
    'Running Balance',
    'GST',
    'YourCustomColumn'  # Add here
]
```

2. Ensure the column exists in your JSON transaction data

## Troubleshooting

### "Insufficient data for account code"
- Account has too few data points for statistical analysis
- Needs at least 2 different values per period
- These accounts are automatically skipped

### "No results generated"
- Check JSON structure matches expected format
- Verify required fields exist in transactions
- Ensure dates are valid

### Large File Processing
- The tool handles large JSON files (tested with 160K+ lines)
- Processing time: ~1-2 minutes per 100 account codes

## Performance

- Tested with: 126 account codes
- Successfully processed: 69 account codes
- Skipped (insufficient data): 57 account codes
- Output columns: 134 metrics per account
- Processing time: ~30 seconds

## Output File Details

**File**: `gl_analysis_results_monthly.csv`

**Structure**:
- 1 header row
- 1 row per account code (69 rows in example)
- 134 columns of metrics

**Size**: Approximately 50-100 KB for 70 account codes

## Dependencies

```bash
pip install pandas scipy numpy python-dateutil
```

## Best Practices

1. **Start with monthly analysis** - Most balanced time period
2. **Review significant changes first** - Filter CSV by `*_Significant == True`
3. **Check effect sizes** - Focus on medium/large effects
4. **Compare multiple periods** - Run weekly, monthly, quarterly for complete picture
5. **Keep raw data** - Archive JSON files for reanalysis

## Notes

- All statistical tests use α = 0.05 (95% confidence level)
- Account codes with insufficient data are automatically skipped
- Results are deterministic (same input = same output)
- CSV can be opened in Excel, imported to databases, or processed with pandas

## Support

For issues or questions:
1. Check JSON format matches specification
2. Verify all required transaction fields exist
3. Ensure dates are in valid format
4. Review console output for specific error messages

---

**Remember**: This tool processes each account code independently, giving you granular insights into every account's statistical changes year-over-year!
