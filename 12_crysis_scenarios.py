#!/usr/bin/env python
# coding: utf-8

# # Backtest HFEA for different Scenarios
# 
# ## Identifying Scenarios

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
from utils.portfolio import Portfolio, MAPortfolio, GermanTaxModel


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


input_path = clean_data_path / "inflation.xlsx"
inflation = pd.read_excel(input_path, index_col=0)
inflation.index = pd.to_datetime(inflation.index)
inflation


# In[6]:


input_path = clean_data_path / "ffr.xlsx"
interest = pd.read_excel(input_path, index_col=0)
interest.index = pd.to_datetime(interest.index)
interest


# ## Portfolios

# In[7]:


portfolios = {}


# ### General Portfolios

# In[8]:


p_sp500 = Portfolio(
    {
        '1x_sp500_eu': 100.0,
    },
    start_value = 1000,
    tax_model=GermanTaxModel(),
).backtest(etfs)

p_2x_sp500_ma = MAPortfolio(
    {
        "2x_sp500_eu": dict(dist=100, ma=290, ma_asset="1x_sp500_eu"),
    },
    start_value = 1000,
    tax_model=GermanTaxModel(),
).backtest(etfs)

p_2x_sp500 = Portfolio(
    {
        '2x_sp500_eu': 100.0,
    },
    start_value = 1000,
    tax_model=GermanTaxModel(),
).backtest(etfs)

p_pari = Portfolio(
    {
        '1x_sp500_eu': 60.0,
        '1x_ltt_eu': 40.0,
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),
    tax_model=GermanTaxModel(),
).backtest(etfs)


# In[9]:


portfolios['S&P500'] = p_sp500
portfolios['2x S&P500'] = p_2x_sp500
portfolios['2x S&P500 (MA)'] = p_2x_sp500_ma
portfolios['P'] = p_pari


# ### 50% Portfolios

# In[10]:


p_base = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50),
        '1x_ltt_eu': dict(dist=50),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
).backtest(etfs)

p_base_ma = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=50, ma=290, ma_asset="1x_sp500_eu"),
        '1x_ltt_eu': dict(dist=50, ma=130, ma_asset="1x_ltt_eu"),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-6),    
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
).backtest(etfs)    


# In[11]:


portfolios['50%'] = p_base
portfolios['50%+G'] = p_g
portfolios['50%+N'] = p_n
portfolios['50%+NG'] = p_ng

portfolios['50%+MA'] = p_base_ma
portfolios['50%+N+MA'] = p_n_ma
portfolios['50%+NG+MA'] = p_ng_ma


# ### 80% Portfolios

# In[12]:


p_base = MAPortfolio(
    {
        '2x_sp500_eu': dict(dist=80),
        '1x_ltt_eu': dict(dist=20),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),   
    spread = 0.002,
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
).backtest(etfs)   


# In[13]:


portfolios['80%'] = p_base
portfolios['80%+G'] = p_g
portfolios['80%+N'] = p_n
portfolios['80%+NG'] = p_ng

portfolios['80%+MA'] = p_base_ma
portfolios['80%+N+MA'] = p_n_ma
portfolios['80%+NG+MA'] = p_ng_ma


# ### 65% (3x) Portfolios

# In[14]:


