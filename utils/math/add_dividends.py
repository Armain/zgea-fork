from typeguard import typechecked
import pandas as pd

from .gmean import gmean


@typechecked()
def add_dividends(
        data: pd.Series,
        divs: pd.Series,
        days_in_year: int = 365,
        adjustment_factor: float = 0,
        monthly: bool = False,
):
    data = data.copy()
    for i in divs.index:
        if i in data.index:
            if monthly:
                days = len(data.loc[f"{i.year}-{i.month}"].index)
            else:
                days = days_in_year

            daily_adjustment_factor = gmean(adjustment_factor, days)
            daily_div = gmean(divs[i], days)
            data.loc[f"{i.year}-{i.month}"] += daily_div + daily_adjustment_factor
    return data
