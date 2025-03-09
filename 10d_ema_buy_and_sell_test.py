#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import pandas.tseries.offsets as pd_offsets
import pickle
import plotly.graph_objects as go
from typing import Dict, Tuple
from dateutil.relativedelta import relativedelta
import itertools


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart, draw_risk_reward_chart, draw_periodic_return
from utils.plots import draw_correlations, compare_portfolios, draw_max_portfolio_drawdowns, draw_min_portfolio_returns
from utils.math import gmean, calc_min_returns, calc_max_drawdown, calc_correlations_over_time, normalize, calc_returns
from utils.math import to_float, calc_growth, normalize_df
from utils.data import cached, read_csv
from utils.portfolio import Portfolio, MAPortfolio


# In[3]:


clean_data_path = Path("clean_data")
cache_path = Path("cached_data")


# In[4]:


input_path = clean_data_path / "etfs.xlsx"
etfs = pd.read_excel(input_path, index_col=0)
etfs.index = pd.to_datetime(etfs.index)
etfs['cash'] = 100.0
etfs


# In[ ]:


details_memory = {}
p_hfea_ma = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55.0, ma=290, ma_asset="1x_sp500_us"),
        '3x_ltt_us': dict(dist=45.0, ma=70, ma_asset="1x_ltt_us"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),
    detailed_output=True,
    details_memory=details_memory,
).backtest(etfs)


# In[ ]:


draw_growth_chart(details_memory['chart'])


# In[ ]:


draw_growth_chart(details_memory['chart'])


# In[ ]:




