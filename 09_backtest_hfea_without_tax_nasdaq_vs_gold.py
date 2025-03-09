#!/usr/bin/env python
# coding: utf-8

# # Backtest of HFEA strategy with Nasdaq and Gold

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


# ## Use Nasdaq-100 instead of S&P 500
# 
# ### 50% Growth Allocation

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
            "2x_ndx100_eu": (growth_allocation*p)/100,
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


# Is seems that 20% Nasdaq-100 allocation gives more returns without increasing the risk. 

# ### 65% Growth Allocation

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
            "2x_ndx100_eu": (growth_allocation*p)/100,
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


# For 65% allocation, a portion of 10% for Nasdaq-100 in the growth part seems to be a good fit.

# ### 80% Growth Allocation

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
            "2x_ndx100_eu": (growth_allocation*p)/100,
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


# By adding Nasdaq-100 to the 80% growth allocation protfolio, we can increase the performance, but also the risk. So we decide to not take a Nasdaq-100 Part here. 

# ### 65% Growth Allocation with 3x Leveraged ETNs

# In[9]:


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
            "3x_sp500_eu": (growth_allocation*(100-p))/100,
            "3x_ndx100_eu": (growth_allocation*p)/100,
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
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
)


# Also here, we see an increase of risk together with the increase of performance. 

# ### HFEA

# In[10]:


allocations = list(range(0,101,5))
growth_allocation = 55

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": (growth_allocation*(100-p))/100,
            "3x_ndx100_us": (growth_allocation*p)/100,
            "3x_ltt_us": 100-growth_allocation,
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


# It seems that an allocation of 45% Nasdaq-100 is increasing the performance a lot, while not further increasing the risk. 

# ## Nasdaq in Combination with Gold
# 
# ### 50% Growth Allocation (with 15% Nasdaq-100)

# In[11]:


allocations = list(range(0,101,5))
growth_allocation = 50
ndx_allocation = 15

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold with Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-ndx_allocation))/100,
            "2x_ndx100_eu": (growth_allocation*ndx_allocation)/100,
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
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Adding Gold to this portfolio is just increasing the risk. 

# ### 65% Growth Allocation (with 15% Nasdaq-100)

# In[12]:


allocations = list(range(0,101,5))
growth_allocation = 65
ndx_allocation = 15

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold with Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-ndx_allocation))/100,
            "2x_ndx100_eu": (growth_allocation*ndx_allocation)/100,
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
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Giving any Gold to this portfolio is just increasing the risk. 

# ### 80% Growth without Nasdaq

# In[ ]:


allocations = list(range(0,101,5))
growth_allocation = 80
ndx_allocation = 15

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold with Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "2x_sp500_eu": (growth_allocation*(100-0))/100,
            "2x_ndx100_eu": (growth_allocation*0)/100,
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
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# Adding gold to this portfolio is reducing the risk. Which is in line with our previous backtests. 

# ### 65% Growth Allocation with 3x leveraged ETNs and without Nasdaq-100

# In[ ]:


allocations = list(range(0,101,5))
growth_allocation = 65
ndx_allocation = 15

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold with Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_eu": (growth_allocation*(100-0))/100,
            "3x_ndx100_eu": (growth_allocation*0)/100,
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
portfolios['P'] = p_pari
short_names.append('P')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# So adding Gold here is slightly increasing the performance, but also the risk. 

# ### HFEA with 25% of Nasdaq-100 allocation

# In[ ]:


allocations = list(range(0,101,5))
growth_allocation = 55
ndx_allocation = 25

