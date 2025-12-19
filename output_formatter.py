# output_formatter.py
# Formats and displays analysis results in the console

import pandas as pd


class OutputFormatter:
    """Formats statistical analysis results for console output"""
    
    def __init__(self):
        self.separator = "=" * 80
        self.sub_separator = "-" * 80
    
    def print_header(self, title):
        """Print a formatted section header"""
        print(f"\n{self.separator}")
        print(f"{title.center(80)}")
        print(f"{self.separator}\n")
    
    def print_section(self, title):
        """Print a formatted subsection header"""
        print(f"\n{title}")
        print(f"{self.sub_separator}")
    
    def display_descriptive_stats(self, desc_last_year, desc_current_year, period):
        """Display descriptive statistics comparison"""
        self.print_header(f"DESCRIPTIVE STATISTICS ({period.upper()} AGGREGATION)")
        
        if desc_last_year.empty or desc_current_year.empty:
            print("⚠ No data available for comparison")
            return
        
        self.print_section("PREVIOUS YEAR STATISTICS")
        print(desc_last_year.to_string())
        
        self.print_section("CURRENT YEAR STATISTICS")
        print(desc_current_year.to_string())
    
    def display_comparison_results(self, comparison_df):
        """Display detailed comparison and statistical test results"""
        self.print_header("STATISTICAL COMPARISON & INFERENCE TESTS")
        
        if comparison_df.empty:
            print("⚠ No comparison data available")
            return
        
        for column in comparison_df.columns:
            self.print_section(f"Analysis for: {column}")
            
            data = comparison_df[column]
            
            # Descriptive differences
            print("\n📊 Descriptive Changes:")
            print(f"   Mean Difference:    {data.get('mean_diff', 'N/A'):.2f}")
            print(f"   Std Dev Difference: {data.get('std_diff', 'N/A'):.2f}")
            print(f"   Min Difference:     {data.get('min_diff', 'N/A'):.2f}")
            print(f"   Max Difference:     {data.get('max_diff', 'N/A'):.2f}")
            print(f"   Median Difference:  {data.get('50%_diff', 'N/A'):.2f}")
            
            # Statistical tests
            print("\n🔬 Statistical Tests:")
            
            # T-Test
            t_sig = "✓ SIGNIFICANT" if data.get('t_significant', False) else "✗ Not significant"
            print(f"   T-Test:             {t_sig}")
            print(f"      - Statistic:     {data.get('t_stat', 'N/A'):.4f}")
            print(f"      - P-value:       {data.get('t_pval', 'N/A'):.4f}")
            
            # Mann-Whitney U Test
            u_sig = "✓ SIGNIFICANT" if data.get('u_significant', False) else "✗ Not significant"
            print(f"   Mann-Whitney U:     {u_sig}")
            print(f"      - Statistic:     {data.get('u_stat', 'N/A'):.4f}")
            print(f"      - P-value:       {data.get('u_pval', 'N/A'):.4f}")
            
            # ANOVA
            anova_sig = "✓ SIGNIFICANT" if data.get('anova_significant', False) else "✗ Not significant"
            print(f"   ANOVA F-Test:       {anova_sig}")
            print(f"      - F-statistic:   {data.get('anova_f_stat', 'N/A'):.4f}")
            print(f"      - P-value:       {data.get('anova_pval', 'N/A'):.4f}")
            
            # Kolmogorov-Smirnov Test
            ks_sig = "✓ SIGNIFICANT" if data.get('ks_significant', False) else "✗ Not significant"
            print(f"   K-S Test:           {ks_sig}")
            print(f"      - Statistic:     {data.get('ks_stat', 'N/A'):.4f}")
            print(f"      - P-value:       {data.get('ks_pval', 'N/A'):.4f}")
            
            # Effect size
            if 'cohens_d' in data and pd.notna(data['cohens_d']):
                effect_size = data.get('effect_size', 'none').upper()
                print(f"\n📈 Effect Size:")
                print(f"   Cohen's d:          {data.get('cohens_d', 'N/A'):.4f}")
                print(f"   Magnitude:          {effect_size}")
            
            # Correlation (if available)
            if 'corr_coef' in data and pd.notna(data['corr_coef']):
                corr_sig = "✓ SIGNIFICANT" if data.get('corr_significant', False) else "✗ Not significant"
                corr_strength = data.get('corr_strength', 'none').upper()
                print(f"\n🔗 Correlation Analysis:")
                print(f"   Pearson r:          {data.get('corr_coef', 'N/A'):.4f}")
                print(f"   P-value:            {data.get('corr_pval', 'N/A'):.4f}")
                print(f"   Significance:       {corr_sig}")
                print(f"   Strength:           {corr_strength}")
            
            print()  # Add spacing between columns
    
    def display_summary(self, comparison_df):
        """Display a summary of significant findings"""
        self.print_header("SUMMARY OF SIGNIFICANT FINDINGS")
        
        if comparison_df.empty:
            print("⚠ No data available for summary")
            return
        
        significant_findings = []
        
        for column in comparison_df.columns:
            data = comparison_df[column]
            tests = []
            
            if data.get('t_significant', False):
                tests.append('T-Test')
            if data.get('u_significant', False):
                tests.append('Mann-Whitney')
            if data.get('anova_significant', False):
                tests.append('ANOVA')
            if data.get('ks_significant', False):
                tests.append('K-S Test')
            
            if tests:
                mean_diff = data.get('mean_diff', 0)
                effect = data.get('effect_size', 'unknown')
                direction = "increase" if mean_diff > 0 else "decrease"
                
                significant_findings.append({
                    'Column': column,
                    'Mean Change': f"{mean_diff:.2f}",
                    'Direction': direction.upper(),
                    'Effect Size': effect.upper(),
                    'Significant Tests': ', '.join(tests)
                })
        
        if significant_findings:
            summary_df = pd.DataFrame(significant_findings)
            print(summary_df.to_string(index=False))
            print(f"\n✓ Found {len(significant_findings)} column(s) with significant changes")
        else:
            print("✓ No statistically significant changes detected")
    
    def display_computation_results(self, results):
        """Display computation method results"""
        self.print_header("COMPUTATION METHODS ANALYSIS")
        
        for method_name, result in results.items():
            self.print_section(f"{method_name.upper().replace('_', ' ')}")
            
            value = result.get('value', 'N/A')
            threshold = result.get('threshold', 'N/A')
            exceeds = result.get('exceeds_threshold', False)
            
            status = "⚠ EXCEEDS THRESHOLD" if exceeds else "✓ Within threshold"
            
            if isinstance(value, (int, float)) and value != float('inf'):
                print(f"   Value:     {value:.2f}")
            else:
                print(f"   Value:     {value}")
            
            print(f"   Threshold: {threshold}")
            print(f"   Status:    {status}")
            print()
