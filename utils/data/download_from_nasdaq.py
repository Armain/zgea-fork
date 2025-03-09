import pandas as pd
import quandl
import yaml
from pathlib import Path
from typeguard import typechecked

from utils.math import to_float


@typechecked()
def download_from_nasdaq(name: str, column_name: str, api_key_path: Path = Path(".")):
    api_key_path_file = api_key_path / "nasdaq_api.secret.yaml"
    assert api_key_path_file.exists(), f"File '{api_key_path_file.absolute()}' does not exist. Please add this file as yaml file with the content: \"key: '<your-nasdaq-api-key>'\""
    with api_key_path_file.open("r") as f:
        api_key = yaml.safe_load(f)
    quandl.ApiConfig.api_key = api_key['key']

    data = quandl.get(name)
    data.index = pd.to_datetime(data.index)
    data = data[column_name].apply(to_float)
    data.name = name
    return data.dropna()
