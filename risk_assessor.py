import pandas as pd
import numpy as np
import json

class GLRiskAssessor:
    def __init__(self, df):
        self.df = df.copy()
        # The metrics available in your output
        self.metrics = ['Credit', 'Debit', 'Running_Balance', 'GST']

    def _calculate_cv(self, mean, std):
        """Calculate Coefficient of Variation (Volatility)"""
        if pd.isna(mean) or mean == 0 or pd.isna(std):
            return 0.0
        return abs(std / mean)

    def _get_account_type(self, name):
        """Guess account type for better interpretation text"""
        name = str(name).lower()
        if any(x in name for x in ['sales', 'revenue', 'income', 'received']):
            return 'Revenue'
        elif any(x in name for x in ['bank', 'cash', 'petty']):
            return 'Cash'
        elif any(x in name for x in ['gst', 'tax', 'payg']):
            return 'Tax'
        elif any(x in name for x in ['salary', 'wages', 'super', 'labour']):
            return 'Payroll'
        else:
            return 'Expense/Other'

    def _generate_interpretation(self, row, triggers, account_type):
        """Generate accounting-specific text based on statistical triggers"""
        text_parts = []
        
        # 1. Distribution Changes (KS Test)
        if "Distribution Change" in triggers:
            if account_type == 'Revenue':
                text_parts.append("Revenue recognition pattern has materially changed.")
            elif account_type == 'Expense/Other':
                text_parts.append("Expense posting behavior has shifted structurally.")
            else:
                text_parts.append("Fundamental change in transaction frequency/pattern.")

        # 2. High Volatility (High CV)
        if "High CV" in triggers:
            if account_type == 'Cash':
                text_parts.append("Cash flow shows high irregularity.")
            else:
                text_parts.append("Highly volatile activity suggests irregular accruals or one-off adjustments.")

        # 3. Mean Shifts (T-Test / Large Effect)
        if "Mean Shift" in triggers:
            direction = "increase" if "Increase" in triggers else "decrease"
            text_parts.append(f"Statistically significant {direction} in average value.")

        # 4. Skewness (Mean-Median Gap)
        if "Mean-Median Gap" in triggers:
            text_parts.append("Skewed distribution indicates lumpy postings or outliers.")

        if not text_parts:
            return "Stable account behavior consistent with prior year."
            
        return " ".join(text_parts)

    def assess_account(self, row):
        """Analyze a single row (account) and return risk details"""
        score = 0
        triggers = set()
        
        # Analyze each metric (Credit, Debit, etc.)
        for metric in self.metrics:
            # Check if columns exist (handling potential missing columns)
            p_col = f'{metric}_TTest_PValue'
            sig_col = f'{metric}_TTest_Significant'
            effect_col = f'{metric}_Effect_Size'
            ks_sig_col = f'{metric}_KS_Significant'
            
            if sig_col not in row: continue
            
            # --- RISK SCORING LOGIC ---
            
            # 1. Statistical Significance (Confidence)
            if row[sig_col] == True:
                score += 1
                triggers.add("Mean Shift")
                
                # Check direction
                if f'{metric}_Mean_Diff' in row and row[f'{metric}_Mean_Diff'] > 0:
                    triggers.add("Increase")
            
            # 2. Effect Size (Materiality)
            if row[effect_col] == 'large':
                score += 2 # Higher weight for large effects
                triggers.add("Large Effect Size")
            elif row[effect_col] == 'medium':
                score += 1

            # 3. Distribution Change (Behavioral Change)
            if ks_sig_col in row and row[ks_sig_col] == True:
                score += 2 # KS Test indicates fundamental behavior change
                triggers.add("Distribution Change")

            # 4. Volatility Check (Derived)
            # Compare Current Year Mean vs Std
            cy_mean = row.get(f'{metric}_CY_Mean', 0)
            cy_std = row.get(f'{metric}_CY_Std', 0)
            cy_median = row.get(f'{metric}_CY_Median', 0)
            
            cv = self._calculate_cv(cy_mean, cy_std)
            if cv > 1.5: # Threshold: Std Dev is 1.5x the Mean
                score += 1
                triggers.add("High CV")

            # 5. Skewness Check (Derived)
            # If Mean and Median differ by > 30%
            if abs(cy_mean) > 0:
                skew_pct = abs(cy_mean - cy_median) / abs(cy_mean)
                if skew_pct > 0.30:
                    score += 1
                    triggers.add("Mean-Median Gap")

        # --- TIER ASSIGNMENT ---
        tier = "Tier-3" # Low Risk / Ignore
        if score >= 4:
            tier = "Tier-1"
        elif score >= 2:
            tier = "Tier-2"

        # Generate Text
        acct_type = self._get_account_type(row['Account Name'])
        interpretation = self._generate_interpretation(row, triggers, acct_type)

        return pd.Series({
            'Tier': tier,
            'Account Code': row['Account Code'],
            'Account Name': row['Account Name'],
            'Key Metrics Triggered': ", ".join(sorted(list(triggers))) if triggers else "None",
            'Accounting Interpretation': interpretation,
            'Risk_Score': score # Internal use for sorting
        })

    def run(self):
        # Apply assessment to every row
        risk_df = self.df.apply(self.assess_account, axis=1)
        
        # Filter out Tier-3 (Low risk) to reduce noise
        risk_df = risk_df[risk_df['Tier'] != 'Tier-3']
        
        # Sort: Tier 1 first, then by internal Risk Score descending
        risk_df = risk_df.sort_values(by=['Tier', 'Risk_Score'], ascending=[True, False])
        
        # Clean up
        risk_df = risk_df.drop(columns=['Risk_Score'])
        
        return risk_df

# ==========================================
# USAGE EXAMPLE
# ==========================================

def generate_risk_report(input_file='gl_analysis_results_monthly.csv', output_file='gl_risk_report.csv'):
    print(f"Loading analysis results from {input_file}...")
    
    try:
        # Try loading CSV first
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        # Fallback to JSON preview for demonstration if CSV not found
        print("CSV not found, looking for JSON preview...")
        try:
            with open('gl_analysis_preview_monthly.json', 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        except:
            print("No data found.")
            return

    print(f"Analyzing {len(df)} accounts for risk patterns...")
    
    assessor = GLRiskAssessor(df)
    report_df = assessor.run()
    
    print(f"Found {len(report_df)} accounts with notable risks.")
    
    # Save
    report_df.to_csv(output_file, index=False)
    print(f"Risk report saved to: {output_file}")
    
    # Display preview
    print("\n" + "="*80)
    print("RISK REPORT PREVIEW")
    print("="*80)
    print(report_df.to_string(index=False))

if __name__ == "__main__":
    # Generate the report based on your previous output
    generate_risk_report()