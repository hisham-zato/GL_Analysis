import re
import decimal
import traceback
import pandas as pd
import datetime
from decimal import Decimal, ROUND_HALF_UP
import subprocess
import sys
import os
import numpy as np

ACCOUNT_NAME_REFERENCE = 'Account Name Reference'
ACCOUNT_CODE_REFERENCE = 'Account Code Reference'
ACCOUNT_CODE = 'Account Code'
ACCOUNT_TYPE = 'Account Type'
ROW_TYPE = 'Row Type'
RUNNING_BALANCE = 'Running Balance'
GST_RATE = 'GST Rate'
GST_RATE_NAME = "GST Rate Name"
INVESTIGATE_ACTION = "Investigate/Action"

def replace_in_strings(obj, old, new):
    if isinstance(obj, dict):
        return {k: replace_in_strings(v, old, new) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_in_strings(i, old, new) for i in obj]
    elif isinstance(obj, str):
        return obj.replace(old, new)
    else:
        return obj


def assign_account_codes(df: pd.DataFrame) -> pd.DataFrame:
    code_counter = 1
    columns_order = [col for col in df.columns if col != ACCOUNT_NAME_REFERENCE] + [ACCOUNT_NAME_REFERENCE]

    def process_group(group):
        nonlocal code_counter
        group = group.copy()
        group[ACCOUNT_CODE] = group[ACCOUNT_CODE].astype(str).where(group[ACCOUNT_CODE].notna(), '')
        mask = group[ACCOUNT_TYPE].notna() & (group[ACCOUNT_CODE] == '')
        if mask.any():
            group.loc[mask, ACCOUNT_CODE] = f'AC{code_counter}'
            code_counter += 1
        return group

    if ACCOUNT_NAME_REFERENCE in df.columns:
        updated_df = df.groupby(df[ACCOUNT_NAME_REFERENCE].fillna('No Reference'), group_keys=False).apply(process_group).reset_index(drop=True)
        
        # Ensure dtype compatibility before update
        df[ACCOUNT_CODE] = df[ACCOUNT_CODE].astype(str)
        updated_df[ACCOUNT_CODE] = updated_df[ACCOUNT_CODE].astype(str)
        
        df.update(updated_df[[ACCOUNT_CODE]])
        return updated_df.reindex(columns=columns_order)
    else:
        return df
    

def safe_decimal(value):
    try:
        if value is None or isinstance(value, str) and value.strip().lower() in ['nan', '']:
            return None
        
        if isinstance(value, str):
            value = value.strip()
            if value.startswith('(') and value.endswith(')'):
                value = '-' + value[1:-1]
        return Decimal(value) if isinstance(value, (int, float, str)) else None
    except (ValueError, TypeError, decimal.InvalidOperation):
        return None


def clean_account_code_reference(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def extract_acc_code(filtered: pd.DataFrame):
        """Extract account code using original priority rules."""
        if len(filtered) > 2 and pd.notna(filtered[ACCOUNT_CODE].iloc[2]):
            return filtered[ACCOUNT_CODE].iloc[2]
        if len(filtered) > 1 and pd.notna(filtered[ACCOUNT_CODE].iloc[1]):
            return filtered[ACCOUNT_CODE].iloc[1]
        return None

    def update_reference(df, acc_code_ref, acc_code):
        """Apply the two update rules exactly as before."""
        mask = df[ACCOUNT_NAME_REFERENCE] == acc_code_ref
        if acc_code.startswith("AC"):
            df.loc[mask, ACCOUNT_NAME_REFERENCE] = acc_code_ref.lstrip("- ").strip()
        elif acc_code_ref.startswith(acc_code):
            df.loc[mask, ACCOUNT_NAME_REFERENCE] = (
                acc_code_ref[len(acc_code):].lstrip("- ").strip()
            )

    for acc_code_ref in df[ACCOUNT_NAME_REFERENCE].unique():
        filtered_df = df[df[ACCOUNT_NAME_REFERENCE] == acc_code_ref]

        # skip if all ACCOUNT_CODE values are NaN → original guard
        if filtered_df[ACCOUNT_CODE].isna().all():
            continue

        acc_code = extract_acc_code(filtered_df)

        if isinstance(acc_code, str) and isinstance(acc_code_ref, str):
            update_reference(df, acc_code_ref, acc_code)

    return df

def create_row_type(df):
    df = df.copy()
    df['row_type'] = pd.NA  
    def determine_row_type(date_value):
        date_str = str(date_value).lower()
        if 'opening balance' in date_str:
            return 'opening'
        elif 'total' in date_str:
            return 'total'
        elif 'net movement' in date_str:
            return 'net'
        elif 'closing balance' in date_str:
            return 'closing'
        return pd.NA 
    df[ROW_TYPE] = df['Date'].apply(determine_row_type)
    mask = df[ROW_TYPE].isna()
    df.loc[mask, ROW_TYPE] = df.loc[mask].apply(
        lambda row: 'transaction' if pd.notna(row[ACCOUNT_CODE]) or pd.notna(row[ACCOUNT_TYPE]) else pd.NA,
        axis=1
    )
   
    df.dropna(subset=[ACCOUNT_NAME_REFERENCE], inplace=True) 
    return df


def create_account_code_reference(df):
    df['Date'] = df['Date'].astype(str)
    opening_rows = df[df['Date'].str.contains('Opening Balance', na=False)].index.tolist()
    # Move the index one step up but keep only valid, non-negative indices
    section_starts = [idx - 1 for idx in opening_rows if idx - 1 in df.index]
    section_ends = df[df['Date'].str.contains('Closing Balance', na=False)].index.tolist()

    df[ACCOUNT_CODE_REFERENCE] = ''

    for start_idx in section_starts:
        end_idx = next((end for end in section_ends if end > start_idx), len(df))
        section_codes = df.loc[start_idx:end_idx, ACCOUNT_CODE].replace('', pd.NA).dropna().mode()
        account_code_value = section_codes[0] if not section_codes.empty else 'Unknown'
        df.loc[start_idx:end_idx, ACCOUNT_CODE_REFERENCE] = account_code_value
    return df


def round_decimal(value, precision='0.01'):
    """Round Decimal to specified precision (default 2 decimal places)."""
    if value is None:
        return None
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)

def clean_int(value):
    try:
        if pd.isna(value):
            return None
        if isinstance(value, (int, float, Decimal)):
            return int(value)
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            if match:
                return int(match.group())
    except (ValueError, TypeError):
        pass
    return None



def convert_file(input_file, output_path, output_format):
    # Check if the input file exists
    if not os.path.isfile(input_file):
        print(f"Error: The file '{input_file}' does not exist.")
        return
    # Construct the LibreOffice command
    # command = ['libreoffice', '--headless', '--convert-to', output_format, input_file, '--outdir', output_path]
    command = ['libreoffice', '--headless', '--convert-to', output_format, '--outdir', output_path, input_file]
    # Run the command using subprocess
    try:
        subprocess.run(command, check=True)
        print(f"File '{input_file}' successfully converted to {output_format}.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Conversion failed with error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def find_header_row_without_sheetname(filepath, keyword="Date"):
    # Read the first few rows to find the header
    preview_df = pd.read_excel(filepath, nrows=10, header=None)
    for i, row in preview_df.iterrows():
        if keyword in row.values:
            return i
    raise ValueError(f"Keyword '{keyword}' not found in the first 10 rows")



#preprocess dataframe to save into database
def preprocess_df(df):
    df = add_group(df)
    df.rename(columns={'Account_Code_Category': ACCOUNT_NAME_REFERENCE}, inplace=True)
    df.replace({ACCOUNT_NAME_REFERENCE: {'': pd.NA}}, inplace=True)
    df.dropna(subset=[ACCOUNT_NAME_REFERENCE], inplace=True)
    df['Account_Code_Category'] = df[ACCOUNT_NAME_REFERENCE] # adding this column for WRC, GRC WP
    df[ACCOUNT_CODE_COPY] = df[ACCOUNT_CODE]
    df[ACCOUNT_CODE_COPY] = df[ACCOUNT_CODE_COPY].replace(pd.NA, '', regex=True)
    df = assign_account_codes(df)
    df = clean_account_code_reference(df)
    df = create_row_type(df)
    df = create_account_code_reference(df)
    return df


def add_group(data):
    df = data.copy()
    df['Account_Code_Category']=df['Date'].str.replace(r"^\d{2}/\d{2}/\d{4}$|^(Net movement|Opening Balance|Closing Balance|Total)", '',regex=True)
    df['Account_Code_Category'] = df['Account_Code_Category'].replace(r'^\s*$', np.nan, regex=True)
    df['Account_Code_Category'] = df['Account_Code_Category'].ffill()
    df['Account_Code_Category'] = df['Account_Code_Category'].str.strip()
    return df

ACCOUNT_NAME_REFERENCE = "Account Name Reference"
ACCOUNT_CODE = "Account Code"
ACCOUNT_CODE_COPY = "Account Code Copy"

