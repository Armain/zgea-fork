#!/usr/bin/env python
# coding: utf-8

# # EMA Buy and Sell Strategy (Shares)

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

p_2x_sp500 = Portfolio(
    {
        '2x_sp500_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_3x_sp500 = Portfolio(
    {
        '3x_sp500_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_ndx100 = Portfolio(
    {
        '1x_ndx100_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_2x_ndx100 = Portfolio(
    {
        '2x_ndx100_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)

p_3x_ndx100 = Portfolio(
    {
        '3x_ndx100_eu': 100.0,
    },
    start_value = 1000,
).backtest(etfs)


# In[6]:


p_details = {}
p = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=100.0, ma=290, ma_asset='1x_sp500_us'),
    },
    start_value = 100,
    detailed_output=False,
    details_memory=p_details,
).backtest(etfs)

print(f"Number of Buys: {len(p_details['asset']['3x_sp500_us']['buys'])}")
print(f"Number of Sells: {len(p_details['asset']['3x_sp500_us']['sells'])}")

draw_growth_chart(
    p_details['chart']
)


# In[7]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x S&P 500")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_sp500_eu": dict(dist=100, ma=ma, ma_asset="1x_sp500_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x S&P500'] = p_3x_sp500.loc[start_date:end_date]
short_names.append("3x S&P500")
portfolios['2x S&P500'] = p_2x_sp500.loc[start_date:end_date]
short_names.append("2x S&P500")
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[8]:


#mas = [50, 40, 70, 80, 60, 210, 90, 220, 200, 330, 340, 380, 270, 260, 390, 40, 370,230, 290, 280, 320, 360, 350, 240, 250, 310, 300]
mas = [210, 220, 200, 330, 340, 380, 270, 260, 390, 370, 230, 290, 280, 320, 360, 350, 240, 250, 310, 300]
sum(mas)/len(mas)


# In[9]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x S&P 500")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_sp500_eu": dict(dist=100, ma=ma, ma_asset="1x_sp500_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x S&P500'] = p_3x_sp500.loc[start_date:end_date]
short_names.append("3x S&P500")
portfolios['2x S&P500'] = p_2x_sp500.loc[start_date:end_date]
short_names.append("2x S&P500")
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[10]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 2x S&P 500")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "2x_sp500_eu": dict(dist=100, ma=ma, ma_asset="1x_sp500_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x S&P500'] = p_3x_sp500.loc[start_date:end_date]
short_names.append("3x S&P500")
portfolios['2x S&P500'] = p_2x_sp500.loc[start_date:end_date]
short_names.append("2x S&P500")
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[11]:


#mas = [50, 60, 40, 70, 80, 210, 90, 220, 200, 420, 110, 430, 340, 330, 370, 320, 380, 280, 390, 400, 270, 260, 280, 230, 360, 350, 300, 310, 240, 250, 410]
mas = [210, 220, 200, 420, 430, 340, 330, 370, 320, 380, 280, 390, 400, 270, 260, 280, 230, 360, 350, 300, 310, 240, 250, 410]
sum(mas)/len(mas)


# In[12]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 2x S&P 500")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "2x_sp500_eu": dict(dist=100, ma=ma, ma_asset="1x_sp500_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x S&P500'] = p_3x_sp500.loc[start_date:end_date]
short_names.append("3x S&P500")
portfolios['2x S&P500'] = p_2x_sp500.loc[start_date:end_date]
short_names.append("2x S&P500")
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ## Nasdaq-100

# In[13]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x Nasdaq-100")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_ndx100_eu": dict(dist=100, ma=ma, ma_asset="1x_ndx100_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x NDX100'] = p_3x_ndx100.loc[start_date:end_date]
short_names.append("3x NDX100")
portfolios['2x NDX100'] = p_2x_ndx100.loc[start_date:end_date]
short_names.append("2x NDX100")
portfolios['NDX100'] = p_ndx100.loc[start_date:end_date]
short_names.append('NDX100')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[14]:


mas = [60, 40, 50, 70, 90, 80, 210, 220, 230, 290, 330, 300, 410, 420, 430, 390, 260, 380, 400, 240, 370, 270, 430, 360, 250, 280, 350]
mas = [210, 220, 230, 290, 330, 300, 410, 420, 430, 390, 260, 380, 400, 240, 370, 270, 430, 360, 250, 280, 350]
sum(mas)/len(mas)


# In[15]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 3x Nasdaq-100")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "3x_ndx100_eu": dict(dist=100, ma=ma, ma_asset="1x_ndx100_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x NDX100'] = p_3x_ndx100.loc[start_date:end_date]
short_names.append("3x NDX100")
portfolios['2x NDX100'] = p_2x_ndx100.loc[start_date:end_date]
short_names.append("2x NDX100")
portfolios['NDX100'] = p_ndx100.loc[start_date:end_date]
short_names.append('NDX100')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[16]:


start_date = '1943'
end_date = '1986'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 2x Nasdaq-100")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "2x_ndx100_eu": dict(dist=100, ma=ma, ma_asset="1x_ndx100_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x NDX100'] = p_3x_ndx100.loc[start_date:end_date]
short_names.append("3x NDX100")
portfolios['2x NDX100'] = p_2x_ndx100.loc[start_date:end_date]
short_names.append("2x NDX100")
portfolios['NDX100'] = p_ndx100.loc[start_date:end_date]
short_names.append('NDX100')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[17]:


mas=[60, 40, 50, 70, 90, 80, 210, 220, 230, 200, 110, 310, 320, 410, 430, 420, 290, 390, 330, 300, 380, 400, 240, 280, 360, 370, 260, 350, 340, 270, 250]
mas=[210, 220, 230, 200, 110, 310, 320, 410, 430, 420, 290, 390, 330, 300, 380, 400, 240, 280, 360, 370, 260, 350, 340, 270, 250]
sum(mas)/len(mas)


# In[18]:


start_date = '1986'
end_date = '2021'
mas = list(range(40,500,10))

short_names = []
portfolios = {}
for ma in mas:
    name = f"MA{ma}"
    print(f"Calculate: {name} for 2x Nasdaq-100")
    short_names.append(name)
    portfolios[name] = MAPortfolio(
        {
            "2x_ndx100_eu": dict(dist=100, ma=ma, ma_asset="1x_ndx100_eu"),
        },
        start_value = 1000,
    ).backtest(etfs).loc[start_date:end_date]
    

portfolios['3x NDX100'] = p_3x_ndx100.loc[start_date:end_date]
short_names.append("3x NDX100")
portfolios['2x NDX100'] = p_2x_ndx100.loc[start_date:end_date]
short_names.append("2x NDX100")
portfolios['NDX100'] = p_ndx100.loc[start_date:end_date]
short_names.append('NDX100')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[ ]:




