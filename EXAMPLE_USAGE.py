#!/usr/bin/env python3
"""
Example Usage Scenarios for GL Analysis Tool

This file demonstrates different ways to use the GL analysis tool
depending on your specific needs.
"""

import json
import pandas as pd
from data_loader import DataLoader
from analyzer import GLAnalyzer
from main import analyze_from_json_objects


# ============================================================================
# SCENARIO 1: Basic Usage - Files on Disk
# ============================================================================
def scenario_1_basic_file_usage():
    """
    You have JSON files saved on disk and want to analyze them.
    This is the simplest approach.
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Basic File Usage")
    print("="*80)
    
    # Load JSON files
    current_year_json = DataLoader.load_json_from_file('gl_current_year_data.json')
    previous_year_json = DataLoader.load_json_from_file('gl_last_year_data.json')
    
    # Run analysis
    output_file = analyze_from_json_objects(
        current_year_json,
        previous_year_json,
        period='monthly',
        output_filename='results_scenario_1.csv'
    )
    
    print(f"\nResults saved to: {output_file}")


# ============================================================================
# SCENARIO 2: Already Have JSON Objects in Memory
# ============================================================================
def scenario_2_json_objects_in_memory():
    """
    You've already loaded/created JSON objects in your application
    and want to pass them directly without saving to files.
    """
    print("\n" + "="*80)
    print("SCENARIO 2: JSON Objects in Memory")
    print("="*80)
    
    # Assume you have these objects from your application
    current_year_data = {
        "180/001": {
            "account_code": "180/001",
            "account_name": "Sales - Labour",
            "transactions": [
                {
                    "Date": "2024-01-15",
                    "Account Code": "180/001",
                    "Debit": 0.0,
                    "Credit": 1000.0,
                    "Running Balance": -1000.0,
                    "GST": -150.0,
                    "GST Rate": 15.0,
                    "GST Rate Name": "15% GST on Income"
                },
                # ... more transactions
            ]
        },
        # ... more account codes
    }
    
    previous_year_data = {
        # Similar structure for previous year
    }
    
    # Run analysis directly
    output_file = analyze_from_json_objects(
        current_year_data,
        previous_year_data,
        period='monthly',
        output_filename='results_scenario_2.csv'
    )
    
    print(f"\nResults saved to: {output_file}")


# ============================================================================
# SCENARIO 3: Multiple Analysis Periods
# ============================================================================
def scenario_3_multiple_periods():
    """
    Generate reports for different time aggregations to see trends
    at various granularities.
    """
    print("\n" + "="*80)
    print("SCENARIO 3: Multiple Analysis Periods")
    print("="*80)
    
    # Load data once
    current_year_json = DataLoader.load_json_from_file('gl_current_year_data.json')
    previous_year_json = DataLoader.load_json_from_file('gl_last_year_data.json')
    
    # Prepare data structure
    loader = DataLoader(current_year_json, previous_year_json)
    account_data = loader.load_from_json()
    
    # Analyze at different periods
    analyzer = GLAnalyzer(account_data)
    
    for period in ['weekly', 'monthly', 'quarterly']:
        print(f"\nAnalyzing at {period} level...")
        results = analyzer.run_analysis_for_all_accounts(period=period)
        
        if not results.empty:
            filename = f'analysis_{period}.csv'
            results.to_csv(filename, index=False)
            print(f"✓ {period.capitalize()} results saved to: {filename}")


# ============================================================================
# SCENARIO 4: Filter and Export Specific Results
# ============================================================================
def scenario_4_filtered_results():
    """
    Run analysis and immediately filter for specific insights,
    then export only relevant data.
    """
    print("\n" + "="*80)
    print("SCENARIO 4: Filtered Results")
    print("="*80)
    
    # Run analysis
    output_file = analyze_from_json_objects(
        DataLoader.load_json_from_file('gl_current_year_data.json'),
        DataLoader.load_json_from_file('gl_last_year_data.json'),
        period='monthly',
        output_filename='full_results.csv'
    )
    
    # Load and filter results
    df = pd.read_csv(output_file)
    
    # Filter 1: Significant credit changes only
    significant_credit = df[df['Credit_TTest_Significant'] == True]
    significant_credit.to_csv('significant_credit_changes.csv', index=False)
    print(f"\n✓ Found {len(significant_credit)} accounts with significant credit changes")
    
    # Filter 2: Large effect sizes only
    large_effects = df[
        (df['Credit_Effect_Size'] == 'large') |
        (df['Debit_Effect_Size'] == 'large') |
        (df['GST_Effect_Size'] == 'large')
    ]
    large_effects.to_csv('large_effect_sizes.csv', index=False)
    print(f"✓ Found {len(large_effects)} accounts with large effect sizes")
    
    # Filter 3: Top 20 increases and decreases
    top_increases = df.nlargest(20, 'Credit_Mean_Diff')
    top_increases.to_csv('top_20_increases.csv', index=False)
    
    top_decreases = df.nsmallest(20, 'Credit_Mean_Diff')
    top_decreases.to_csv('top_20_decreases.csv', index=False)
    
    print(f"✓ Exported top 20 increases and decreases")


# ============================================================================
# SCENARIO 5: Specific Account Codes Only
# ============================================================================
def scenario_5_specific_accounts():
    """
    Analyze only specific account codes of interest
    instead of all accounts.
    """
    print("\n" + "="*80)
    print("SCENARIO 5: Specific Account Codes")
    print("="*80)
    
    # Load data
    current_year_json = DataLoader.load_json_from_file('gl_current_year_data.json')
    previous_year_json = DataLoader.load_json_from_file('gl_last_year_data.json')
    
    loader = DataLoader(current_year_json, previous_year_json)
    account_data = loader.load_from_json()
    
    # Filter to specific accounts
    accounts_of_interest = ['180/001', '180/002', '220', '246']
    filtered_data = {
        code: data for code, data in account_data.items()
        if code in accounts_of_interest
    }
    
    print(f"\nAnalyzing {len(filtered_data)} specific account codes...")
    
    # Analyze only these accounts
    analyzer = GLAnalyzer(filtered_data)
    results = analyzer.run_analysis_for_all_accounts(period='monthly')
    
    if not results.empty:
        results.to_csv('specific_accounts_analysis.csv', index=False)
        print(f"✓ Results saved for {len(results)} accounts")


# ============================================================================
# SCENARIO 6: Create Executive Summary
# ============================================================================
def scenario_6_executive_summary():
    """
    Run analysis and create a simplified executive summary
    with only key metrics.
    """
    print("\n" + "="*80)
    print("SCENARIO 6: Executive Summary")
    print("="*80)
    
    # Run full analysis
    output_file = analyze_from_json_objects(
        DataLoader.load_json_from_file('gl_current_year_data.json'),
        DataLoader.load_json_from_file('gl_last_year_data.json'),
        period='monthly',
        output_filename='full_analysis.csv'
    )
    
    # Load results
    df = pd.read_csv(output_file)
    
    # Create executive summary with key columns only
    summary_columns = [
        'Account Code',
        'Account Name',
        'Credit_LY_Mean',
        'Credit_CY_Mean',
        'Credit_Mean_Diff',
        'Credit_TTest_Significant',
        'Credit_Effect_Size',
        'Debit_LY_Mean',
        'Debit_CY_Mean',
        'Debit_Mean_Diff',
        'GST_LY_Mean',
        'GST_CY_Mean',
        'GST_Mean_Diff'
    ]
    
    summary = df[summary_columns].copy()
    
    # Add a "Needs Review" flag
    summary['Needs_Review'] = (
        (df['Credit_TTest_Significant'] == True) |
        (df['Credit_Effect_Size'] == 'large') |
        (df['Debit_TTest_Significant'] == True) |
        (df['Debit_Effect_Size'] == 'large')
    )
    
    # Sort by accounts needing review first
    summary = summary.sort_values('Needs_Review', ascending=False)
    
    # Save executive summary
    summary.to_csv('executive_summary.csv', index=False)
    
    print(f"\n✓ Executive summary created with {len(summary)} accounts")
    print(f"✓ {summary['Needs_Review'].sum()} accounts flagged for review")


# ============================================================================
# SCENARIO 7: Comparison Across Periods
# ============================================================================
def scenario_7_period_comparison():
    """
    Compare how results differ when using different aggregation periods.
    """
    print("\n" + "="*80)
    print("SCENARIO 7: Period Comparison")
    print("="*80)
    
    # Load data
    current_year_json = DataLoader.load_json_from_file('gl_current_year_data.json')
    previous_year_json = DataLoader.load_json_from_file('gl_last_year_data.json')
    
    loader = DataLoader(current_year_json, previous_year_json)
    account_data = loader.load_from_json()
    
    analyzer = GLAnalyzer(account_data)
    
    # Analyze at different periods and collect key metrics
    comparison_data = []
    
    for period in ['weekly', 'monthly', 'quarterly']:
        print(f"\nAnalyzing at {period} level...")
        results = analyzer.run_analysis_for_all_accounts(period=period)
        
        if not results.empty:
            # Count significant changes
            sig_credit = results['Credit_TTest_Significant'].sum()
            sig_debit = results['Debit_TTest_Significant'].sum()
            
            comparison_data.append({
                'Period': period,
                'Accounts_Analyzed': len(results),
                'Significant_Credit_Changes': sig_credit,
                'Significant_Debit_Changes': sig_debit,
                'Large_Credit_Effects': (results['Credit_Effect_Size'] == 'large').sum(),
                'Large_Debit_Effects': (results['Debit_Effect_Size'] == 'large').sum()
            })
    
    # Create comparison summary
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df.to_csv('period_comparison_summary.csv', index=False)
    
    print("\n" + "="*80)
    print("Period Comparison Summary:")
    print("="*80)
    print(comparison_df.to_string(index=False))


# ============================================================================
# MAIN - Run Examples
# ============================================================================
def main():
    """
    Uncomment the scenario you want to run.
    """
    print("\nGL Analysis Tool - Usage Examples")
    print("="*80)
    print("\nUncomment the scenario you want to run in this file.")
    print("\nAvailable scenarios:")
    print("  1. Basic file usage")
    print("  2. JSON objects in memory")
    print("  3. Multiple analysis periods")
    print("  4. Filtered results")
    print("  5. Specific account codes")
    print("  6. Executive summary")
    print("  7. Period comparison")
    print("\n")
    
    # Uncomment the scenario you want to run:
    
    # scenario_1_basic_file_usage()
    # scenario_2_json_objects_in_memory()
    # scenario_3_multiple_periods()
    # scenario_4_filtered_results()
    # scenario_5_specific_accounts()
    # scenario_6_executive_summary()
    # scenario_7_period_comparison()


if __name__ == "__main__":
    main()
