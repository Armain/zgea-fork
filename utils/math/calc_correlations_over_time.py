import pandas as pd
from dateutil.relativedelta import relativedelta
from typeguard import typechecked
from typing import List
from itertools import combinations


@typechecked()
def calc_correlations_over_time(
        returns: pd.DataFrame,
        correlation_size: relativedelta,
        step_size: relativedelta,
        assets: List[str],
    ) -> pd.DataFrame:
    correlations_over_time = pd.DataFrame()
    i = min(returns.index)

    while True:
        start_index = i
        end_index = start_index + correlation_size
        i = i + step_size
        if i + correlation_size > max(returns.index):
            return correlations_over_time

        print(start_index)
        correlation_window = returns.loc[start_index:end_index, :][assets]
        correlation_window = correlation_window.corr()

        for c in combinations(assets, 2):
            correlations_over_time.loc[end_index, f'{c[0]} vs. {c[1]}'] = correlation_window.loc[c[0], c[1]]
