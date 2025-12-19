import pandas as pd
from scipy.stats import ttest_ind, mannwhitneyu, f_oneway, ks_2samp, pearsonr
import numpy as np
from dateutil import parser


class StatisticalInferences:
    def __init__(self, df_last_year, df_current_year, columns_of_interest):
        self.columns_of_interest = columns_of_interest
        self.df_last_year = self.load_and_prepare_data(df_last_year)
        self.df_current_year = self.load_and_prepare_data(df_current_year)

    def parse_dates(self, date_series):
        def try_parse(date_str):
            try:
                return parser.parse(str(date_str), dayfirst=True)
            except ValueError:
                return pd.NaT  # Return NaT for invalid dates

        return date_series.apply(try_parse)

    def convert_to_numeric(self, df, columns):
        for column in columns:
            df[column] = pd.to_numeric(df[column], errors='coerce')
        return df

    def load_and_prepare_data(self, df):
        if not df.empty:
            df['Date'] = self.parse_dates(df['Date'])
            df = df.dropna(subset=['Date'])
            df = self.convert_to_numeric(df, self.columns_of_interest)
            return df

    def aggregate(self, df, period):
        if df is not None and not df.empty:
            if period == 'weekly':
                df['Period'] = df['Date'].dt.to_period('W')
            elif period == 'bi-weekly':
                df['Period'] = (
                    df['Date']
                    .dt.to_period('W')
                    .astype(int)
                    // 2
                ).astype(str)
            elif period == 'monthly':
                df['Period'] = df['Date'].dt.to_period('M')
            elif period == 'quarterly':
                df['Period'] = df['Date'].dt.to_period('Q')
            else:
                raise ValueError("""Invalid period specified. Choose from 'weekly',
                                'bi-weekly', 'monthly', or 'quarterly'.""")
            return df.groupby('Period')[self.columns_of_interest].sum()
        else:
            return pd.DataFrame()

    def compare_statistical_inferences(self, period):
        
        self.monthly_last_year = self.aggregate(self.df_last_year, period)
        self.monthly_current_year = self.aggregate(self.df_current_year,
                                                   period)
        if not self.monthly_last_year.empty and not self.monthly_current_year.empty:
            describe_last_year = self.monthly_last_year.describe()
            describe_current_year = self.monthly_current_year.describe()

            comparison_inferences = {}

            for column in self.columns_of_interest:
                if column in self.monthly_current_year.columns and \
                    self.monthly_last_year[column].nunique() > 1 and \
                        self.monthly_current_year[column].nunique() > 1:
                    comparison_inferences[column] = {}
                    comparison_inferences[column]['mean_diff'] = (
                        describe_current_year[column]['mean'] -
                        describe_last_year[column]['mean']
                    )
                    comparison_inferences[column]['std_diff'] = (
                        describe_current_year[column]['std'] -
                        describe_last_year[column]['std']
                    )
                    comparison_inferences[column]['min_diff'] = (
                        describe_current_year[column]['min'] -
                        describe_last_year[column]['min']
                    )
                    comparison_inferences[column]['max_diff'] = (
                        describe_current_year[column]['max'] -
                        describe_last_year[column]['max']
                    )
                    comparison_inferences[column]['25%_diff'] = (
                        describe_current_year[column]['25%'] -
                        describe_last_year[column]['25%']
                    )
                    comparison_inferences[column]['50%_diff'] = (
                        describe_current_year[column]['50%'] -
                        describe_last_year[column]['50%']
                    )
                    comparison_inferences[column]['75%_diff'] = (
                        describe_current_year[column]['75%'] -
                        describe_last_year[column]['75%']
                    )

                    t_stat, t_pval = ttest_ind(self.monthly_last_year[column],
                                            self.monthly_current_year[column],
                                            nan_policy='omit')
                    comparison_inferences[column]['t_stat'] = t_stat
                    comparison_inferences[column]['t_pval'] = t_pval
                    comparison_inferences[column]['t_significant'] = t_pval < 0.05

                    u_stat, u_pval = mannwhitneyu(
                        self.monthly_last_year[column],
                        self.monthly_current_year[column],
                        alternative='two-sided')
                    comparison_inferences[column]['u_stat'] = u_stat
                    comparison_inferences[column]['u_pval'] = u_pval
                    comparison_inferences[column]['u_significant'] = u_pval < 0.05

                    f_stat, f_pval = f_oneway(self.monthly_last_year[column],
                                            self.monthly_current_year[column])
                    comparison_inferences[column]['anova_f_stat'] = f_stat
                    comparison_inferences[column]['anova_pval'] = f_pval
                    comparison_inferences[column]['anova_significant'] = (
                        f_pval < 0.05
                    )

                    ks_stat, ks_pval = ks_2samp(self.monthly_last_year[column],
                                                self.monthly_current_year[column])
                    comparison_inferences[column]['ks_stat'] = ks_stat
                    comparison_inferences[column]['ks_pval'] = ks_pval
                    comparison_inferences[column]['ks_significant'] = (
                        ks_pval < 0.05
                    )

                    if (len(self.monthly_last_year[column]) ==
                            len(self.monthly_current_year[column])):
                        corr_coef, corr_pval = pearsonr(
                            self.monthly_last_year[column],
                            self.monthly_current_year[column])
                        comparison_inferences[column]['corr_coef'] = corr_coef
                        comparison_inferences[column]['corr_pval'] = corr_pval
                        comparison_inferences[column]['corr_significant'] = (
                            corr_pval < 0.05
                        )
                        corr_abs = abs(corr_coef)
                        if 0.1 < corr_abs < 0.3:
                            corr_strength = 'weak'
                        elif 0.3 < corr_abs < 0.5:
                            corr_strength = 'moderate'
                        elif corr_abs > 0.5:
                            corr_strength = 'strong'
                        else:
                            corr_strength = 'none'
                        comparison_inferences[column]['corr_strength'] = corr_strength

                    mean_diff = comparison_inferences[column]['mean_diff']
                    pooled_std = np.sqrt(
                        (describe_last_year[column]['std']**2 +
                        describe_current_year[column]['std']**2) / 2
                    )
                    if pooled_std != 0:
                        cohens_d = mean_diff / pooled_std
                        comparison_inferences[column]['cohens_d'] = cohens_d
                        abs_cd = abs(cohens_d)
                        if abs_cd < 0.2:
                            effect_size = 'small'
                        elif abs_cd < 0.5:
                            effect_size = 'medium'
                        elif abs_cd >= 0.8:
                            effect_size = 'large'
                        else:
                            effect_size = 'none'
                        comparison_inferences[column]['effect_size'] = effect_size
                    else:
                        comparison_inferences[column]['cohens_d'] = np.nan
                        comparison_inferences[column]['effect_size'] = 'none'

            comparison_df = pd.DataFrame(comparison_inferences)

            return describe_last_year, describe_current_year, comparison_df
        return pd.DataFrame(),pd.DataFrame(),pd.DataFrame()
