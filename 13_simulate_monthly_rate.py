#!/usr/bin/env python
# coding: utf-8

# # Simulate Monthly Rate

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import pandas.tseries.offsets as pd_offsets
import pickle
import plotly.graph_objects as go
from typing import Dict, Tuple, Optional
from dateutil.relativedelta import relativedelta
import itertools
from typeguard import typechecked


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart, draw_risk_reward_chart, draw_periodic_return
from utils.plots import draw_correlations, compare_portfolios, draw_max_portfolio_drawdowns, draw_min_portfolio_returns
from utils.plots import draw_monte_carlo_simulation
from utils.math import gmean, calc_min_returns, calc_max_drawdown, calc_correlations_over_time, normalize, calc_returns
from utils.math import to_float, calc_growth, normalize_df, calc_monte_carlo_simulations
from utils.math import apply_monte_carlo_sim, calc_simulation_characteristics
from utils.data import cached, read_csv
from utils.portfolio import Portfolio, Asset, GermanTaxModel, MAPortfolio


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


p_cash = MAPortfolio(
    {
        'cash': dict(dist=100),
    },
    start_value = 10000,
).backtest(etfs)


# In[6]:


p_50 = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50),
        '1x_ltt_eu': dict(dist=50),
    },
    start_value = 10000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[7]:


p_80 = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80),
        '1x_ltt_eu': dict(dist=20),
    },
    start_value = 10000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[8]:


p_65_3x = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65),
        '3x_itt_eu': dict(dist=35),
    },
    start_value = 10000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[9]:


p_2x_sp500_ma = MAPortfolio(
    {
        "2x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[10]:


p_hfea = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55),
        '3x_ltt_us': dict(dist=45),
    },
    start_value = 10000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[11]:


@typechecked
def perform_monte_carlo_simulation(
    simulation_time: relativedelta,
    portfolio: pd.DataFrame,
    portfolio_name: str,
    start_value: float = 10000,
    monthly_rate: float = 0,
    portfolio_simulations: int = 100,
    reference: Optional[pd.DataFrame] = None,
    reference_name: Optional[str] = None,
    reference_simulations: int = 100,
):
    portfolio_simulation = calc_monte_carlo_simulations(portfolio, portfolio_simulations, simulation_time)
    portfolio_simulation = apply_monte_carlo_sim(
        portfolio_simulation, 
        start_value = start_value, 
        periodic_rate = monthly_rate, 
        rate_interval = 30
    )

    kwargs = {}
    is_reference = reference is not None and reference_name is not None
    if is_reference:
        reference_simulation = calc_monte_carlo_simulations(reference, reference_simulations, simulation_time)
        reference_simulation = apply_monte_carlo_sim(
            reference_simulation, 
            start_value = start_value, 
            periodic_rate = monthly_rate, 
            rate_interval = 30
        )
        kwargs['reference']=calc_simulation_characteristics(reference_simulation)['mean']
        kwargs['reference_name']=reference_name  

    draw_monte_carlo_simulation(
        calc_simulation_characteristics(portfolio_simulation),
        portfolio_name,
        draw_stddev = True,
        draw_minmax = True,
        **kwargs,
    )


# ### Settings

# In[12]:


start_value = 10000
monthly_rate = 100
simulation_time = relativedelta(years = 15)


# ### 50% Portfolio

# In[13]:


perform_monte_carlo_simulation(
    portfolio = p_50,
    portfolio_name = '50% Portfolio',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = start_value,
    monthly_rate = monthly_rate,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# ### 80% Portfolio

# In[14]:


perform_monte_carlo_simulation(
    portfolio = p_80,
    portfolio_name = '80% Portfolio',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = start_value,
    monthly_rate = monthly_rate,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# ### 65% (3x) Portfolio

# In[15]:


perform_monte_carlo_simulation(
    portfolio = p_65_3x,
    portfolio_name = '65% (3x) Portfolio',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = start_value,
    monthly_rate = monthly_rate,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# ### HFEA

# In[16]:


perform_monte_carlo_simulation(
    portfolio = p_hfea,
    portfolio_name = 'HFEA',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = start_value,
    monthly_rate = monthly_rate,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# ### 2x S&P 500 (MA) Portfolio

# In[17]:


perform_monte_carlo_simulation(
    portfolio = p_2x_sp500_ma,
    portfolio_name = '2x S&P 500 (MA)',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = start_value,
    monthly_rate = monthly_rate,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# ### Wishes

# In[19]:


perform_monte_carlo_simulation(
    portfolio = p_2x_sp500_ma,
    portfolio_name = '2x S&P 500 (MA)',
    reference = p_cash,
    reference_name = 'cash',
    simulation_time = simulation_time,
    start_value = 5800,
    monthly_rate = 250,
    portfolio_simulations = 300,
    reference_simulations = 10,
)


# In[ ]:




