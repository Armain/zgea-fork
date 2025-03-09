#!/usr/bin/env python
# coding: utf-8

# # MA200 Buy and Sell Strategy

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

p_gold = Portfolio(
    {
        '1x_gold_eu': 100.0,
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


# In[6]:


details_memory = {}
p_3x_sp500_ma = MAPortfolio(
    {
        "3x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
    details_memory = details_memory
).backtest(etfs)

p_2x_sp500_ma = MAPortfolio(
    {
        "2x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
).backtest(etfs)

p_3x_ndx100_ma = MAPortfolio(
    {
        "3x_ndx100_eu": dict(dist=100, ma=320, ma_asset="1x_ndx100_eu"),
    },
    start_value = 1000,
).backtest(etfs)

p_2x_ndx100_ma = MAPortfolio(
    {
        "2x_ndx100_eu": dict(dist=100, ma=320, ma_asset="1x_ndx100_eu"),
    },
    start_value = 1000,
).backtest(etfs)

p_1x_ltt_ma = MAPortfolio(
    {
        "1x_ltt_eu": dict(dist=100, ma=90, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
).backtest(etfs)

p_3x_ltt_ma = MAPortfolio(
    {
        "3x_ltt_us": dict(dist=100, ma=90, ma_asset="1x_ltt_us"),
    },
    start_value = 1000,
).backtest(etfs)

p_3x_itt_ma = MAPortfolio(
    {
        "3x_itt_eu": dict(dist=100, ma=70, ma_asset="1x_itt_eu"),
    },
    start_value = 1000,
).backtest(etfs)

p_gold_ma = MAPortfolio(
    {
        "1x_gold_eu": dict(dist=100, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
).backtest(etfs)


# In[7]:


len(details_memory['asset']['3x_sp500_eu']['buys']) + len(details_memory['asset']['3x_sp500_eu']['sells'])


# In[8]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['Gold'] = p_gold.loc[start_date:end_date]
short_names.append('Gold')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['3x S&P500 (MA)'] = p_3x_sp500_ma.loc[start_date:end_date]
short_names.append('3x S&P500 (MA)')
portfolios['2x NDX100 (MA)'] = p_2x_ndx100_ma.loc[start_date:end_date]
short_names.append('2x NDX100 (MA)')
portfolios['3x NDX100 (MA)'] = p_3x_ndx100_ma.loc[start_date:end_date]
short_names.append('3x NDX100 (MA)')
portfolios['3x ITT (MA)'] = p_3x_itt_ma.loc[start_date:end_date]
short_names.append('3x ITT (MA)')
portfolios['3x LTT (MA)'] = p_3x_ltt_ma.loc[start_date:end_date]
short_names.append('3x LTT (MA)')
portfolios['1x LTT (MA)'] = p_1x_ltt_ma.loc[start_date:end_date]
short_names.append('1x LTT (MA)')
portfolios['1x Gold (MA)'] = p_gold_ma.loc[start_date:end_date]
short_names.append('1x Gold (MA)')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### Consider Spread

# In[9]:


p_3x_sp500_ma = MAPortfolio(
    {
        "3x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_2x_sp500_ma = MAPortfolio(
    {
        "2x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_3x_ndx100_ma = MAPortfolio(
    {
        "3x_ndx100_eu": dict(dist=100, ma=310, ma_asset="1x_ndx100_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_2x_ndx100_ma = MAPortfolio(
    {
        "2x_ndx100_eu": dict(dist=100, ma=310, ma_asset="1x_ndx100_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_1x_ltt_ma = MAPortfolio(
    {
        "1x_ltt_eu": dict(dist=100, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_3x_ltt_ma = MAPortfolio(
    {
        "3x_ltt_us": dict(dist=100, ma=70, ma_asset="1x_ltt_us"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_3x_itt_ma = MAPortfolio(
    {
        "3x_itt_eu": dict(dist=100, ma=70, ma_asset="1x_itt_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)

p_gold_ma = MAPortfolio(
    {
        "1x_gold_eu": dict(dist=100, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    spread = 0.002,
).backtest(etfs)


# In[10]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')
portfolios['LTT'] = p_ltt.loc[start_date:end_date]
short_names.append('LTT')
portfolios['Gold'] = p_gold.loc[start_date:end_date]
short_names.append('Gold')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['3x S&P500 (MA)'] = p_3x_sp500_ma.loc[start_date:end_date]
short_names.append('3x S&P500 (MA)')
portfolios['2x NDX100 (MA)'] = p_2x_ndx100_ma.loc[start_date:end_date]
short_names.append('2x NDX100 (MA)')
portfolios['3x NDX100 (MA)'] = p_3x_ndx100_ma.loc[start_date:end_date]
short_names.append('3x NDX100 (MA)')
portfolios['3x ITT (MA)'] = p_3x_itt_ma.loc[start_date:end_date]
short_names.append('3x ITT (MA)')
portfolios['3x LTT (MA)'] = p_3x_ltt_ma.loc[start_date:end_date]
short_names.append('3x LTT (MA)')
portfolios['1x LTT (MA)'] = p_1x_ltt_ma.loc[start_date:end_date]
short_names.append('1x LTT (MA)')
portfolios['1x Gold (MA)'] = p_gold_ma.loc[start_date:end_date]
short_names.append('1x Gold (MA)')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### 50% Portfolios

# In[11]:


p_base = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50),
        '1x_ltt_eu': dict(dist=50),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_g = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50),
        '1x_ltt_eu': dict(dist=37.5),
        '1x_gold_eu': dict(dist=12.5),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_n = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=42.5),
        '2x_ndx100_eu': dict(dist=7.5),
        '1x_ltt_eu': dict(dist=50),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),  
    spread = 0.002,
).backtest(etfs)

p_ng = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=42.5),
        '2x_ndx100_eu': dict(dist=7.5),
        '1x_ltt_eu': dict(dist=37.5),
        '1x_gold_eu': dict(dist=12.5),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=50, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),    
).backtest(etfs)

p_g_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=37.5, ma=130, ma_asset="1x_ltt_eu"),
        '1x_gold_eu': dict(dist=12.5, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
).backtest(etfs)

p_n_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=42.5, ma=290, ma_asset="1x_sp500_eu"),
        '2x_ndx100_eu': dict(dist=7.5, ma=310, ma_asset="1x_ndx100_eu"),
        '1x_ltt_eu': dict(dist=50, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
).backtest(etfs)

p_ng_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=42.5, ma=290, ma_asset="1x_sp500_eu"),
        '2x_ndx100_eu': dict(dist=7.5, ma=310, ma_asset="1x_ndx100_eu"),
        '1x_ltt_eu': dict(dist=37.5, ma=130, ma_asset="1x_ltt_eu"),
        '1x_gold_eu': dict(dist=12.5, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
).backtest(etfs)    


# In[12]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['50%'] = p_base.loc[start_date:end_date]
short_names.append('50%')
portfolios['50%+G'] = p_g.loc[start_date:end_date]
short_names.append('50%+G')
portfolios['50%+N'] = p_n.loc[start_date:end_date]
short_names.append('50%+N')
portfolios['50%+NG'] = p_ng.loc[start_date:end_date]
short_names.append('50%+NG')

portfolios['50%+MA'] = p_base_ma.loc[start_date:end_date]
short_names.append('50%+MA')
portfolios['50%+G+MA'] = p_g_ma.loc[start_date:end_date]
short_names.append('50%+G+MA')
portfolios['50%+N+MA'] = p_n_ma.loc[start_date:end_date]
short_names.append('50%+N+MA')
portfolios['50%+NG+MA'] = p_ng_ma.loc[start_date:end_date]
short_names.append('50%+NG+MA')

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### 65% Portfolio

# In[13]:


p_base = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=65),
        '1x_ltt_eu': dict(dist=35),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_g = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=65),
        '1x_ltt_eu': dict(dist=26.25),
        '1x_gold_eu': dict(dist=8.75),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)

p_n = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=55.25),
        '2x_ndx100_eu': dict(dist=9.75),
        '1x_ltt_eu': dict(dist=35),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),  
    spread = 0.002,
).backtest(etfs)

#p_ng = MAPortfolio(
#    {
#        '2x_sp500_eu': dict(dist=42.5),
#        '2x_ndx100_eu': dict(dist=7.5),
#        '1x_ltt_eu': dict(dist=37.5),
#        '1x_gold_eu': dict(dist=12.5),
#    },
#    start_value = 1000,
#    rebalancing = relativedelta(months=3),
#    rebalancing_offset = relativedelta(days=-8), 
#    spread = 0.002,
#).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=65, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=35, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),   
    spread = 0.002,
).backtest(etfs)

p_g_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=65, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=26.25, ma=130, ma_asset="1x_ltt_eu"),
        '1x_gold_eu': dict(dist=8.75, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),  
    spread = 0.002,
).backtest(etfs)

p_n_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=55.25, ma=290, ma_asset="1x_sp500_eu"),
        '2x_ndx100_eu': dict(dist=9.75, ma=310, ma_asset="1x_ndx100_eu"),
        '1x_ltt_eu': dict(dist=35, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

#p_ng_ma = MAPortfolio(
#    {
#        '2x_sp500_eu': dict(dist=42.5, ma=290, ma_asset="1x_sp500_eu"),
#        '2x_ndx100_eu': dict(dist=7.5, ma=310, ma_asset="1x_ndx100_eu"),
#        '1x_ltt_eu': dict(dist=37.5, ma=130, ma_asset="1x_ltt_eu"),
#        '1x_gold_eu': dict(dist=12.5, ma=400, ma_asset="1x_gold_eu"),
#    },
#    start_value = 1000,
#    rebalancing = relativedelta(months=3),
#    rebalancing_offset = relativedelta(days=-8),  
#    spread = 0.002,
#).backtest(etfs)   


# In[14]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['65%'] = p_base.loc[start_date:end_date]
short_names.append('65%')
portfolios['65%+G'] = p_g.loc[start_date:end_date]
short_names.append('65%+G')
portfolios['65%+N'] = p_n.loc[start_date:end_date]
short_names.append('65%+N')
#portfolios['50%+NG'] = p_ng.loc[start_date:end_date]
#short_names.append('65%+NG')

portfolios['65%+MA'] = p_base_ma.loc[start_date:end_date]
short_names.append('65%+MA')
portfolios['65%+G+MA'] = p_g_ma.loc[start_date:end_date]
short_names.append('65%+G+MA')
portfolios['65%+N+MA'] = p_n_ma.loc[start_date:end_date]
short_names.append('65%+N+MA')
#portfolios['65%+NG+MA'] = p_ng_ma.loc[start_date:end_date]
#short_names.append('65%+NG+MA')

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### 80% Portfolio

# In[15]:


p_base = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80),
        '1x_ltt_eu': dict(dist=20),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)

p_g = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80),
        '1x_ltt_eu': dict(dist=15),
        '1x_gold_eu': dict(dist=5),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)

p_n = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=68),
        '2x_ndx100_eu': dict(dist=12),
        '1x_ltt_eu': dict(dist=20),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
).backtest(etfs)

