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