import pandas as pd
from typing import Union
from typeguard import typechecked


@typechecked()
def reindex_and_fill(
        data: Union[pd.DataFrame, pd.Series],
        first_date: pd.Timestamp,
        last_date: pd.Timestamp,
        freq: str
):
    date_range = pd.date_range(first_date, last_date, freq=freq)
    new_data = data.reindex(date_range)
    new_data = new_data.ffill()
    new_data = new_data.bfill() # if for coincidence a data point is directly missing at the beginning
    return new_data


@typechecked()
def reindex_and_interpolate(
        data: Union[pd.DataFrame, pd.Series],
        first_date: pd.Timestamp,
        last_date: pd.Timestamp,
        freq: str
):
    date_range = pd.date_range(first_date, last_date, freq=freq)
    new_data = data.reindex(date_range)
    new_data = new_data.interpolate(axis=0)
    return new_data
