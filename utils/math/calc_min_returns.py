import pandas as pd
import numpy as np
from typeguard import typechecked
from dateutil.relativedelta import relativedelta
from typing import Tuple, List


@typechecked()
def calc_min_returns(data: pd.DataFrame, years: List[int], progress_output: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculates the minimum return of all assets in the dataframe.
    This is calculated, by iterating over the dates and calculating the return after a number of years
    (1 year, 2 years, 3 years). It remembers always this investing date and the return which is the
    minimum for a given numbers of years (worst timing investiment).

    :param data: A dataframe with the asset growth.
    :param years: A list of years to hold the investment.
    :return: Returns a tuple of two dataframes: The first one contains the minimum return in percent for
             each asset and year and the second one the investment date.
    """

    min_returns = pd.DataFrame(index=years, columns=data.columns)
    min_returns_date = pd.DataFrame(index=years, columns=data.columns)

    last_year = 0
    last_date = max(data.index)
    start_date = min(data.index)
    for i in data.index:
        for y in years:
            start_date = i
            end_date = i + relativedelta(years=y)
            if end_date <= last_date:
                ret = (data.loc[end_date, :] / data.loc[start_date, :] - 1) * 100
                for a in data.columns:
                    if np.isnan(min_returns.loc[y, a]) or ret[a] < min_returns.loc[y, a]:
                        min_returns.loc[y, a] = ret[a]
                        min_returns_date.loc[y, a] = start_date

        if progress_output:
            if last_year != start_date.year:
                last_year = start_date.year
                print(f" * calc: {start_date}")

    return min_returns, min_returns_date
