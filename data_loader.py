# data_loader.py
# Handles loading and validation of GL data from JSON objects

import pandas as pd
import sys
import json


class DataLoader:
    """Loads and validates GL data from JSON objects"""
    
    def __init__(self, current_year_json, previous_year_json):
        """
        Initialize with JSON objects (dicts)
        
        Args:
            current_year_json: Dict with account codes as keys, each containing transactions
            previous_year_json: Dict with account codes as keys, each containing transactions
        """
        self.current_year_json = current_year_json
        self.previous_year_json = previous_year_json
        
    def load_from_json(self):
        """Load and structure data from JSON objects"""
        try:
            print("Processing JSON data...")
            
            # Get all unique account codes from both years
            current_codes = set(self.current_year_json.keys())
            previous_codes = set(self.previous_year_json.keys())
            all_codes = current_codes.union(previous_codes)
            
            print(f"✓ Found {len(current_codes)} account codes in current year")
            print(f"✓ Found {len(previous_codes)} account codes in previous year")
            print(f"✓ Total unique account codes: {len(all_codes)}")
            
            # Structure data by account code
            account_data = {}
            
            for account_code in all_codes:
                account_data[account_code] = {
                    'account_name': None,
                    'current_year': pd.DataFrame(),
                    'previous_year': pd.DataFrame()
                }
                
                # Get current year data
                if account_code in self.current_year_json:
                    acc_info = self.current_year_json[account_code]
                    account_data[account_code]['account_name'] = acc_info.get('account_name', 'Unknown')
                    
                    if 'transactions' in acc_info and acc_info['transactions']:
                        df_current = pd.DataFrame(acc_info['transactions'])
                        account_data[account_code]['current_year'] = df_current
                
                # Get previous year data
                if account_code in self.previous_year_json:
                    acc_info = self.previous_year_json[account_code]
                    if not account_data[account_code]['account_name']:
                        account_data[account_code]['account_name'] = acc_info.get('account_name', 'Unknown')
                    
                    if 'transactions' in acc_info and acc_info['transactions']:
                        df_previous = pd.DataFrame(acc_info['transactions'])
                        account_data[account_code]['previous_year'] = df_previous
            
            return account_data
            
        except Exception as e:
            print(f"✗ Error processing JSON data: {e}")
            sys.exit(1)
    
    def validate_data(self, df_current, df_previous, required_columns):
        """Validate that required columns exist in the data"""
        if df_current.empty and df_previous.empty:
            return False
        
        try:
            # Check current year if not empty
            if not df_current.empty:
                missing_current = [col for col in required_columns if col not in df_current.columns]
                if missing_current:
                    return False
            
            # Check previous year if not empty
            if not df_previous.empty:
                missing_previous = [col for col in required_columns if col not in df_previous.columns]
                if missing_previous:
                    return False
            
            return True
            
        except Exception as e:
            return False
    
    @staticmethod
    def load_json_from_file(filepath):
        """Helper method to load JSON from file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"✗ Error loading JSON file {filepath}: {e}")
            sys.exit(1)
