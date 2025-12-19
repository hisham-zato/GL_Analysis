#!/usr/bin/env python3
"""
GL Analysis Tool - Main Entry Point

Simple interface to analyze General Ledger data from JSON objects.
Processes each account code separately and outputs results to CSV.

Usage:
    1. Load your JSON files into Python objects
    2. Pass them to the analyzer
    3. Get CSV output with account-code-wise results
"""

from data_loader import DataLoader
from analyzer import GLAnalyzer
import config
import json
import os
import pandas as pd
import numpy as np

from helper import (
    ACCOUNT_CODE,
    ACCOUNT_NAME_REFERENCE,
    find_header_row_without_sheetname,
    convert_file,
    preprocess_df,
    ACCOUNT_CODE_REFERENCE
)


# function to save GL data to database
def load_gl_data(gl_path):
    print(f'Loading GL data from file: {gl_path}')
    header = find_header_row_without_sheetname(gl_path)

    output_folder_path = os.path.dirname(gl_path)
    convert_file(gl_path, output_folder_path, 'csv')
    csv_path = os.path.splitext(gl_path)[0] + '.csv'

    # Convert CSV to temporary Excel file
    temp_excel_path = os.path.splitext(gl_path)[0] + '_temp.xlsx'
    df_csv = pd.read_csv(csv_path, dtype={ACCOUNT_CODE: str})

    df_csv.columns = ["" if col.startswith("Unnamed") else col for col in df_csv.columns]
    df_csv.to_excel(temp_excel_path, index=False)

    # Read back from temp Excel
    df = pd.read_excel(temp_excel_path, header=header, dtype={'Account Code': str})

    print(df.shape[0], 'records in the GL file')
    required_gl_columns = ['Date', 'Account Code', 'Account Type','Source','Description', 'Reference', 'Debit', 'Credit', 'Running Balance', 'GST', 'GST Rate', 'GST Rate Name']
    missing_columns = [col for col in required_gl_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f'Missing required columns in GL file: {", ".join(missing_columns)}')

    pre_df = preprocess_df(df)

    # Normalize NaN → None for JSON safety
    df = pre_df.replace({np.nan: None})

    # Keep only actual transaction rows
    df = df[df["Row Type"] == "transaction"]

    # Columns to retain inside each transaction
    transaction_cols = [
        "Date",
        "Account Code",
        "Account Type",
        "Source",
        "Description",
        "Reference",
        "Debit",
        "Credit",
        "Running Balance",
        "GST",
        "GST Rate",
        "GST Rate Name",
    ]

    grouped_json = {}

    for account_code, group in df.groupby("Account Code Reference", dropna=True):
        account_code = str(account_code)

        # Get account name safely
        account_name = (
            group["Account Name Reference"]
            .dropna()
            .iloc[0]
            if "Account Name Reference" in group and not group["Account Name Reference"].dropna().empty
            else None
        )

        transactions = group[transaction_cols].to_dict(orient="records")

        grouped_json[account_code] = {
            "account_code": account_code,
            "account_name": account_name,
            "transactions": transactions,
        }

    return grouped_json


def analyze_from_json_objects(current_year_json_obj, previous_year_json_obj, 
                              period='monthly', output_filename='gl_analysis_results.csv'):
    """
    Run analysis directly from JSON objects (dicts) already loaded in memory
    
    Args:
        current_year_json_obj: Dict with account codes and transactions for current year
        previous_year_json_obj: Dict with account codes and transactions for previous year
        period: Analysis period ('weekly', 'bi-weekly', 'monthly', 'quarterly')
        output_filename: Name for the output CSV file
        
    Returns:
        Path to the output CSV file
    """
    print("\n" + "="*80)
    print("GL STATISTICAL ANALYSIS TOOL - JSON OBJECT VERSION".center(80))
    print("="*80)
    
    # Process data
    print("\nProcessing data by account code...")
    loader = DataLoader(current_year_json_obj, previous_year_json_obj)
    account_data = loader.load_from_json()
    
    # Run analysis
    print("\nRunning statistical analysis...")
    analyzer = GLAnalyzer(account_data)
    results_df = analyzer.run_analysis_for_all_accounts(period=period)
    
    # Save results
    if not results_df.empty:
        
        results_df.to_csv(output_filename, index=False)
        
        print(f"\n{'='*80}")
        print("RESULTS SAVED!")
        print(f"{'='*80}")
        print(f"\n✓ Output file: {output_filename}")
        print(f"✓ Total account codes analyzed: {len(results_df)}")
        print(f"✓ Total columns in output: {len(results_df.columns)}")
        
        print(f"\n{'='*80}")
        print("Analysis completed successfully!")
        print(f"{'='*80}\n")
        
        return output_filename
    else:
        print("\n✗ No results generated. Please check your data.")
        return None


