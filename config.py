# config.py
# Configuration settings for GL Analysis

# Columns to analyze
COLUMNS_OF_INTEREST = [
    'Debit',
    'Credit',
    'Running Balance',
    'GST'
]

# Analysis periods available
ANALYSIS_PERIODS = ['weekly', 'bi-weekly', 'monthly', 'quarterly']

# Default analysis period
DEFAULT_PERIOD = 'monthly'

# Statistical significance threshold
SIGNIFICANCE_LEVEL = 0.05

# Output settings
CONSOLE_OUTPUT = True
SHOW_DETAILED_STATS = True