short_names = []
portfolios = {}
for p in allocations:
    name = f"{p}%"
    print(f"Calculate: {name} Gold with Nasdaq-100")
    short_names.append(name)
    portfolios[name] = Portfolio(
        {
            "3x_sp500_us": (growth_allocation*(100-40))/100,
            "3x_ndx100_us": (growth_allocation*40)/100,
            "3x_ltt_us": ((100-growth_allocation)*(100-p))/100,
            "1x_gold_us": ((100-growth_allocation)*(p))/100,
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


# So adding 5% Gold is giving less risk with more or less the same performance. 

# ## Summary
# 
# It seems that it does not make too much sense to add Nasdaq-100 and Gold together. So actually is a decision where we either add Gold in order to anticipate higher inflation and interest rate or to add Nasdaq-100 to anticipate upcoming low interest rate for the next years and thus a strong performance of growth/tech stocks. 

# In[ ]:


allocations = [
    ("2x S&P 500",  ('2x_sp500_eu', 100), ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 0),  ('1x_gold_eu', 0)),
    
    ("50%",         ('2x_sp500_eu', 50),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 50), ('1x_gold_eu', 0)),
    ("50%+G",       ('2x_sp500_eu', 50),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 37.5), ('1x_gold_eu', 12.5)),
    ("50%+N",       ('2x_sp500_eu', 42.5),  ('2x_ndx100_eu', 7.5), ('1x_ltt_eu', 50), ('1x_gold_eu', 0)),
    ("50%+NG",      ('2x_sp500_eu', 42.5),  ('2x_ndx100_eu', 7.5),  ('1x_ltt_eu',37.50), ('1x_gold_eu', 12.5)),
    
    ("65%",         ('2x_sp500_eu', 65),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 35), ('1x_gold_eu', 0)),
    ("65%+G",       ('2x_sp500_eu', 65),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 26.25), ('1x_gold_eu', 8.75)),
    ("65%+N",       ('2x_sp500_eu', 55.25),  ('2x_ndx100_eu', 9.75),  ('1x_ltt_eu', 35), ('1x_gold_eu', 0)),
    
    ("80%",         ('2x_sp500_eu', 80),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 20), ('1x_gold_eu', 0)),
    ("80%+G",       ('2x_sp500_eu', 80),  ('2x_ndx100_eu', 0),  ('1x_ltt_eu', 15), ('1x_gold_eu', 5)),
    ("80%+N",       ('2x_sp500_eu', 68),  ('2x_ndx100_eu', 12), ('1x_ltt_eu', 20), ('1x_gold_eu', 0)),
    ("80%+NG",      ('2x_sp500_eu', 68),  ('2x_ndx100_eu', 12), ('1x_ltt_eu', 15), ('1x_gold_eu', 5)),
    
    ("65% (3x)",    ('3x_sp500_eu', 65),  ('3x_ndx100_eu', 0),  ('3x_itt_eu', 35), ('1x_gold_eu', 0)),
    ("65%+G (3x)",  ('3x_sp500_eu', 65),  ('3x_ndx100_eu', 0),  ('3x_itt_eu', 26.25), ('1x_gold_eu', 8.75)),
    ("65%+N (3x)",  ('3x_sp500_eu', 55.25), ('3x_ndx100_eu', 9.75),  ('3x_itt_eu', 35), ('1x_gold_eu', 0)),
    
    ("HFEA",        ('3x_sp500_us', 55),  ('3x_ndx100_us', 0),  ('3x_ltt_us', 45), ('1x_gold_us', 0)),
    ("HFEA+G",      ('3x_sp500_us', 55),  ('3x_ndx100_us', 0),  ('3x_ltt_us', 33.75), ('1x_gold_us', 11.25)),
    ("HFEA+N",      ('3x_sp500_us', 41.25),  ('3x_ndx100_us', 13.75), ('3x_ltt_us', 45), ('1x_gold_us', 0)),
    ("HFEA+NG",     ('3x_sp500_us', 41.25),  ('3x_ndx100_us', 13.75),  ('3x_ltt_us', 38.25), ('1x_gold_us', 6.75)),
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
            a[4][0]: a[4][1],
        },
        start_value = 1000,
        rebalancing = relativedelta(months=3),
        rebalancing_offset = relativedelta(days=-6),
    ).backtest(etfs)
    

portfolios['S&P500'] = p_sp500
short_names.append('S&P500')

compare_portfolios(
    portfolios,
    short_names = short_names,
    details=True,
) 


# In[ ]:




