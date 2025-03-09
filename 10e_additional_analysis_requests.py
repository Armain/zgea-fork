#!/usr/bin/env python
# coding: utf-8

# # Mixed 2x S&P 500 + 3x Nasdaq Portfolios

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
from utils.portfolio import Portfolio


# In[3]:


clean_data_path = Path("clean_data")
cache_path = Path("cached_data")


# In[4]:


input_path = clean_data_path / "etfs.xlsx"
etfs = pd.read_excel(input_path, index_col=0)
etfs.index = pd.to_datetime(etfs.index)
etfs['cash'] = 100.0
etfs


# In[5]:


p_sp500 = Portfolio(
    {
        '1x_sp500_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_hfea = Portfolio(
    {
        '3x_sp500_us': 55.0,
        '3x_ltt_us': 45.0,
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),
).backtest(etfs)

p_pari = Portfolio(
    {
        '1x_sp500_eu': 60.0,
        '1x_ltt_eu': 40.0,
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),
).backtest(etfs)


# ## 50% Portfolio

# In[6]:


allocations = list(range(0,101,5))
growth_allocation = 50

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-p))/100,
            "3x_ndx100_eu": (growth_allocation*p)/100,
            "1x_ltt_eu": 100-growth_allocation,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ## 65% Portfolio

# In[7]:


allocations = list(range(0,101,5))
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-p))/100,
            "3x_ndx100_eu": (growth_allocation*p)/100,
            "1x_ltt_eu": 100-growth_allocation,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# ## 80% Portfolio

# In[8]:


allocations = list(range(0,101,5))
growth_allocation = 80

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-p))/100,
            "3x_ndx100_eu": (growth_allocation*p)/100,
            "1x_ltt_eu": 100-growth_allocation,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# In[ ]:




