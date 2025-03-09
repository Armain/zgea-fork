import pandas as pd
import numpy as np
from typeguard import typechecked


@typechecked()
def merge_series(data1: pd.Series, data2: pd.Series) -> pd.Series:
    combined = pd.Series(
        index = pd.date_range(
            min(min(data1.index), min(data2.index)),
            max(max(data1.index), max(data2.index)),
            freq="D",
        ),
        dtype=np.float64,
    )
    if max(data1.index) > max(data2.index):
        first = data2
        second = data1
    else:
        first = data1
        second = data2

    combined.loc[min(first.index):max(first.index)] = first
    combined.loc[min(second.index):max(second.index)] = second

    return combined