p_ng = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=68),
        '2x_ndx100_eu': dict(dist=12),
        '1x_ltt_eu': dict(dist=15),
        '1x_gold_eu': dict(dist=5),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=20, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),    
    spread = 0.002,
).backtest(etfs)

p_g_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=15, ma=130, ma_asset="1x_ltt_eu"),
        '1x_gold_eu': dict(dist=5, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_n_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=68, ma=290, ma_asset="1x_sp500_eu"),
        '2x_ndx100_eu': dict(dist=12, ma=310, ma_asset="1x_ndx100_eu"),
        '1x_ltt_eu': dict(dist=20, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_ng_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=68, ma=290, ma_asset="1x_sp500_eu"),
        '2x_ndx100_eu': dict(dist=12, ma=310, ma_asset="1x_ndx100_eu"),
        '1x_ltt_eu': dict(dist=15, ma=130, ma_asset="1x_ltt_eu"),
        '1x_gold_eu': dict(dist=5, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)   


# In[16]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['80%'] = p_base.loc[start_date:end_date]
short_names.append('80%')
portfolios['80%+G'] = p_g.loc[start_date:end_date]
short_names.append('80%+G')
portfolios['80%+N'] = p_n.loc[start_date:end_date]
short_names.append('80%+N')
portfolios['80%+NG'] = p_ng.loc[start_date:end_date]
short_names.append('80%+NG')

portfolios['80%+MA'] = p_base_ma.loc[start_date:end_date]
short_names.append('80%+MA')
portfolios['80%+G+MA'] = p_g_ma.loc[start_date:end_date]
short_names.append('80%+G+MA')
portfolios['80%+N+MA'] = p_n_ma.loc[start_date:end_date]
short_names.append('80%+N+MA')
portfolios['80%+NG+MA'] = p_ng_ma.loc[start_date:end_date]
short_names.append('80%+NG+MA')

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### 65% (3x) Portfolio

# In[17]:


p_base = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65),
        '3x_itt_eu': dict(dist=35),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_g = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65),
        '3x_itt_eu': dict(dist=26.25),
        '1x_gold_eu': dict(dist=8.75),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_n = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=55.25),
        '3x_ndx100_eu': dict(dist=9.75),
        '3x_itt_eu': dict(dist=35),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

#p_ng = MAPortfolio(
#    {
#        '2x_sp500_eu': dict(dist=68),
#        '2x_ndx100_eu': dict(dist=12),
#        '1x_ltt_eu': dict(dist=15),
#        '1x_gold_eu': dict(dist=5),
#    },
#    start_value = 1000,
#    rebalancing = relativedelta(months=3),
#    rebalancing_offset = relativedelta(days=-8),    
#    spread = 0.002,
#).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65, ma=290, ma_asset="1x_sp500_eu"),
        '3x_itt_eu': dict(dist=35, ma=70, ma_asset="1x_itt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),    
    spread = 0.002,
).backtest(etfs)

