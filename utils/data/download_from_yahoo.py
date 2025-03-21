import yfinance
import pandas as pd
from typeguard import typechecked
from typing import Optional

from utils.math import to_float, calc_returns, calc_growth, reindex_and_fill


@typechecked()
def download_from_yahoo(ticker: str, name: Optional[str] = None, adjust=True, dividends=False):
    if name is None:
        name = ticker

    data = yfinance.download(
        [ticker],
        start=None,
        period='max',
        auto_adjust=adjust,
        actions=False,
        progress=False
    )['Close'].apply(to_float)
    data.name = name
    data.index = pd.to_datetime(data.index)
    data = reindex_and_fill(data, min(data.index), max(data.index), freq="D")

    if dividends:
        dividends = yfinance.Ticker(ticker).dividends
        value_percent = calc_returns(data, freq="D")
        for i in dividends.index:
            if i in data.index:
                value_percent[i] += dividends[i]/data[i]

        return calc_growth(value_percent, data.iloc[0])

    return data

