import requests
import io
import pandas as pd
import numpy as np
import time
from typeguard import typechecked
from typing import Optional

from utils.math import to_float


@typechecked()
def download_from_fred(name: str, column_name: Optional[str] = None):
    if column_name is None:
        column_name = name

    url = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={name}'
    session = requests.Session()
    time.sleep(np.random.uniform(0.5, 1.5))
    response = session.get(url)
    assert response.status_code == 200, f"Error when downloading the data. Status-Code: {response.status_code}\n{response.text}"
    with io.StringIO(response.text) as f:
        data = pd.read_csv(f, index_col=0)

    data.index = pd.to_datetime(data.index)
    data = data[column_name].apply(to_float)
    return data
