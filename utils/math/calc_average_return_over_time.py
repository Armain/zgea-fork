import pandas as pd
from dateutil.relativedelta import relativedelta
from typeguard import typechecked
from typing import List

from .gmean import gmean


@typechecked()
def calc_average_return_over_time(
        returns: pd.DataFrame,
        average_size: relativedelta,
        step_size: relativedelta,
        assets: List[str],
    ) -> pd.DataFrame:
    returns_over_time = pd.DataFrame()
    i = min(returns.index)

    while True:
        start_index = i
        end_index = start_index + average_size
        i = i + step_size
        if i + average_size > max(returns.index):
            return returns_over_time

        print(start_index)
        for a in assets:
            average_return = gmean(returns.loc[start_index:end_index, a])
            returns_over_time.loc[end_index, a] = average_return
