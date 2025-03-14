import pandas as pd
import numpy as np
from typeguard import typechecked
from typing import Tuple


@typechecked()
def calc_max_drawdown(data: pd.DataFrame, progress_output: bool = False) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculates the maximum drawdown of all assets in the dataframe.

    :param data: A dataframe with the growth of all assets.
    :return: Returns a tuple of 3 series: The first one contains for every asset the max. drawdown in percent.
             The second one contains the start-date, when the drawdown started and the third one the end-date.
    """

    max_drawdown = pd.Series(index=data.columns, dtype=np.float64)
    max_value = pd.Series(index=data.columns, dtype=np.float64)
    max_drawdown_start = pd.Series(index=data.columns, dtype=np.float64)
    max_drawdown_last_max_value = pd.Series(index=data.columns, dtype=np.float64)
    max_drawdown_end = pd.Series(index=data.columns, dtype=np.float64)
    last_year = 0

    for i in data.index:
        for a in data.columns:
            if np.isnan(max_value[a]) or data.loc[i, a] > max_value[a]:
                max_value[a] = data.loc[i, a]
                max_drawdown_last_max_value[a] = i

            drawdown = (data.loc[i, a] / max_value[a] - 1) * 100

            if np.isnan(max_drawdown[a]) or drawdown < max_drawdown[a]:
                max_drawdown[a] = drawdown
                max_drawdown_end[a] = i
                max_drawdown_start[a] = max_drawdown_last_max_value[a]

        if progress_output:
            if last_year != i.year:
                last_year = i.year
                print(f" * calc: {i}")

    return max_drawdown, max_drawdown_start, max_drawdown_end