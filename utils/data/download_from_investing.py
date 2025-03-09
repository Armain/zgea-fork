import requests
import time
import re
import json5
import datetime
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from typeguard import typechecked
from typing import Optional, Union

from utils.math import to_float


@typechecked()
def download_from_investing(
        name: str,
        start_date: Optional[Union[str, pd.Timestamp]] = None,
        end_date: Optional[Union[str, pd.Timestamp]] = None,
        category: str = "indices",
):
    if start_date is None:
        start_date = datetime.date.today() - relativedelta(months=1)

    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)

    if end_date is None:
        end_date = datetime.date.today()

    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)

    data_excess_info_pattern = re.compile(r"window.histDataExcessInfo = ({[^}]*})", flags=re.DOTALL)

    base_url = f"https://www.investing.com/{category}/{name}-historical-data"
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36'})
    response = session.get(base_url)
    time.sleep(np.random.uniform(0.5, 1.5))
    assert response.status_code == 200, f"Request was not successful: {response.status_code}:\n{response.text}"

    match = data_excess_info_pattern.search(response.text)
    assert match is not None, f"Cannot find 'histDataExcessInfo' inside response:\n {response.text}"

    data_excess_info_text = match.groups()[0]
    try:
        data_excess_info=json5.loads(data_excess_info_text)
    except:
        assert False, f"Cannot parse data-excess-info text as json: {data_excess_info_text}"

    url = "https://www.investing.com/instruments/HistoricalDataAjax"
    arguments = {
        'curr_id': str(data_excess_info['pairId']).strip(),
        'smlID': str(data_excess_info['smlId']).strip(),
        'header': 'Historical Data',
        'st_date': start_date.strftime("%m/%d/%Y"),
        'end_date': end_date.strftime("%m/%d/%Y"),
        'interval_sec': 'Daily',
        'sort_col': 'date',
        'sort_ord': 'DESC',
        'action': 'historical_data',
    }
    response = session.post(url, data=arguments, headers={
        'POST': '/instruments/HistoricalDataAjax HTTP/3',
        'Host': 'www.investing.com',
        'Accept': 'text/plain, */*; q=0.01',
        'Accept-Language': 'en-US;q=0.7,en;q=0.3',
        'Referer': 'https://www.investing.com/indices/nasdaq-100-tr-historical-data',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.investing.com',
        'Alt-Used': 'www.investing.com',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    })
    time.sleep(np.random.uniform(0.5, 1.5))
    assert response.status_code == 200, f"Request was not successful: {response.status_code}:\n{response.text}"

    html_content = response.content.decode('utf-8')
    assert '<table' in html_content, f"HTML content does not contain any table"

    tables = pd.read_html(html_content, index_col=0)
    for t in tables:
        if 'Open' in t.columns and 'Price' in t.columns:
            data = t['Price']
            data.index = pd.to_datetime(data.index)
            data = data.apply(to_float)
            data.name = name
            return data

    assert f"Cannot find correct table: {[t.columns for t in tables]}"