p_g_ma = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65, ma=290, ma_asset="1x_sp500_eu"),
        '3x_itt_eu': dict(dist=26.25, ma=70, ma_asset="1x_itt_eu"),
        '1x_gold_eu': dict(dist=8.75, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_n_ma = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=55.25, ma=290, ma_asset="1x_sp500_eu"),
        '3x_ndx100_eu': dict(dist=9.75, ma=310, ma_asset="1x_ndx100_eu"),
        '3x_itt_eu': dict(dist=35, ma=70, ma_asset="1x_itt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

#p_ng_ma = MAPortfolio(
#    {
#        '2x_sp500_eu': dict(dist=68, ma=290, ma_asset="1x_sp500_eu"),
#        '2x_ndx100_eu': dict(dist=12, ma=310, ma_asset="1x_ndx100_eu"),
#        '1x_ltt_eu': dict(dist=15, ma=130, ma_asset="1x_ltt_eu"),
#        '1x_gold_eu': dict(dist=5, ma=400, ma_asset="1x_gold_eu"),
#    },
#    start_value = 1000,
#    rebalancing = relativedelta(months=3),
#    rebalancing_offset = relativedelta(days=-8),    
#    spread = 0.002,
#).backtest(etfs)   


# In[18]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['65% (3x)'] = p_base.loc[start_date:end_date]
short_names.append('65% (3x)')
portfolios['65%+G (3x)'] = p_g.loc[start_date:end_date]
short_names.append('65%+G (3x)')
portfolios['65%+N (3x)'] = p_n.loc[start_date:end_date]
short_names.append('65%+N (3x)')
#portfolios['80%+NG'] = p_ng.loc[start_date:end_date]
#short_names.append('80%+NG')

portfolios['65%+MA (3x)'] = p_base_ma.loc[start_date:end_date]
short_names.append('65%+MA (3x)')
portfolios['65%+G+MA (3x)'] = p_g_ma.loc[start_date:end_date]
short_names.append('65%+G+MA (3x)')
portfolios['65%+N+MA (3x)'] = p_n_ma.loc[start_date:end_date]
short_names.append('65%+N+MA (3x)')
#portfolios['80%+NG+MA'] = p_ng_ma.loc[start_date:end_date]
#short_names.append('80%+NG+MA')

portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ### HFEA Portfolio

# In[19]:


p_base = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55),
        '3x_ltt_us': dict(dist=45),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
).backtest(etfs)

