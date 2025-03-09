import pandas as pd
from pathlib import Path
from typeguard import typechecked
from typing import Optional, Callable, Any

from utils.math import to_float


@typechecked()
def read_csv(
        file_path: Path,
        column_name: str,
        name: Optional[str] = None,
        sep: str = ",",
        index_mapping: Callable[[pd.RangeIndex], pd.RangeIndex] = pd.to_datetime,
        value_mapping: Callable[[Any], float] = to_float
):
    if name is None:
        name = file_path.stem

    data = pd.read_csv(file_path, sep=sep, index_col=0)
    data.index = index_mapping(data.index)
    assert column_name in data.columns, f"Column '{column_name}' is not in {list(data.columns)}"
    data = data[column_name].apply(value_mapping)
    data.name = name
    return data
