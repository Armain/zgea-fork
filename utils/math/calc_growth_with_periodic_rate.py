from typeguard import typechecked
from typing import Optional
import pandas as pd
import numpy as np


@typechecked()
def calc_growth_with_periodic_rate(
        data: pd.Series,
        start_value: float = 100,
        periodic_rate: float = 0,
        rate_interval: Optional[int] = None,
        percent: float = 1
):
    value = start_value
    growth = pd.Series(index=data.index, dtype=np.float64)
    next_rate = rate_interval
    for i in data.index:
        if next_rate is not None:
            next_rate -= 1
            if next_rate <= 0:
                next_rate = rate_interval
                value = value + periodic_rate
        value = value * (1 + (data.loc[i]/percent))
        growth.loc[i] = value
    return growth
