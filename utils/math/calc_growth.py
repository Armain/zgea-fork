from typeguard import typechecked
import pandas as pd
import numpy as np


@typechecked()
def calc_growth(data: pd.Series, start_value: float = 100, percent: float = 1):
    value = start_value
    growth = pd.Series(index=data.index, dtype=np.float64)
    for i in data.index:
        value = value * (1 + (data.loc[i]/percent))
        growth.loc[i] = value
    return growth