p_base = MAPortfolio(
    {
        '3x_sp500_eu': dict(dist=65),
        '3x_itt_eu': dict(dist=35),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8),    
    spread = 0.002,
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
#    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
#    tax_model=GermanTaxModel(),
#).backtest(etfs)   


# In[15]:


portfolios['65% (3x)'] = p_base
portfolios['65%+G (3x)'] = p_g
portfolios['65%+N (3x)'] = p_n

portfolios['65%+MA (3x)'] = p_base_ma
portfolios['65%+N+MA (3x)'] = p_n_ma


# ### HFEA Portfolios

# In[16]:


p_base = MAPortfolio(
    {
        '3x_sp500_us': dict(dist=55),
        '3x_ltt_us': dict(dist=45),
    },
    start_value = 1000,
    rebalancing = relativedelta(months=3),
    rebalancing_offset = relativedelta(days=-8), 
    spread = 0.002,
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
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
    tax_model=GermanTaxModel(),
).backtest(etfs)   


# In[17]:


portfolios['HFEA'] = p_base
portfolios['HFEA+G'] = p_g
portfolios['HFEA+N'] = p_n
portfolios['HFEA+NG'] = p_ng

portfolios['HFEA+MA'] = p_base_ma
portfolios['HFEA+N+MA'] = p_n_ma
portfolios['HFEA+NG+MA'] = p_ng_ma


# In[18]:


### Crysis-Tests


# In[19]:


def calc_backtests(portfolios, beginn, end):
    short_names = list(portfolios.keys())

    copied_portfolios = {}
    for name in portfolios.keys():
        copied_portfolios[name] = portfolios[name].loc[str(beginn):str(end)].copy()
        copied_portfolios[name] = normalize_df(copied_portfolios[name], start_value=10000)
    
    compare_portfolios(
        copied_portfolios,
        short_names = short_names,
        details=True,
    ) 
    return portfolios


# ### 1962: Cuba Crysis
# 
# * Start October 1962
# * USA and Russia threatened each other with a nuclear first strike
# * USA stationed nuclear weapons in Turky, GB and Italy
# * Russia stationed nuclear weapons in Cuba
# * After USA detected those nuclear weapons in Cuba, they started blocking ships with target Cuba
# * It was the frist and last time, that USA and Russia was directly on the edge of a nuclear war
# * Dow Jones lost 25%
# * However, stock market recovered fast, after diplomatic solution to the crysis

# In[20]:


beginning = '1962'
end = '1964'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
#fig.update_yaxes(title_text="inflation in % (yoy)", secondary_y=True, showgrid=False)
#fig.add_trace(
#    go.Scatter(
#        x=inflation.loc[beginning:end, 'yoy'].index,
#        y=inflation.loc[beginning:end, 'yoy'],
#        mode='lines',
#        name="inflation",
#    ),
#    secondary_y=True
#)
fig.show()


# We see a maximum drawdown of 25% in S&P 500. Also a small drawdown in LTTs are visible. The drawdown started around the 20th of March 1962 as the bottom was reached in June 1962. This was before the Cuba Crysis started to became hot. It was called the "Flash Crash of 1962" and one of the reasons for this small crash was probably a long time of strong growting beforehand, which now leads to an substantial correction. 
# 
# After the Crash the prices started to recover soon, until Aug. 1962, when the first signs of the Cuba Crysis became public. Then the stock prices crashed again until the final solution of the Crysis in Oct. 1962. Afterwards a strong growth started again and in April 1963, the stock markete recovered completly. 

# In[21]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall
# * The crash was with 25% not so bad, thus the 2x S&P 500 could recover quite fast. It just had a drawdown of 46% and was able to recover within 11 month. 
# * 65% (3x) and HFEA portfiolio can reach the same performance as 2x S&P 500. Even with smaller risk. 
# * 80% portfolio is much worse than 2x S&P 500.
# * 50% portfolio is even not fully reaching the 2&P 500 performance. 
# * All MA variants are much better and much less riskier than non MA variants. 
# 
# #### Winner (Performance)
# * The 2x S&P 500 (MA) portfolio is the clear winner. 
# * Best non-MA is HFEA(+N/+NG/+G)
# 
# #### Winner (Risk/Peroformance-Tradeof)
# * Also here the 2x S&P 500 (MA) portfolio is the winner. 
# 
# #### Notes
# * Holding a small amount of Gold during this time is reducing the performance without any improvement of the risk measure. 
# * Nasdaq-100 was not applicable at this time. 

# ### 1973: "Oil Crysis"
# 
# * In 1973, OPEC is reducing the production of Oil to protest against support of western countries for Isreal in the "Yom Kippur War"
# * Due to Oil shortage, the economic growth was dropping and inflation was raising
# * Countries started policies for increasing economic growth, but since the supply shock did not end, this was just increasing inflation leading to a stagflation. 

# In[22]:


beginning = '1973'
end = '1980'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# Already in January 1973 the stock market started to fade away. In the same time the inflation was increasing drastically from 3% to 7%. In October 1973, the Yom Kippur War started and as reaction to this war OPEC was reducing the Oil production. We can see a first big drop by 16% in the stock market until December, followed by a sideway period. In March 1974, so around 3-4 month after the drop, it seems that a recovery will come, but then the stock market dropped again up to 35% from the value of March 1974. In sum the stock market was dropping 44%. During this time the inflation was reaching a value of up to 12%. 
# 
# When inflation started to decrease, the stock market also started to recover strongly. But it still was sensitive to small increases of inflation as we can see in Jul. 1975. It tool 42 month, until the stock market reached the level before the crysis started. But afterwards it was still trapped in years long sideway trend until late 1978/1979. Interestingly the second oil crysis in 1987 seems not to have a big effect at all. 
# 
# The interest rate was also increased from beginning of 1973 until Sep. 1973. Then the rate was reduced, just to increase it strongly from beginning 1974 to mid of 1974. After mid of 1974 the interest rate was falling until 1977 and then slightly increaed again. 
# 
# We can clearly see, that the LTT price is are often inverse to the interest rate. If the interest rate growth strongly the LTT in declining. If the interest rate in dropping, the LTTs are growing. Very interesting is the time from 1977, where the interest rate is starting to increase again, but very slowly. At this time the LTTs are just moving sideways and are not dropping much. However they start to drop mid of 1979, when the interest rate was increased much in very short time. 
# 
# So here we can conclude: That a moderate increase of interest rate is not directly harming LTTs. But a strong and therefore maybe unexpected increase lets the LTTs drop. Nevertheless, you need to take into account, that LTTs were callable at this time. So it could be that they are now much less sensitive to interest rate then at the 1970th. 
# 
# The gold price is exploding at this time. However: we don't know if the increase of the gold price was the reaction of the high inflation or the reaction of the end of the Bretton-Woods-System.

# In[23]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall
# While the S&P 500 is losing 45% during the first crash, the 2x S&P 500 is losing almost 75%. Furthermore we have a long an somehow choppy recovering, thus the 2x S&P 500 is even more suffering from volatility decay. It takes 84 month for the leverages S&P 500 to recover to the value before the crysis started. 
# 
# Not a single non MA portfolio was able to reach the same performance as S&P 500 during this crysis. 2x S&P 500, HFEA and 65% (3x) had even negative CAGR for 7 years, while HFEA is performing the worst with -7.3% CAGR and 76% max. drawdown. Only 65% (3x) and S&P 500 have a higher drawdown. 
# 
# All MA-Variants are performing much better then non MA-Variants. HFEA+NG+MA is almost reaching S&P 500 and 50%+NG+MA is even better then S&P 500, with much lower risk. 
# 
# #### Winner (Peformance)
# * 50%+NG+MA
# * Best non-MA Variant: 50%+G or 50%+NG
# 
# #### Winnder (Risk/Performance-Tradeoff)
# * Also 50%+NG+MA
# 
# #### Notes
# * In this crysis the LTTs are losing together with shares
# * Adding Gold is giving a major improvement in this situation
# 

# ### 1987: Black Monday
# * Over the past years, there was a very strong share growth
# * However in Aug. 1987 the stock prices starts to go sideways 
# * furthermore there was still a high inflation and thus a strong interest rate

# In[24]:


beginning = '1987'
end = '1989'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# We see a strong growth in the stock market of over 40% in the first 7 month of 1987. The ATH is reached at the 25. Aug. 1987. Suddently the stock price corrects by around 8% in September. After this correction is starts to recover up to 2% below ATH and then crashes drastically within few days by 30%. However compared to the stock price beginning of the year, we are jut 5% down. The Nasdaq-100 is moving very similar to S&P 500, but shows in general a higher growth. 
# 
# After December 1987, a choppy but steady recovery is starting and after around 2 years the ATH from Aug. 1987 is reached again.
# 
# The LTTs have dropped all the time from beginning 1987 until the crash. But at the day of the crash, the LTTs start to jump and grow again. Eventhough the interest rate is beeing increaed at this time. The Inflation is with around 5% quite high at this time, but the interest rate is high as well. 
# 
# Gold price is increasing until beginning of 1988 and starts then to drop, when it became clear, that the inflation rate seems to be stable at around 5%. 

# In[25]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall 
# During the 3 years of this time, almost no non-MA portfolio was able to reach the performance of S&P 500 buy and hold. Only the MA-Portfolios are able to outperform the S&P 500, but this is coming with the price of a higher risk. The 80% portfolio is reaching with CAGR of 15,3% almost the CAGR of S&P 500, but with much higher risk (50% vs. 33%). HFEA and 65% (3x) portfolio had the lovest CAGR and highest risk levels. HFEA+N portfolio is performing extremly well in this crysis. 
# 
# #### Winner (Performance)
# * 2x S&P 500 (MA)
# * Non-MA: 80% Portfolio with CAGR
# 
# #### Winner (Risk/Performance-Tradeof)
# * 50%(+N/+NG/+G)+MA
# 
# #### Notes
# * Adding Gold is reducing the risk slightly, but also the CAGR (in Non-MA cases only)
# * Adding Nasdaq-100 is increasing the performance drastically and also lowering the risk slightly

# ### 1990: The Second Gulf War
# * Iraq was attacking Kuwait
# * A coalition lead by USA started the defence of Kuwait as attacks Iraq. 

# In[26]:


beginning = '1990'
end = '1991'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# The stock market reaches a high in Jul. 1990, since then it was dropping. Beginning auf Aug. it starts to drop enormously and reaches around -20% from the last high in Jul 1990. The stock market is recovering even before the US coalition was formed. At the beginning of the coalition attacs in Jan. 1991 the stock market crashes again slightly, but recovers very fast, even before the victory of the coalition. Already in February 1991 the stock market reaches a new high and starts growing strongly the years after. The Nasdaq-100 is following S&P 500 with a higher drop, but then also with a stronger growth afterwards. 
# 
# Gold is losing slightly all the time, but jumped up, when the stock market started to crash. Maybe the market participents fear a new oil crysis due to the war. When it was clear, that the war is just a regional conflict and even many OPEC countries are not on the side of Iraq, the goldprice dropped again. 
# 
# In all that time, LTTs where mostly growing, which is because the interest rate was reduced after October 1990 from 8.5% to 4% in end of 1991. Also the inflation was decreasing to only 3% in end of 1991. The decreasing interest rate might be the reason for the strong growth of Nasdaq-100 in the years after the war. 

# In[27]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall
# * Every non-MA portfolio without gold is outperforming S&P 500 and 2x S&P 500 during those two years.
# * All MA portfolios are massivly underperforming, because of the fast recovery
# 
# #### Winner (Performance)
# * HFEA+N is drastically outperforming all other portfolios with CAGR of 23% and a max. drawdown of 43%.
# * 65% (3x) with CAGR of 16% and a max. drawdown of 39%
# 
# #### Winner (Risk/Performance-Tradeoff)
# * 50%+N is reachong high performance and low risk
# 
# #### Notes
# * Adding Gold is reducing the risk slightly, but also the performance
# * Adding Nasdaq-100 is strongly increasing the performance, but also slightly the risk 

# ### 2000: Dot-Com Bubble
#   * Beginning of 2000 it was clear, that many tech-companies will not have positive earnings in the next time
#   * Furthermore the markert capitalization was too high compared to the real asset value the companies owned
#   * Also more and more of those tech-companies became bankrupted 
#   * Thus the trust in those companies faded and stock prices started to drop
#   * Over 5 years many tech-companies had a much too low company valuation
#   * The FED started to decrease interest rates and due to the missing trust in growth companies, capital was flowing mostly in value companies and real estate assets
#   * This was maybe one of the reason for the financial crysis in year 2007
# 

# In[28]:


beginning = '2000'
end = '2005'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# This was a slow and long crash of the stock market. The S&P 500 went sideways from starting of 2000, after reaching a high in March. Beginning from September it started to fade, with a lot of tries to recover but big drops shortly after such recovery attempt. In March 2001 and Sep. 2001 (probably due to 9/11) the stock price was dropped very fast. The minimum was reached in Oct. 2002 with -48%, when the S&P 500 went sideways again until May 2003 and then breaks out and recovers over many years. Even end of 2005 the S&P 500 have not been recovered completely. 
# 
# The crash of the Nasdaq-100 started alreaey in March 2000 and here as well the minim was reached in Oct. 2002 with -83% (!). After a short time of slow recovery from March 2003 to beginning 2004, the Nasdaq-100 went mostsly sideways and have not even been able to recover to -50% until end of 2005.
# 
# Since 2002 Gold started to grow again, after 20 years of decay. During the crysis the interest rate was reduced to just 1% but mid of 2004 it was increased again, because inflation became slightly higher. Inflation was with below 1.5% in first half of 2002 very low and then normalized again to 3%. LTTs had a stead growth at this time without any drops, which could be related to the Dot-Com Bubble. 

# In[29]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall
# * This crysis is a stock-market crysis. Thus all portfolios with high stock allocation are suffering from it. 
# * Only 50% and HFEA portfolios have a positive CAGR for those 5 years. 
# * Using MA-Strategy is increasing CAGR and reducing risk, but still all MA-Portfolios have negative CAGR for those years (except 50%+MA).
# 
# #### Winner (Performance)
# * HFEA has a CAGR of 0.6% for those 5 years, but a huge drawdown of 63%
# * 50% portfolio has a CAGR of 0.1% but a drawdown of only 46%, which makes it to a better portfolio then HFEA directly
# 
# #### Winner (Risk/Performance-Tradeof)
# * 50% portfolio has a CAGR of 0.1% but a drawdown of only 46%, which makes it to a better portfolio then HFEA directly
# 
# #### Notes
# * Adding Nasdaq-100 is just increasing the risk and even decreasing the performance
# * Adding Gold is neither increasing performance nor decreasing risk

# ### 2007: Financial Crysis
#   * Start in August 2007 due to fading trust in many real estate loans
#   * In September 2008 the Bank Leman Brothers became bankrupped

# In[30]:


beginning = '2007'
end = '2012'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# The last high was in October 2007. But this high was already just a very small imvprovement compared to the high in Jul 2007. Thus actually the stock market went already sideways at this time. After October 2007 the market dropped. It somehow started to recover, but in the end it just build lower highs and lower lows. Then in September 2008 there was the big crash. Also here we had several attempts to recover. In January 2009 we had a local high, but the bottom was reached on May 2009 with -55% from the last real high in October 2007. So the crash actually last almost 2 years, before the real recovery started. In March 2012 the stock market built a new ATH. Nasdaq-100 was very similar to S&P 500, but it recovered faster. Here already in January 2011 a new ATH was reached. 
# 
# Gold was growing strongly during this time. However it also crashed sligthly in March 2008 and reaches a buttom in November 2008 with -30%. LTTs did not crash, but jumped up during the stock market crash. Also, already in June, the interest rate started to drop and reached 0.17% in March 2009. The inflation rate jumped up in 2008, but then dropped hardly and stabilized at 2% in the end of 2012. 

# In[31]:


p = calc_backtests(portfolios, beginning, end)


# #### Overall
# * The 2x S&P 500 ETF did not reach breakeven until 2012, thus it had a negative CAGR by almost -5%
# * Also some 80% portfolios had a negative CAGR.
# * All other portfolios had positive CAGR. Most of then outperform the S&P 500. 
# 
# #### Winners (Performance)
# * HFEA+N is the clear winner with a CAGR of 13.9% and a max. drawdown of 64% during the crysis. 
# * The 50%+N portfolio reaches a CAGR of 6.5%, combined with a max. drawdown of just 51%.
# 
# #### Winners (Risk/Performance-Tradeof)
# * The 50%+MA portfolios reaches a CAGR of 4.4%, combined with a max. drawdown of just 17%.
# 
# #### Notes
# * Adding Nasdaq-100 is increaing the performance and also reducing the risk. 
# * Adding Gold does not give any advantage. 
# * Using MA Strategy is reducing the risk drastically, but also the CAGR.

# ### 2020: Corona-Pandemic
#   * Started on 9th of March with a "Lockdown" in many countries of the world. 

# In[32]:


beginning = '2020'
end = '2020'
normalized_etfs = normalize_df(etfs.loc[beginning:end, :], start_value=100)
fig = draw_growth_chart(
    {
        'S&P 500': normalized_etfs['1x_sp500_us'],
        'Nasdaq-100': normalized_etfs['1x_ndx100_us'],
        'Gold': normalized_etfs['1x_gold_us'],
        'LTT': normalized_etfs['1x_ltt_us'],
    },
    show = False
)
fig.update_yaxes(title_text="inflation (yoy) in % / interest rate", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=inflation.loc[beginning:end, 'yoy'].index,
        y=inflation.loc[beginning:end, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.add_trace(
    go.Scatter(
        x=interest.loc[beginning:end, 'ffr'].index,
        y=interest.loc[beginning:end, 'ffr'],
        mode='lines',
        name="interest",
    ),
    secondary_y=True
)
fig.show()


# Before the crysis the stock market had a high at 19th of February 2020 and then it lost -34% until 23rd of March 2020. After this it started to recover very fast and reached a new ATH in August 2020. The Nasdaq-100 was even faster and reached a new ATH in June. In general the growth of the Nasdaq-100 was superior to the S&P 500 during this time. 
# 
# Gold hat a short drop in March, but recoverd soon. Then it was growting a little bit until August and lost then again. LTTs jumped up to a new high in March 2020 and went sideways afterwards. 
# 
# Inflation dropped to almost 0 and stabilized at around 1.5%, while interest rate was reduced to almost 0% in April 2020. 

# In[33]:


p = calc_backtests(portfolios, beginning, end)


# #### Overview
# * Apart from the drawdown in March/April, this was not a real stock market crysis. Even the S&P reached a return of 18% in 2020. All portfolios had a much higher return.
# * The 2x S&P 500 (MA) could not outperform the 2x S&P 500, which is unique.
# 
# #### Winner (Performance)
# * HFEA+N is reaching the absolut top performance with 59% in 2020 and a max. drawdown of 38%. 
# * 80%+NG reaches 45% CAGR
# 
# #### Winner (Risk/Performance)
# * The 50%+NG+MA portfolio has a higher performance than S&P 500 ETF with 21% and just a max. drawdown of 17%.
# 
# #### Notes
# * Adding Nasdaq-100 is massivly increasing the performance without changing the risk.
# * Adding Gold is not giving any advantage. 
# * MA-Strategy is reducing CAGR but also risk a lot. 
