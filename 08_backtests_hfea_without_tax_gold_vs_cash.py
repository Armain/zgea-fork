#!/usr/bin/env python
# coding: utf-8

# # Backtest of HFEA without Tax (Compare Gold vs. Cash)

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

p_hfea_m = Portfolio(
    {
        '3x_sp500_us': 55.0,
        '1x_ltt_us': 45.0,
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


# ## Gold
# 
# ### 50% 2x S&P 500 

# In[6]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 50

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# An allocation of 20%-40% to Gold inside the Hedge part seems to perform better and has lower risk compared to LTT only. 

# ### 65% 2x S&P 500

# In[7]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# Here Gold seems to increase slightly the performance, but also the risk. So maximum 20% would be acceptable. 

# ### 80% 2x S&P 500

# In[8]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 80

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# For such a high allocation to S&P 500, Gold is reducing the risk, while not further increasing the performance. So 30%-20% seems to be a good value, without losing performance. 

# ### 65% 3x S&P 500

# In[9]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_eu": growth_allocation,
            "3x_itt_eu": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Gold is slightly increasing the performance, but also risk. So maximum 20% is acceptable. 

# ### HFEA

# In[10]:


allocations = [
    10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 55

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": growth_allocation,
            "3x_ltt_us": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# Gold is massivly reducing the risk. Up to 50% seems to be a good choice. 

# ### HFEA-

# In[11]:


allocations = [
    10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 55

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": growth_allocation,
            "1x_ltt_us": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_eu": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# ## Cash
# 
# ### 50% 2x S&P 500

# In[12]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 50

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Every amount of cash is reducing the performance. Until 20-30% it gives at least some reduced risk.

# ## 65% 2x S&P 500

# In[13]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Cash is just reducing the performance and even increasing the risk. 

# ### 80% 2x S&P 500

# In[14]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 80

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": growth_allocation,
            "1x_ltt_eu": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# We see the same effect here. 

# ### 65% 3x S&P 500

# In[15]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_eu": growth_allocation,
            "3x_itt_eu": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# ### HFEA

# In[16]:


allocations = [
    10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 55

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": growth_allocation,
            "3x_ltt_us": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Having Cash together with standard HFEA is drastically reducing the risk, but also the returns. So Gold is much better. 

# ### HFEA-

# In[17]:


allocations = [
    10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 55

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": growth_allocation,
            "1x_ltt_us": ((100-growth_allocation)*(100-p))/100,
            "cash": ((100-growth_allocation)*(p))/100,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# ## Summary

# In[25]:


allocations = [
    ("2x S&P 500",  ('2x_sp500_eu', 100), ('1x_ltt_eu', 0), ('1x_gold_eu', 0)),
    ("50%",         ('2x_sp500_eu', 50), ('1x_ltt_eu', 50), ('1x_gold_eu', 0)),
    ("50%+G",       ('2x_sp500_eu', 50), ('1x_ltt_eu', 37.5), ('1x_gold_eu', 12.5)),
    ("65%",         ('2x_sp500_eu', 65), ('1x_ltt_eu', 35), ('1x_gold_eu', 0)),
    ("65%+G",       ('2x_sp500_eu', 65), ('1x_ltt_eu', 26.25), ('1x_gold_eu', 8.75)),
    ("80%",         ('2x_sp500_eu', 80), ('1x_ltt_eu', 20), ('1x_gold_eu', 0)),
    ("80%+G",       ('2x_sp500_eu', 80), ('1x_ltt_eu', 15), ('1x_gold_eu', 5)),
    ("65% (3x)",    ('3x_sp500_eu', 65), ('3x_itt_eu', 35), ('1x_gold_eu', 0)),
    ("65%+G (3x)",  ('3x_sp500_eu', 65), ('3x_itt_eu', 26.25), ('1x_gold_eu', 8.75)),
    ("HFEA",        ('3x_sp500_us', 55), ('3x_ltt_us', 45), ('1x_gold_us', 0)),
    ("HFEA+G",      ('3x_sp500_us', 55), ('3x_ltt_us', 33.75), ('1x_gold_us', 11.25)),
    ("HFEA-",       ('3x_sp500_us', 55), ('1x_ltt_us', 45), ('1x_gold_us', 0)),
    ("HFEA-+G",     ('3x_sp500_us', 55), ('1x_ltt_us', 33.75), ('1x_gold_us', 11.25)),
]


short_names = []
portfolios = {}
for a in allocations:
    name = a[0]
    print(f"Calculate: {name}")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            a[1][0]: a[1][1],
            a[2][0]: a[2][1],
            a[3][0]: a[3][1],
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[22]:


draw_max_portfolio_drawdowns(portfolios)


# In[23]:


draw_min_portfolio_returns(portfolios) 


# ## Additional Analysis

# In[28]:


allocations = [
    0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100
]
growth_allocation = 65

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Cash")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": ((growth_allocation)*(100-p))/100,
            "3x_sp500_eu": ((growth_allocation)*(p))/100,
            "3x_itt_eu": 100-growth_allocation,
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['HFEA'] = p_hfea
short_names.append("HFEA")
portfolios['S&P500'] = p_sp500
short_names.append('S&P500')
portfolios['HFEA-'] = p_hfea_m
short_names.append("HFEA-")
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[ ]:




