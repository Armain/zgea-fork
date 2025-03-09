#!/usr/bin/env python
# coding: utf-8

# # EMA Buy and Sell Strategy (Bonds)

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


# In[5]:


p_sp500 = Portfolio(
    {
        '1x_sp500_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_ltt = Portfolio(
    {
        '1x_ltt_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_3x_ltt = Portfolio(
    {
        '3x_ltt_us': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_3x_itt = Portfolio(
    {
        '3x_itt_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_gold = Portfolio(
    {
        '1x_gold_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)


# In[6]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 1x LTT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "1x_ltt_eu": dict(dist=100, ma=ma, ma_asset="1x_ltt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[18]:


mas=[60, 70, 90, 80, 100, 110, 120, 220, 190, 200, 180, 210]
mas=[60, 70, 90, 80, 100, 110, 120]
sum(mas)/len(mas)


# In[8]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 1x LTT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "1x_ltt_eu": dict(dist=100, ma=ma, ma_asset="1x_ltt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[9]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x LTT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_ltt_us": dict(dist=100, ma=ma, ma_asset="1x_ltt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['3x LTT'] = p_3x_ltt.loc[start_date:end_date]
short_names.append('3x LTT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[10]:


mas=[60, 70, 80, 90]
sum(mas)/len(mas)


# In[11]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x LTT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_ltt_us": dict(dist=100, ma=ma, ma_asset="1x_ltt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['3x LTT'] = p_3x_ltt.loc[start_date:end_date]
short_names.append('3x LTT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[12]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x ITT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_itt_eu": dict(dist=100, ma=ma, ma_asset="1x_itt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['3x LTT'] = p_3x_ltt.loc[start_date:end_date]
short_names.append('3x LTT')
portfolios['3x ITT'] = p_3x_itt.loc[start_date:end_date]
short_names.append('3x ITT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[13]:


mas=[40, 50, 60, 70, 80, 90, 100]
sum(mas)/len(mas)


# In[14]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x ITT")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_itt_eu": dict(dist=100, ma=ma, ma_asset="1x_itt_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['3x LTT'] = p_3x_ltt.loc[start_date:end_date]
short_names.append('3x LTT')
portfolios['3x ITT'] = p_3x_itt.loc[start_date:end_date]
short_names.append('3x ITT')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# # EMA Buy and Sell Strategy (Gold)

# In[15]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 1x Gold")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "1x_gold_eu": dict(dist=100, ma=ma, ma_asset="1x_gold_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['Gold'] = p_gold.loc[start_date:end_date]
short_names.append('Gold')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[16]:


mas = [420, 390, 450, 440, 430, 470, 410, 490, 480, 330, 350, 340, 320, 310]
sum(mas)/len(mas)


# In[17]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 1x Gold")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "1x_gold_eu": dict(dist=100, ma=ma, ma_asset="1x_gold_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['Gold'] = p_gold.loc[start_date:end_date]
short_names.append('Gold')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[ ]:




