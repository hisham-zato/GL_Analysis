import pandas as pd


class Compute:
    def __init__(self, current_year_file, previous_year_file, thresholds_file,
                 client_id):
        self.current_year_data = pd.read_excel(current_year_file,
                                               sheet_name='CY', skiprows=4)
        self.previous_year_data = pd.read_excel(previous_year_file,
                                                sheet_name='LY', skiprows=4)
        self.thresholds = pd.read_csv(thresholds_file)
        self.client_id = client_id
        self.threshold_values = self._load_thresholds()

    def _load_thresholds(self):
        client_thresholds = self.thresholds[
            self.thresholds['client_id'] == self.client_id
        ]
        return dict(
            zip(
                client_thresholds['computation_method'],
                client_thresholds['threshold_value']
            )
        )

    def _get_threshold(self, method_name):
        return self.threshold_values.get(method_name, 0)

    def check_credit(self):
        threshold = self._get_threshold('greater_than')
        values = (
            self.current_year_data[
                self.current_year_data['Credit'] > threshold
            ].tolist())
        return {
            'value': values,
            'exceeds_threshold': values > threshold,
            'threshold': threshold
        }

    def difference(self):
        threshold = self._get_threshold('difference')
        diff = self.current_year_data.sum().sum() - \
            self.previous_year_data.sum().sum()
        return {
            'value': diff,
            'exceeds_threshold': abs(diff) > threshold,
            'threshold': threshold
        }

    def variance(self):
        threshold = self._get_threshold('variance')
        current_variance = self.current_year_data.values.var()
        previous_variance = self.previous_year_data.values.var()
        var_change = (
            (current_variance - previous_variance) / previous_variance * 100
            if previous_variance != 0
            else float('inf')
        )
        return {
            'value': var_change,
            'exceeds_threshold': abs(var_change) > threshold,
            'threshold': threshold
        }

    def ratio(self):
        threshold = self._get_threshold('ratio')
        current_total = self.current_year_data.sum().sum()
        previous_total = self.previous_year_data.sum().sum()
        ratio = (current_total / previous_total
                 if previous_total != 0
                 else float('inf'))
        return {
            'value': ratio,
            'exceeds_threshold': abs(ratio - 1) > threshold,
            'threshold': threshold
        }

    def mean(self):
        threshold = self._get_threshold('mean')
        current_mean = self.current_year_data.mean().mean()
        previous_mean = self.previous_year_data.mean().mean()
        mean_change = (
            (current_mean - previous_mean) / previous_mean * 100
            if previous_mean != 0
            else float('inf')
        )
        return {
            'value': mean_change,
            'exceeds_threshold': abs(mean_change) > threshold,
            'threshold': threshold
        }

    def median(self):
        threshold = self._get_threshold('median')
        current_median = self.current_year_data.median().median()
        previous_median = self.previous_year_data.median().median()
        median_change = (
            (current_median - previous_median) / previous_median * 100
            if previous_median != 0
            else float('inf')
        )
        return {
            'value': median_change,
            'exceeds_threshold': abs(median_change) > threshold,
            'threshold': threshold
        }

    def mode(self):
        threshold = self._get_threshold('mode')
        current_mode = self.current_year_data.mode().iloc[0].mode().iloc[0]
        previous_mode = self.previous_year_data.mode().iloc[0].mode().iloc[0]
        mode_change = (
            (current_mode - previous_mode) / previous_mode * 100
            if previous_mode != 0
            else float('inf')
        )
        return {
            'value': mode_change,
            'exceeds_threshold': abs(mode_change) > threshold,
            'threshold': threshold
        }

    def std_dev(self):
        threshold = self._get_threshold('std_dev')
        current_std_dev = self.current_year_data.values.std()
        previous_std_dev = self.previous_year_data.values.std()
        std_dev_change = (
            (current_std_dev - previous_std_dev) / previous_std_dev * 100
            if previous_std_dev != 0
            else float('inf')
        )
        return {
            'value': std_dev_change,
            'exceeds_threshold': abs(std_dev_change) > threshold,
            'threshold': threshold
        }