p_g = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55),
        '3x_ltt_us': dict(dist=33.75),
        '1x_gold_eu': dict(dist=11.25),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)

p_n = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=41.25),
        '3x_ndx100_us': dict(dist=13.75),
        '3x_ltt_us': dict(dist=45),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
).backtest(etfs)

p_ng = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=41.25),
        '3x_ndx100_us': dict(dist=13.75),
        '3x_ltt_us': dict(dist=38.25),
        '1x_gold_eu': dict(dist=6.75),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),  
    spread = 0.002,
).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55, ma=290, ma_asset="1x_sp500_us"),
        '3x_ltt_us': dict(dist=45, ma=130, ma_asset="1x_ltt_us"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),    
    spread = 0.002,
).backtest(etfs)

p_g_ma = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55, ma=290, ma_asset="1x_sp500_us"),
        '3x_ltt_us': dict(dist=33.75, ma=130, ma_asset="1x_ltt_us"),
        '1x_gold_eu': dict(dist=11.25, ma=400, ma_asset="1x_gold_us"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)

p_n_ma = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=41.25, ma=290, ma_asset="1x_sp500_us"),
        '3x_ndx100_us': dict(dist=13.75, ma=310, ma_asset="1x_ndx100_us"),
        '3x_ltt_us': dict(dist=45, ma=130, ma_asset="1x_ltt_us"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
).backtest(etfs)

p_ng_ma = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=41.25, ma=290, ma_asset="1x_sp500_us"),
        '3x_ndx100_us': dict(dist=13.75, ma=310, ma_asset="1x_ndx100_us"),
        '3x_ltt_us': dict(dist=38.25, ma=130, ma_asset="1x_ltt_us"),
        '1x_gold_eu': dict(dist=6.75, ma=400, ma_asset="1x_gold_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
).backtest(etfs)   


# In[20]:


start_date = '1944'
end_date = '2021'
portfolios = {}
short_names = []

portfolios['HFEA'] = p_base.loc[start_date:end_date]
short_names.append('HFEA')
portfolios['HFEA+G'] = p_g.loc[start_date:end_date]
short_names.append('HFEA+G')
portfolios['HFEA+N'] = p_n.loc[start_date:end_date]
short_names.append('HFEA+N')
portfolios['HFEA+NG'] = p_ng.loc[start_date:end_date]
short_names.append('HFEA+NG')

portfolios['HFEA+MA'] = p_base_ma.loc[start_date:end_date]
short_names.append('HFEA+MA')
portfolios['HFEA+G+MA'] = p_g_ma.loc[start_date:end_date]
short_names.append('HFEA+G+MA')
portfolios['HFEA+N+MA'] = p_n_ma.loc[start_date:end_date]
short_names.append('HFEA+N+MA')
portfolios['HFEA+NG+MA'] = p_ng_ma.loc[start_date:end_date]
short_names.append('HFEA+NG+MA')

#portfolios['HFEA'] = p_hfea.loc[start_date:end_date]
#short_names.append('HFEA')
portfolios['S&P500'] = p_sp500.loc[start_date:end_date]
short_names.append('S&P500')
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma.loc[start_date:end_date]
short_names.append('2x S&P500 (MA)')
portfolios['3x S&P500 (MA)'] = p_3x_sp500_ma.loc[start_date:end_date]
short_names.append('3x S&P500 (MA)')
portfolios['P'] = p_pari.loc[start_date:end_date]
short_names.append('P')

for v in portfolios.values():
    v = normalize_df(v, start_value = 1000)

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[ ]:




