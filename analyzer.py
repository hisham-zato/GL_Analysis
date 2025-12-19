# analyzer.py
# Orchestrates the statistical analysis workflow for multiple account codes

from statisticsal_inferences import StatisticalInferences
import config
import pandas as pd


class GLAnalyzer:
    """Main analyzer that coordinates statistical inference analysis for multiple account codes"""
    
    def __init__(self, account_data):
        """
        Initialize with account-structured data
        
        Args:
            account_data: Dict with account codes as keys, each containing:
                - account_name
                - current_year (DataFrame)
                - previous_year (DataFrame)
        """
        self.account_data = account_data
        self.columns_of_interest = config.COLUMNS_OF_INTEREST
        
    def run_analysis_for_all_accounts(self, period='monthly'):
        """
        Run statistical analysis for all account codes
        
        Args:
            period: Aggregation period ('weekly', 'bi-weekly', 'monthly', 'quarterly')
            
        Returns:
            DataFrame with account-code-wise results
        """
        print(f"\n{'='*80}")
        print(f"Starting Statistical Analysis - {period.upper()} aggregation")
        print(f"Processing {len(self.account_data)} account codes...")
        print(f"{'='*80}\n")
        
        all_results = []
        successful = 0
        skipped = 0
        
        for account_code, data in sorted(self.account_data.items()):
            account_name = data['account_name']
            df_current = data['current_year']
            df_previous = data['previous_year']
            
            # Skip if both dataframes are empty
            if df_current.empty and df_previous.empty:
                skipped += 1
                continue
            
            print(f"Processing Account Code: {account_code} - {account_name}")
            
            try:
                # Initialize statistical inference engine
                stats_engine = StatisticalInferences(
                    df_previous,
                    df_current,
                    self.columns_of_interest
                )
                
                # Run comparison
                desc_last_year, desc_current_year, comparison_df = \
                    stats_engine.compare_statistical_inferences(period)
                
                if not comparison_df.empty:
                    # Extract metrics for this account code
                    result = self._extract_metrics(
                        account_code,
                        account_name,
                        desc_last_year,
                        desc_current_year,
                        comparison_df
                    )
                    all_results.append(result)
                    successful += 1
                    print(f"  ✓ Analysis completed for {account_code}")
                else:
                    print(f"  ⚠ Insufficient data for {account_code}")
                    skipped += 1
                    
            except Exception as e:
                print(f"  ✗ Error processing {account_code}: {e}")
                skipped += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"Analysis Summary:")
        print(f"  - Successfully processed: {successful} account codes")
        print(f"  - Skipped: {skipped} account codes")
        print(f"{'='*80}\n")
        
        if all_results:
            results_df = pd.DataFrame(all_results)
            return results_df
        else:
            print("⚠ No results generated")
            return pd.DataFrame()
    
    def _extract_metrics(self, account_code, account_name, desc_last_year, 
                        desc_current_year, comparison_df):
        """Extract all metrics into a single row for this account code"""
        
        result = {
            'Account Code': account_code,
            'Account Name': account_name
        }
        
        # Extract metrics for each column of interest
        for column in self.columns_of_interest:
            if column not in comparison_df.columns:
                continue
                
            data = comparison_df[column]
            prefix = column.replace(' ', '_')
            
            # Descriptive statistics - Previous Year
            if not desc_last_year.empty and column in desc_last_year.columns:
                result[f'{prefix}_LY_Mean'] = desc_last_year[column].get('mean', None)
                result[f'{prefix}_LY_Std'] = desc_last_year[column].get('std', None)
                result[f'{prefix}_LY_Min'] = desc_last_year[column].get('min', None)
                result[f'{prefix}_LY_Max'] = desc_last_year[column].get('max', None)
                result[f'{prefix}_LY_Median'] = desc_last_year[column].get('50%', None)
            
            # Descriptive statistics - Current Year
            if not desc_current_year.empty and column in desc_current_year.columns:
                result[f'{prefix}_CY_Mean'] = desc_current_year[column].get('mean', None)
                result[f'{prefix}_CY_Std'] = desc_current_year[column].get('std', None)
                result[f'{prefix}_CY_Min'] = desc_current_year[column].get('min', None)
                result[f'{prefix}_CY_Max'] = desc_current_year[column].get('max', None)
                result[f'{prefix}_CY_Median'] = desc_current_year[column].get('50%', None)
            
            # Differences
            result[f'{prefix}_Mean_Diff'] = data.get('mean_diff', None)
            result[f'{prefix}_Std_Diff'] = data.get('std_diff', None)
            result[f'{prefix}_Min_Diff'] = data.get('min_diff', None)
            result[f'{prefix}_Max_Diff'] = data.get('max_diff', None)
            result[f'{prefix}_Median_Diff'] = data.get('50%_diff', None)
            
            # Statistical tests
            result[f'{prefix}_TTest_Statistic'] = data.get('t_stat', None)
            result[f'{prefix}_TTest_PValue'] = data.get('t_pval', None)
            result[f'{prefix}_TTest_Significant'] = data.get('t_significant', None)
            
            result[f'{prefix}_MannWhitney_Statistic'] = data.get('u_stat', None)
            result[f'{prefix}_MannWhitney_PValue'] = data.get('u_pval', None)
            result[f'{prefix}_MannWhitney_Significant'] = data.get('u_significant', None)
            
            result[f'{prefix}_ANOVA_FStatistic'] = data.get('anova_f_stat', None)
            result[f'{prefix}_ANOVA_PValue'] = data.get('anova_pval', None)
            result[f'{prefix}_ANOVA_Significant'] = data.get('anova_significant', None)
            
            result[f'{prefix}_KS_Statistic'] = data.get('ks_stat', None)
            result[f'{prefix}_KS_PValue'] = data.get('ks_pval', None)
            result[f'{prefix}_KS_Significant'] = data.get('ks_significant', None)
            
            # Effect size
            result[f'{prefix}_Cohens_D'] = data.get('cohens_d', None)
            result[f'{prefix}_Effect_Size'] = data.get('effect_size', None)
            
            # Correlation (if available)
            result[f'{prefix}_Correlation'] = data.get('corr_coef', None)
            result[f'{prefix}_Correlation_PValue'] = data.get('corr_pval', None)
            result[f'{prefix}_Correlation_Significant'] = data.get('corr_significant', None)
            result[f'{prefix}_Correlation_Strength'] = data.get('corr_strength', None)
        
        return result
