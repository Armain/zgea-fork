import pandas as pd
import numpy as np
from typeguard import typechecked
from typing import Union


@typechecked()
def calc_returns(data: Union[pd.DataFrame, pd.Series], freq="D"):
    data = data.pct_change(1, freq=freq)
    if isinstance(data, pd.DataFrame):
        if all(np.isnan(data.iloc[0])):
            data.iloc[0] = 0
    elif isinstance(data, pd.Series):
        if np.isnan(data.iloc[0]):
            data.iloc[0] = 0
    return data.dropna()