def analyze_from_gl_file(current_gl_file_path, previous_gl_file_path, 
                         period='monthly', output_filename='gl_analysis_results.csv'):
    """
    Run analysis directly from GL files (Excel/CSV)
    Args:
        current_gl_file_path: Path to current year GL file
        previous_gl_file_path: Path to previous year GL file
        period: Analysis period ('weekly', 'bi-weekly', 'monthly', 'quarterly')
        output_filename: Name for the output CSV file

    Returns:
        results_df: DataFrame with analysis results
    """
    print("\n" + "="*80)
    print("GL STATISTICAL ANALYSIS TOOL - GL FILE VERSION".center(80))
    print("="*80)
    # Load GL data from files
    print("\nLoading GL data from files...")
    current_year_json = load_gl_data(current_gl_file_path)
    previous_year_json = load_gl_data(previous_gl_file_path)

    # save json for debugging
    with open('current_year_debug.json', 'w') as f:
        json.dump(current_year_json, f, indent=4)
    with open('previous_year_debug.json', 'w') as f:
        json.dump(previous_year_json, f, indent=4)

    # Process data
    print("\nProcessing data by account code...")
    loader = DataLoader(current_year_json, previous_year_json)
    account_data = loader.load_from_json()

    # Run analysis
    print("\nRunning statistical analysis...")
    analyzer = GLAnalyzer(account_data)
    results_df = analyzer.run_analysis_for_all_accounts(period=period)
    
    # Save results
    if not results_df.empty:
        
        results_df.to_csv(output_filename, index=False)
        
        print(f"\n{'='*80}")
        print("RESULTS SAVED!")
        print(f"{'='*80}")
        print(f"\n✓ Output file: {output_filename}")
        print(f"✓ Total account codes analyzed: {len(results_df)}")
        print(f"✓ Total columns in output: {len(results_df.columns)}")
        
        print(f"\n{'='*80}")
        print("Analysis completed successfully!")
        print(f"{'='*80}\n")
        
        return results_df
    else:
        print("\n✗ No results generated. Please check your data.")
        return None


def main():
    """Main entry point for GL analysis"""
    
    # ====================
    # STEP 1: LOAD JSON FILES
    # ====================
    print("\n" + "="*80)
    print("GL STATISTICAL ANALYSIS TOOL - JSON INPUT VERSION".center(80))
    print("="*80)
    
    print("\nStep 1: Loading JSON files...")
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load JSON files into Python objects
    current_year_json = DataLoader.load_json_from_file(os.path.join(script_dir, 'gl_current_year_data.json'))
    previous_year_json = DataLoader.load_json_from_file(os.path.join(script_dir, 'gl_last_year_data.json'))
    
    print("✓ JSON files loaded successfully")
    
    
    # ====================
    # STEP 2: PROCESS DATA AND RUN ANALYSIS
    # ====================
    print("\nStep 2: Processing data and running analysis...")
    output_csv = analyze_from_json_objects(
        current_year_json,
        previous_year_json,
        period='monthly',
        output_filename=os.path.join(script_dir, 'gl_analysis_results.csv')
    )
    if output_csv:
        print(f"✓ Analysis results saved to: {output_csv}")
    else:
        print("✗ Analysis failed or produced no results.")


if __name__ == "__main__":
    main()