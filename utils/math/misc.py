from typeguard import typechecked
from typing import Optional
import pandas as pd


def to_float(value):
    value = str(value)
    try:
        value = str(value).replace(",", "")
        return float(value)

    except:
        return None


@typechecked
def normalize(values: pd.Series, reference: Optional[pd.Series] = None, start_value: Optional[float] = None):
    assert (reference is not None) or (start_value is not None), \
        "You must either specify a reference time-series or a start value"

    if reference is not None:
        first_common_date = max([min(values.index), min(reference.index)])
        return (values / values.loc[first_common_date]) * reference.loc[first_common_date]

    if start_value is not None:
        first_common_date = min(values.index)
        return (values / values.loc[first_common_date]) * start_value


@typechecked
def normalize_df(values: pd.DataFrame, reference: Optional[pd.Series] = None, start_value: Optional[float] = None):
    assert (reference is not None) or (start_value is not None), \
        "You must either specify a reference time-series or a start value"

    if reference is not None:
        first_common_date = max([min(values.index), min(reference.index)])
        return (values / values.loc[first_common_date, :]) * reference.loc[first_common_date]

    if start_value is not None:
        first_common_date = min(values.index)
        return (values / values.loc[first_common_date, :]) * start_value
