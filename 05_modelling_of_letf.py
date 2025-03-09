#!/usr/bin/env python
# coding: utf-8

# # Modelling of (L)ETFs
# 
# In this section we will model (L)ETFs out of our basic asset classes. To verify our model, we check the modeled results aginst real ETFs for the same underlaying. We start with ETFs from US and if we get reasonable results here, we also check against EU ETFs, if possible.

# Again, hat bogleheads there is a thread about a LETF model, which can be used as source four our work here: https://www.bogleheads.org/forum/viewtopic.php?f=10&t=272640#top
# 
# In the post https://www.bogleheads.org/forum/viewtopic.php?p=4421454#p4421454 the user `siamond`, which is also maintaining Simbas Backtest Spreadsheet, comes up with a model, which can more or less be seen as final. Later another user makes this model even more realistic, by introducing some more correction values, for which timeseries are available. However it is often hard to get those timeseries from 1943. So will use the model of `siamond` here, which uses data, we already have and abstracts the other values in a higher adjustment factor, which is some kind of curve fitting. 
# 
# In this model the daily return of a (L)ETF $r_{return}$ is calculated by:
# 
# $$r_{letf} = L \cdot r_{index} - ER_{daily} - (L-1) \cdot BR_{daily} + A_{daily}$$
# 
# With the following terms:
# * $r_{index}$ is the daily return of the underlaying 
# * $L$ is the leverage factor
# * $ER_{daily}$ is the daily expense ratio of the ETF
# * $BR_{daily}$ is the daily borroring rate
# * $A_{daily}$ is an anjustment factor, which abstracts away other tracking error and ETF expenses 
# 
# 
# For calculating daily percentage values out of yearly values, we use the geometric mean, which is defined as:
# 
# $$x_{daily} = \sqrt[\frac{1}{365}]{x_{yearly} + 1} - 1$$
# 
# There are many small details about this formula discussed in the thread. For example to use 360 days per year instead of 365 for to not use geometric mean for the borrwing rate. However during my experiments I found out, that using 365 days and geometric mean is leading more or less to the same results. 

# In[1]:


import numpy as np
import pandas as pd
from pathlib import Path


# In[2]:


from utils.data import download_from_yahoo, download_from_investing, read_csv
from utils.math import calc_returns, calc_growth, normalize, reindex_and_fill, to_float
from utils.plots import draw_growth_chart, draw_telltale_chart


# In[3]:


def calc_letf(daily_returns, er, borrowing_rate=None, leverage = 1, adjustment_factor = 0, days_in_year = 365, percent=100):
    def gmean(x):
        return (x + 1)**(1 / days_in_year) - 1
    
    assert (leverage == 1) or (borrowing_rate is not None), "If leverage is not 1, you must provide the ffr argument!"
    
    if borrowing_rate is not None:
        daily_borrowing_rate = (leverage - 1) * gmean(-borrowing_rate/percent)
    else:
        daily_borrowing_rate = 0
        
    daily_adjustment_factor = gmean(adjustment_factor/percent)
    daily_er = gmean(-er/percent)
    
    return daily_returns * leverage + daily_er + daily_borrowing_rate + daily_adjustment_factor
    


# In[4]:


clean_data_path = Path("clean_data")
raw_data_path = Path("raw_data")


# In[5]:


assets_path = clean_data_path / "assets.xlsx"
assets = pd.read_excel(assets_path, index_col = 0)
assets.index = pd.to_datetime(assets.index)
assets


# In[6]:


borrowing = pd.read_excel(clean_data_path / "borrowing_rate.xlsx", index_col = 0)
borrowing.index = pd.to_datetime(borrowing.index)
borrowing = borrowing['borrowing_rate']
borrowing


# In[7]:


assets_daily_returns = calc_returns(assets, freq="D")
assets_daily_returns


# ## S&P 500 (L)ETFs
# 
# Let's start buy using the S&P 500 index an create ETFs with 1x, 2x and 3x leverage here. The comparison ETFs are:
# * S&P 500 x1 => SPY (+ dividends)
# * S&P 500 x2 => ULPIX (+ dividends)
# * S&P 500 x3 => UPRO (+ dividends)

# In[8]:


spy = download_from_yahoo("SPY", adjust=True)
spy = reindex_and_fill(spy, min(spy.index), max(spy.index), freq="D")
spy


# Now we compare the SPY ETF growth with our S&P 500 time-series. In the telltale chart, we use the SPY as refernce. 

# In[9]:


draw_growth_chart(
    {
        'SPY (S&P 500 x1)': normalize(spy, assets['sp500+div']),
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    normalize(spy, assets['sp500+div']),
    {
        'S&P 500': assets['sp500+div'],
    },
    "S&P 500 (reference: SPY)",
    overlapping_only = True,
)


# We can see, that our S&P 500 time-series is already tracking the SPY very well. However over many years the S&P 500 is diverging from the SPY reference. This is, because we did not take the Expense Ratio of the SPY into account. For this we now model a an ETF. The SPY ETF has an ER of 0,09%. 

# In[10]:


etfs = pd.DataFrame(index=assets.index)


# In[11]:


etfs['1x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    er=0.09, 
    percent=100
), percent=1)
etfs


# In[12]:


n = normalize(spy, etfs['1x_sp500_us'])
draw_growth_chart(
    {
        'SPY (S&P 500 x1)': n,
        '1x S&P 500 (model)': etfs['1x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x S&P 500 (model)': etfs['1x_sp500_us'],
    },
    "S&P 500 (reference: SPY)",
    overlapping_only = True,
)


# With the expense ratio of 0,09% our ETF model is not diverging anymore so strong. But there is still a positive offset, which slightly grows over time. Thus we introduce additionally 0,04% per year as adjustment factor. This adjustment factor takes further tracking errors of the ETF into account.

# In[13]:


etfs['1x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    er=0.09, 
    adjustment_factor=-0.04,
    percent=100,
), percent=1)
etfs


# In[14]:


n = normalize(spy, etfs['1x_sp500_us'])
draw_growth_chart(
    {
        'SPY (S&P 500 x1)': n,
        '1x S&P 500 (model)': etfs['1x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x S&P 500 (model)': etfs['1x_sp500_us'],
    },
    "S&P 500 (reference: SPY)",
    overlapping_only = True,
)


# Eventhough our ETF model is slighly higher for many years, we clearly see that the difference is not growing anymore. Thus it seems that the model is tracking the SPY good enough. 

# Next we concentrate on a leverage of 2 and compare it to the ULPIX.

# In[15]:


ulpix = download_from_yahoo("ULPIX", adjust=True)
ulpix = reindex_and_fill(ulpix, min(ulpix.index), max(ulpix.index), freq="D")
ulpix


# In[16]:


n = normalize(ulpix, assets['sp500+div'])
draw_growth_chart(
    {
        'ULPIX (S&P 500 x2)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500 (reference: ULPIX)",
    overlapping_only = True,
)


# Comparing the ULPIX with our S&P 500 time-series reviels, that it was underperforming the index by a long periode. Only recently since the corona crash it recovers. 
# 
# ULPIX has an expanse ratio of 1,51%. So we can create an ETF model out of it.

# In[17]:


etfs['2x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=1.51, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[18]:


n = normalize(ulpix, etfs['2x_sp500_us'])
draw_growth_chart(
    {
        'ULPIX (S&P 500 x2)': n,
        '2x S&P 500 (model)': etfs['2x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x S&P 500 (model)': etfs['2x_sp500_us'],
    },
    "S&P 500 (reference: ULPIX)",
    overlapping_only = True,
)


# As we can see, our model diverges over time from the ULPIX. So we have to add an adjustment factor for keeping further costs into account. We chose here -1.1% per year. 

# In[19]:


etfs['2x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=1.51, 
    adjustment_factor=-1.1,
    percent=100
), percent=1)
etfs


# In[21]:


n = normalize(ulpix, etfs['2x_sp500_us'])
draw_growth_chart(
    {
        'ULPIX (S&P 500 x2)': n,
        '2x S&P 500 (model)': etfs['2x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x S&P 500 (model)': etfs['2x_sp500_us'],
    },
    "S&P 500 (reference: ULPIX)",
    overlapping_only = True,
)


# Now the error curve ist mostly flat and not growing over time. There are several huge spikes like the on on 13th of March 2020. On that day the S&P 500 increased quite a lot, while the ULPIX did not increase. This can also be seen on other platforms, when comparing ULPIX with S&P 500 on that day. So, we can assume, that those are the tracking errors of the fund. Apart from that, especially the mid- and longterm trend seems to be fine for our model. 

# Let's download the UPRO data and model this LETF.

# In[22]:


upro = download_from_yahoo("UPRO", adjust=True)
upro


# In[23]:


n = normalize(upro, assets['sp500+div'])
draw_growth_chart(
    {
        'UPRO (S&P 500 x3)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500 (reference: UPRO)",
    overlapping_only = True,
)


# Obvoisly the UPRO has outperformed the S&P 500 in the bullish market phase after the financial crisis. 

# In[24]:


etfs['3x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.91, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[25]:


n = normalize(upro, etfs['3x_sp500_us'])
draw_growth_chart(
    {
        'UPRO (S&P 500 x3)': n,
        '3x S&P 500 (model)': etfs['3x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x S&P 500 (model)': etfs['3x_sp500_us'],
    },
    "S&P 500 (reference: UPRO)",
    overlapping_only = True,
)


# Also here, the model is in generel following the UPRO, but it diverges over time from it. So we also set here an adjustment factor of -1.0%.

# In[26]:


etfs['3x_sp500_us'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.91, 
    adjustment_factor=-1.0,
    percent=100
), percent=1)
etfs


# In[27]:


n = normalize(upro, etfs['3x_sp500_us'])
draw_growth_chart(
    {
        'UPRO (S&P 500 x3)': n,
        '3x S&P 500 (model)': etfs['3x_sp500_us'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x S&P 500 (model)': etfs['3x_sp500_us'],
    },
    "S&P 500 (reference: UPRO)",
    overlapping_only = True,
)


# This makes the model stable, so we now also found a model for the UPRO. In the next step, we focus on leverage ETFs from europe for the S&P 500. 
# 
# Here we take: 
# * S&P 500 1x => iShares Core S&P 500 UCITS ETF (ticker `SXR8`)
# * S&P 500 2x => S&P 500 2x Leveraged Daily Swap UCITS ETF (ticker `DBPG`)
# * S&P 500 3x => WisdomTree S&P 500 3x Daily Leveraged (ticker `3USL`)*
# 
# __*) Keep in mind that the WisdomTree is not an ETF, but an ETN. This includes a higher risk when the emittent gets bunkrupt.__
# 
# Since all those ETP prices are given in EUR, we have to calculate the USD price out of it, before we can use it to compare our modelling. The following function will help us with that.

# In[28]:


eurusd = download_from_yahoo("EURUSD=X")
eurusd

def to_usd(data):
    assert min(data.index) >= min(eurusd.index)
    assert max(data.index) <= max(eurusd.index)
    return data * eurusd.loc[min(data.index):max(data.index)]


# In[29]:


sxr8 = to_usd(download_from_yahoo("SXR8.DE", adjust=True))
sxr8


# In[30]:


n = normalize(sxr8, assets['sp500+div'])
draw_growth_chart(
    {
        'SXR8 (S&P 500 x1)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)


# We can see a huge glitch in the ETF at the 24.10.2010. Due to this glitch the ETF lacks behinds the real index. Since other exchange places like Frankfurt oder Milan does not show this glitch (but does not provide data for the years before), we ignore it and just take the ETF from beginning of 2011 for comparison.

# In[31]:


sxr8 = to_usd(download_from_yahoo("SXR8.DE", adjust=True)).loc['2011':]
sxr8


# In[32]:


n = normalize(sxr8, assets['sp500+div'])
draw_growth_chart(
    {
        'SXR8 (S&P 500 x1)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)


# Now both time-lines are following each-other, but the real index outperforms over time the ETF, which is logical because of the expense ratio. Now we create the model for this ETF. As expense ratio, we set a value of 0,07% per year.

# In[33]:


etfs['1x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    er=0.07, 
    percent=100,
    adjustment_factor=0,
), percent=1)
etfs


# In[34]:


n = normalize(sxr8, etfs['1x_sp500_eu'])
draw_growth_chart(
    {
        'SXR8 (S&P 500 x1)': n,
        '1x S&P 500 (model)': etfs['1x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x S&P 500 (model)': etfs['1x_sp500_eu'],
    },
    "S&P 500 (reference: SXR8)",
    overlapping_only = True,
)


# So even with applying an expense ration of 0.07%, our model still diverges from the real ETF. To compensate this, we introduce an adjustment-factor of -0.3% per year.

# In[35]:


etfs['1x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    er=0.07, 
    percent=100,
    adjustment_factor=-0.3,
), percent=1)
etfs


# In[37]:


n = normalize(sxr8, etfs['1x_sp500_eu'])
draw_growth_chart(
    {
        'SXR8 (S&P 500 x1)': n,
        '1x S&P 500 (model)': etfs['1x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x S&P 500 (model)': etfs['1x_sp500_eu'],
    },
    "S&P 500 (reference: SXR8)",
    overlapping_only = True,
)


# Now we just see a lot of noise, which probably comes from the EUR to USD translation, but the mean value of the curve is flat. Thus our model now tracks the real ETF very good. 
# 
# As next step we investigate in the DBPG as 2x leverages S&P 500 ETF.

# In[38]:


dbpg = to_usd(download_from_yahoo("DBPG.DE", adjust=True))
dbpg


# In[39]:


n = normalize(dbpg, assets['sp500+div'])
draw_growth_chart(
    {
        'DBPG (S&P 500 x2)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)


# Here again, we see a lot of glitches in the chart until mid of 2011. Thus we will start our comparison just from 2012.

# In[40]:


dbpg = to_usd(download_from_yahoo("DBPG.DE", adjust=True)).loc['2012':]
dbpg


# In[41]:


n = normalize(dbpg, assets['sp500+div'])
draw_growth_chart(
    {
        'DBPG (S&P 500 x2)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)


# Now we apply our model with leverage factor 2 and an expense ratio of 0.6%.

# In[42]:


etfs['2x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.6, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[43]:


n = normalize(dbpg, etfs['2x_sp500_eu'])
draw_growth_chart(
    {
        'DBPG (S&P 500 x2)': n,
        '2x S&P 500 (model)': etfs['2x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x S&P 500 (model)': etfs['2x_sp500_eu'],
    },
    "S&P 500 (reference: DBPG)",
    overlapping_only = True,
)


# Our model is following the ETF, but is diverging. Thus we introduce also here an adjutment factor of -1.2%.

# In[44]:


etfs['2x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.6, 
    adjustment_factor=-1.2,
    percent=100
), percent=1)
etfs


# In[45]:


n = normalize(dbpg, etfs['2x_sp500_eu'])
draw_growth_chart(
    {
        'DBPG (S&P 500 x2)': n,
        '2x S&P 500 (model)': etfs['2x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x S&P 500 (model)': etfs['2x_sp500_eu'],
    },
    "S&P 500 (reference: DBPG)",
    overlapping_only = True,
)


# Now our model is following the ETF quite well with a flat error curve. 
# 
# Time to focus on the 3x leveraged ETN 3USL.

# In[46]:


usl3 = to_usd(download_from_yahoo("3USL.MI", adjust=True))
usl3


# In[47]:


n = normalize(usl3, assets['sp500+div'])
draw_growth_chart(
    {
        '3USL (S&P 500 x3)': n,
        'S&P 500 (incl. dividends)': assets['sp500+div'],
    },
    "S&P 500",
    overlapping_only = True,
)


# In[48]:


etfs['3x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.75, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[49]:


n = normalize(usl3, etfs['3x_sp500_eu'])
draw_growth_chart(
    {
        '3USL (S&P 500 x3)': n,
        '3x S&P 500 (model)': etfs['3x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x S&P 500 (model)': etfs['3x_sp500_eu'],
    },
    "S&P 500 (reference: 3USL)",
    overlapping_only = True,
)


# For this ETN we introduce an adjustment factor of -2.75%. This is a very huge factor, especially compared to the UPRO ETF, which just needed a factor of -1%.

# In[50]:


etfs['3x_sp500_eu'] = calc_growth(calc_letf(
    assets_daily_returns['sp500+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.75, 
    adjustment_factor=-2.75,
    percent=100
), percent=1)
etfs


# In[51]:


n = normalize(usl3, etfs['3x_sp500_eu'])
draw_growth_chart(
    {
        '3USL (S&P 500 x3)': n,
        '3x S&P 500 (model)': etfs['3x_sp500_eu'],
    },
    "S&P 500",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x S&P 500 (model)': etfs['3x_sp500_eu'],
    },
    "S&P 500 (reference: 3USL)",
    overlapping_only = True,
)


# Also here our model is now following the ETN.

# ## Nasdaq-100 (L)ETFs
# 
# After modelling all S&P 500 ETFs, we can now model ETFs for the Nasdaq-100. Also here we first chose 3 US ETFs for comparison:
# 
# * Nasdaq-100 x1 => QQQ (+ dividends)
# * Nasdaq-100 x2 => QLD (+ dividends)
# * Nasdaq-100 x3 => TQQQ (+ dividends)
# 

# In[52]:


qqq = download_from_yahoo("QQQ", adjust=True)
qqq


# In[53]:


n = normalize(qqq, assets['ndx100+div'])
draw_growth_chart(
    {
        'QQQ (Nasdaq-100 x1)': n,
        'Nasdaq-100': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# As usual the pure index is outperforming the ETF slightly, due to the costs. So we start modelling the ETF with an expense ratio of 0.2% per year.

# In[54]:


etfs['1x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.2, 
    adjustment_factor=-0.00,
    percent=100
), percent=1)
etfs


# In[55]:


n = normalize(qqq, etfs['1x_ndx100_us'])
draw_growth_chart(
    {
        'QQQ (Nasdaq-100 1x)': n,
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_us'],
    },
    "Nasdaq-100 (reference: QQQ)",
    overlapping_only = True,
)


# We see a strong noise in the beginning of the ETF until 2005. After this date the error curve is very flat and the average error is much below 1%. We can optimize it slightly by settings an adjustment factor of -0.01%.

# In[56]:


etfs['1x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.2, 
    adjustment_factor=-0.01,
    percent=100
), percent=1)
etfs


# In[57]:


n = normalize(qqq, etfs['1x_ndx100_us'])
draw_growth_chart(
    {
        'QQQ (Nasdaq-100 1x)': n,
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_us'],
    },
    "Nasdaq-100 (reference: QQQ)",
    overlapping_only = True,
)


# As next step we model a 2x leverages ETF and compare it with QLD.

# In[58]:


qld = download_from_yahoo("QLD", adjust=True)
qld


# In[59]:


n = normalize(qld, assets['ndx100+div'])
draw_growth_chart(
    {
        'QLD (Nasdaq-100 x2)': n,
        'Nasdaq-100': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# We model this ETF with an expense ratio of 0.95%.

# In[60]:


etfs['2x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-0.00,
    percent=100
), percent=1)
etfs


# In[61]:


n = normalize(qld, etfs['2x_ndx100_us'])
draw_growth_chart(
    {
        'QLD (Nasdaq-100 2x)': n,
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_us'],
    },
    "Nasdaq-100 (reference: QLD)",
    overlapping_only = True,
)


# Here we use an adjustment factor of -0.55%

# In[62]:


etfs['2x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-0.55,
    percent=100
), percent=1)
etfs


# In[63]:


n = normalize(qld, etfs['2x_ndx100_us'])
draw_growth_chart(
    {
        'QLD (Nasdaq-100 2x)': n,
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_us'],
    },
    "Nasdaq-100 (reference: QLD)",
    overlapping_only = True,
)


# Is is very hard to find an adjustment factor, which keeps the error curve flat. It seems, that the expense ratio or costs of this ETF have changed over time. But with an adjustment factor of -0.55% the curve looks more or less reasonable and is slightly underperforming the ETF, which is also not too bad for a backtest. 
# 
# The last U.S. ETF we look for is TQQQ.

# In[64]:


tqqq = download_from_yahoo("TQQQ", adjust=True)
tqqq


# In[65]:


n = normalize(tqqq, assets['ndx100+div'])
draw_growth_chart(
    {
        'TQQQ (Nasdaq-100 x3)': n,
        'Nasdaq-100': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# For our first modelling of the TQQQ, we set the expense ratio to 0.96%.

# In[66]:


etfs['3x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.95, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[67]:


n = normalize(tqqq, etfs['3x_ndx100_us'])
draw_growth_chart(
    {
        'TQQQ (Nasdaq-100 3x)': n,
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_us'],
    },
    "Nasdaq-100 (reference: TQQQ)",
    overlapping_only = True,
)


# And to flatten the error curve, we set an adjustment-factor of -1.1%.

# In[68]:


etfs['3x_ndx100_us'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.95, 
    adjustment_factor=-1.1,
    percent=100
), percent=1)
etfs


# In[69]:


n = normalize(tqqq, etfs['3x_ndx100_us'])
draw_growth_chart(
    {
        'TQQQ (Nasdaq-100 3x)': n,
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_us'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_us'],
    },
    "Nasdaq-100 (reference: TQQQ)",
    overlapping_only = True,
)


# Also here it is hard to get a flat curve, but the overall error is with maximum -3% not so bad.
# 
# Now, we can focus on european ETFs for the Nasdaq-100. The following ETFs can be chosen as reference:
# * Nasdaq-100 1x => PowerShares EQQQ Nasdaq-100 UCITS ETF (`EQQQ`)
# * Nasdaq-100 2x => Lyxor Nasdaq-100 Daily (2x) Leveraged UCITS ETF (`L8I7`)
# * Nasdaq-100 3x => WisdomTree NASDAQ 100 3x Daily Leveraged (`QQQ3`)*
# 
# __*) Keep in mind that the WisdomTree is not an ETF, but an ETN. This includes a higher risk when the emittent gets bunkrupt.__
# 
# Again all ETPs are trades in EUR, thus we have to transform the price first to USD before we can work with it.
# 
# Let's start with EQQQ.

# In[70]:


eqqq = to_usd(download_from_yahoo("EQQQ.MI", adjust=True))
eqqq 


# In[71]:


n = normalize(eqqq, assets['ndx100+div'])
draw_growth_chart(
    {
        'EQQQ (Nasdaq-100 1x)': n,
        'Nasdaq-100 (incl. dividends)': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# For modelling this ETF, we use an expense ratio of 0,33%.

# In[72]:


etfs['1x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.33, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[73]:


n = normalize(eqqq, etfs['1x_ndx100_eu'])
draw_growth_chart(
    {
        'EQQQ (Nasdaq-100 1x)': n,
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: EQQQ)",
    overlapping_only = True,
)


# Furthermore we apply an adjustment-factor of -0.8%.

# In[74]:


etfs['1x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.33, 
    adjustment_factor=-0.8,
    percent=100
), percent=1)
etfs


# In[75]:


n = normalize(eqqq, etfs['1x_ndx100_eu'])
draw_growth_chart(
    {
        'EQQQ (Nasdaq-100 1x)': n,
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Nasdaq-100 (model)': etfs['1x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: EQQQ)",
    overlapping_only = True,
)


# Now the curve is reasonable flat and we can go on with the L8I7.

# In[76]:


l8i7 = to_usd(download_from_yahoo("L8I7.DE", adjust=True))
l8i7


# In[77]:


n = normalize(l8i7, assets['ndx100+div'])
draw_growth_chart(
    {
        'L8I7 (Nasdaq-100 2x)': n,
        'Nasdaq-100 (incl. dividends)': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# For this ETF we have extremly little history. It is very hard to reasonably fit the curves together, but this is the only ETF, which I found on europe for 2x Nasdaq-100. Thus we have to try our best here. We start with an expense ratio of 0.6%. 

# In[78]:


etfs['2x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.6, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[79]:


n = normalize(l8i7, etfs['2x_ndx100_eu'])
draw_growth_chart(
    {
        'L8I7 (Nasdaq-100 2x)': n,
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: L8I7)",
    overlapping_only = True,
)


# We already have a very good fit. But we can slightly improve it by using an adjustment-factor of -0.2%.

# In[80]:


etfs['2x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.6, 
    adjustment_factor=-0.2,
    percent=100
), percent=1)
etfs


# In[81]:


n = normalize(l8i7, etfs['2x_ndx100_eu'])
draw_growth_chart(
    {
        'L8I7 (Nasdaq-100 2x)': n,
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Nasdaq-100 (model)': etfs['2x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: L8I7)",
    overlapping_only = True,
)


# Let's keep it like this and go on with the ETN QQQ3 from WisdomTree.

# In[82]:


qqq3 = download_from_investing("boost-nasdaq-100-3x-leverage", start_date="2014-02-26", category="etfs")
qqq3 = reindex_and_fill(qqq3, min(qqq3.index), max(qqq3.index), freq="D")
qqq3 = to_usd(qqq3)
qqq3


# In[83]:


n = normalize(qqq3, assets['ndx100+div'])
draw_growth_chart(
    {
        'QQQ3 (Nasdaq-100 3x)': n,
        'Nasdaq-100 (incl. dividends)': assets['ndx100+div'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)


# For our model we start with an expense ratio of 0.75%.

# In[84]:


etfs['3x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.75, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[85]:


n = normalize(qqq3, etfs['3x_ndx100_eu'])
draw_growth_chart(
    {
        'QQQ3 (Nasdaq-100 3x)': n,
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: QQQ3)",
    overlapping_only = True,
)


# To flatten the curve we also add an adjutment-factor of -2.1%. This is again, quite high, compared to the other ETFs, but we have seen the same effect with the WisdomTree 3x S&P 500 ETN. 

# In[86]:


etfs['3x_ndx100_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ndx100+div'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.75, 
    adjustment_factor=-2.1,
    percent=100
), percent=1)
etfs


# In[87]:


n = normalize(qqq3, etfs['3x_ndx100_eu'])
draw_growth_chart(
    {
        'QQQ3 (Nasdaq-100 3x)': n,
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_eu'],
    },
    "Nasdaq-100",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Nasdaq-100 (model)': etfs['3x_ndx100_eu'],
    },
    "Nasdaq-100 (reference: QQQ3)",
    overlapping_only = True,
)


# ## Gold ETFs
# 
# The next step is to model Gold ETFs with and without leverage factor. For the U.S. we have the following ETFs available:
# 
# * 1x Gold => SPDR Gold Shares (`GLD`)
# * 2x Gold => ProShares Ultra Gold (`UGL`)
# 
# It seems, that there is not 3x leveraged Gold ETF available.

# In[88]:


gld = download_from_yahoo("GLD", adjust=True)
gld


# In[89]:


n = normalize(gld, assets['gold'])
draw_growth_chart(
    {
        'GLD (Gold 1x)': n,
        'Gold': assets['gold'],
    },
    "Gold",
    overlapping_only = True,
)


# As we can see, there is just a small difference between the real gold-price and the gold ETF. We now apply our model with an expense ratio of 0.4%.

# In[90]:


etfs['1x_gold_us'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.4, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[92]:


n = normalize(gld, etfs['1x_gold_us'])
draw_growth_chart(
    {
        'GLD (Gold 1x)': n,
        '1x Gold (model)': etfs['1x_gold_us'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Gold (model)': etfs['1x_gold_us'],
    },
    "Gold (reference: GLD)",
    overlapping_only = True,
)


# Except of the noise, we have a very flat error curve, so we don't need to add an adjustment-factor to this model.
# 
# Let's continue with UGL as 2x leveraged gold ETF.

# In[93]:


ugl = download_from_yahoo("UGL", adjust=True)
ugl


# In[94]:


n = normalize(ugl, assets['gold'])
draw_growth_chart(
    {
        'UGL (Gold 2x)': n,
        'Gold': assets['gold'],
    },
    "Gold",
    overlapping_only = True,
)


# For the model, we chose an expense ratio of 0.95%.

# In[95]:


etfs['2x_gold_us'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[96]:


n = normalize(ugl, etfs['2x_gold_us'])
draw_growth_chart(
    {
        'UGL (Gold 2x)': n,
        '2x Gold (model)': etfs['2x_gold_us'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Gold (model)': etfs['2x_gold_us'],
    },
    "Gold (reference: UGL)",
    overlapping_only = True,
)


# Furthermore, we add an adjustment-factor of -2% to it.

# In[98]:


etfs['2x_gold_us'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-2.0,
    percent=100
), percent=1)
etfs


# In[99]:


n = normalize(ugl, etfs['2x_gold_us'])
draw_growth_chart(
    {
        'UGL (Gold 2x)': n,
        '2x Gold (model)': etfs['2x_gold_us'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x Gold (model)': etfs['2x_gold_us'],
    },
    "Gold (reference: UGL)",
    overlapping_only = True,
)


# The introduced adjustment-factor for our 2x Gold ETF is very high, especially compared to the other U.S. ETFs. However it is well known, that Gold and Silver ETFs have a huge tracking error, due to the usage of Swaps. See http://www.columbia.edu/~klg2138/FieldsPaper_v4.pdf for more details. 

# As next step we look for europe Gold ETCs. Here the following are available:
# 
# * 1x Gold => Invesco Physical Gold ETC (`SGLD`)
# * 3x Gold => WisdomTree Gold 3x Daily Leveraged (`3GOL`)
# 
# I was not able to find a 2x leveraged ETC for Gold in europe.
# 
# We start with SGLD and since the data has some glitches at the end of 2021, we just take the data until beginning of November 2021. 

# In[100]:


sgld = download_from_yahoo("SGLD.L", adjust=True).loc[:'2021-01-01']
sgld


# In[101]:


n = normalize(sgld, assets['gold'])
draw_growth_chart(
    {
        'SGLD (Gold 1x)': n,
        'Gold': assets['gold'],
    },
    "Gold",
    overlapping_only = True,
)


# We model this ETC with an expense ratio of 0.12%.

# In[102]:


etfs['1x_gold_eu'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.12, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[103]:


n = normalize(gld, etfs['1x_gold_eu'])
draw_growth_chart(
    {
        'SGLD (Gold 1x)': n,
        '1x Gold (model)': etfs['1x_gold_eu'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Gold (model)': etfs['1x_gold_eu'],
    },
    "Gold (reference: SGLD)",
    overlapping_only = True,
)


# The error curve is still diverging, thus we introduce an adjustment-factor of -0.28%

# In[104]:


etfs['1x_gold_eu'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.12, 
    adjustment_factor=-0.28,
    percent=100
), percent=1)
etfs


# In[105]:


n = normalize(gld, etfs['1x_gold_eu'])
draw_growth_chart(
    {
        'SGLD (Gold 1x)': n,
        '1x Gold (model)': etfs['1x_gold_eu'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x Gold (model)': etfs['1x_gold_eu'],
    },
    "Gold (reference: SGLD)",
    overlapping_only = True,
)


# With those settings we reach a quite good error curve and we can proceed with 3GOL. 

# In[106]:


gol3 = to_usd(download_from_yahoo("3GOL.MI", adjust=True))
gol3


# In[107]:


n = normalize(gol3, assets['gold'])
draw_growth_chart(
    {
        '3GOL (Gold 3x)': n,
        'Gold': assets['gold'],
    },
    "Gold",
    overlapping_only = True,
)


# We start our modeling here with an expense ratio of 0.99%.

# In[108]:


etfs['3x_gold_eu'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.99, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[109]:


n = normalize(gol3, etfs['3x_gold_eu'])
draw_growth_chart(
    {
        '3GOL (Gold 3x)': n,
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold (reference: 3GOL)",
    overlapping_only = True,
)


# In the error curve, we can see several glitches, starting of 2014. Thus for further tests, we will ignore the data before April 2014.

# In[110]:


gol3 = gol3.loc['2014-04-01':]


# In[111]:


n = normalize(gol3, etfs['3x_gold_eu'])
draw_growth_chart(
    {
        '3GOL (Gold 3x)': n,
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold (reference: 3GOL)",
    overlapping_only = True,
)


# Now we introduce an adjustment-factor of -4%, which is very huge, but it is in-sync with other WisdomTree ETNs and also with the Gold-ETFs from U.S.

# In[112]:


etfs['3x_gold_eu'] = calc_growth(calc_letf(
    assets_daily_returns['gold'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.99, 
    adjustment_factor=-4.0,
    percent=100
), percent=1)
etfs


# In[113]:


n = normalize(gol3, etfs['3x_gold_eu'])
draw_growth_chart(
    {
        '3GOL (Gold 3x)': n,
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x Gold (model)': etfs['3x_gold_eu'],
    },
    "Gold (reference: 3GOL)",
    overlapping_only = True,
)


# It seems, that it is very hard to model leveraged Gold ETFs/ETCs. But for a rough exstimation during our backtest, it should be ok.

# ## Short Term Treasury Bonds
# 
# In the U.S. the following ETFs are available:
#     
#     * 1x STT => iShares 1-3 Year Treasury Bond ETF (`SHY`)
# 
# I was not able to find a leveraged ETF for STT. Thus we will just introduce artificial leveraged ETFs for Short Term Treasury bonds with adjustment-factors that seems to be true for normal ETFs. 

# In[114]:


shy = download_from_yahoo("SHY", adjust=True)
shy


# In[115]:


n = normalize(shy, assets['stt_us'])
draw_growth_chart(
    {
        'SHY (STT 1x)': n,
        'STT (US, 1-3 years)': assets['stt_us'],
    },
    "Short Term Treasuries",
    overlapping_only = True,
)


# We model the ETF with an expense ratio of 0.15%.

# In[116]:


etfs['1x_stt_us'] = calc_growth(calc_letf(
    assets_daily_returns['stt_us'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.15, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[117]:


n = normalize(shy, etfs['1x_stt_us'])
draw_growth_chart(
    {
        'SHY (STT 1x)': n,
        '1x STT (model)': etfs['1x_stt_us'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x STT (model)': etfs['1x_stt_us'],
    },
    "Short Term Treasury Bonds (reference: SHY)",
    overlapping_only = True,
)


# Furthermore, we add an negative adjustment-factor of -0.15%

# In[118]:


etfs['1x_stt_us'] = calc_growth(calc_letf(
    assets_daily_returns['stt_us'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.15, 
    adjustment_factor=-0.15,
    percent=100
), percent=1)
etfs


# In[119]:


n = normalize(shy, etfs['1x_stt_us'])
draw_growth_chart(
    {
        'SHY (STT 1x)': n,
        '1x STT (model)': etfs['1x_stt_us'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x STT (model)': etfs['1x_stt_us'],
    },
    "Short Term Treasury Bonds (reference: SHY)",
    overlapping_only = True,
)


# The error is quite low. Keep in mind, that the treasury bond data is completly simulated. For such simulated data the error is really excellent! 

# For a 2x STT ETF, we just assume an expense ratio of 0.95% as we have seen with many leveraged ETFs and an adjustment-factor of -0.5%.

# In[116]:


etfs['2x_stt_us'] = calc_growth(calc_letf(
    assets_daily_returns['stt_us'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-0.5,
    percent=100
), percent=1)
etfs


# In[117]:


n = normalize(shy, etfs['2x_stt_us'])
draw_growth_chart(
    {
        'SHY (STT 1x)': n,
        '2x STT (model)': etfs['2x_stt_us'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)


# As you can see the assumed costs, which are in sync with other leveraged ETFs are high enough to completely destroy the performance of such an ETF. Maybe this is the reason, why no leveraged STT ETFs are available at all?
# 
# We also simulate a 3x leveraged ETF, where we assume an expense ratio of 0.95% and an adjustment-factor of -1.0%.

# In[118]:


etfs['3x_stt_us'] = calc_growth(calc_letf(
    assets_daily_returns['stt_us'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.95, 
    adjustment_factor=-1.0,
    percent=100
), percent=1)
etfs


# In[119]:


n = normalize(shy, etfs['3x_stt_us'])
draw_growth_chart(
    {
        'SHY (STT 1x)': n,
        '3x STT (model)': etfs['3x_stt_us'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)


# And also here we can see, that the performance gain of the leverage factor is not high enough to compendate the costs.

# For europe we have the following ETFs available:
# * 1x STT => iShares $ Treasury Bond 1-3yr UCITS ETF (`IBTA`)
# 
# Also for europe, I was not able to find any leveraged ETF. 

# In[120]:


ibta = download_from_yahoo("IBTA.L", adjust=True)
ibta


# In[121]:


n = normalize(ibta, assets['stt_eu'])
draw_growth_chart(
    {
        'IBTA (STT 1x)': n,
        'STT (EU, 1-3 years)': assets['stt_eu'],
    },
    "Short Term Treasuries",
    overlapping_only = True,
)


# We model this ETF with an expense ratio of 0.07%.

# In[122]:


etfs['1x_stt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['stt_eu'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.07, 
    adjustment_factor=0.00,
    percent=100
), percent=1)
etfs


# In[123]:


n = normalize(ibta, etfs['1x_stt_eu'])
draw_growth_chart(
    {
        'IBTA (STT 1x)': n,
        '1x STT (model)': etfs['1x_stt_eu'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x STT (model)': etfs['1x_stt_eu'],
    },
    "Short Term Treasury Bonds (reference: IBTA)",
    overlapping_only = True,
)


# Also here the error is very low with maximum 1%. 
# 
# Here again, we model now a 2x leveraged ETF with 0.95% expense ratio and -0.5% adjustment factor.

# In[124]:


etfs['2x_stt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['stt_eu'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-0.5,
    percent=100
), percent=1)
etfs


# In[125]:


n = normalize(ibta, etfs['2x_stt_eu'])
draw_growth_chart(
    {
        'IBTA (STT 1x)': n,
        '2x STT (model)': etfs['2x_stt_eu'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)


# And as we already have seen it for the US ETF, the leveraged version underperfroms the unleveraged version.
# 
# But we also model a 3x leveraged ETF with 0.95% expense ratio and -1.0% adjustment-factor.

# In[126]:


etfs['3x_stt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['stt_eu'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-1.0,
    percent=100
), percent=1)
etfs


# In[127]:


n = normalize(ibta, etfs['3x_stt_eu'])
draw_growth_chart(
    {
        'IBTA (STT 1x)': n,
        '3x STT (model)': etfs['3x_stt_eu'],
    },
    "Short Term Treasury Bonds",
    overlapping_only = True,
)


# And the performance of this version is even worse. 

# ## Intermediate Term Treasury Bonds
# 
# For the intermediate term treasury bonds, we can find different ETFs with all leverage factors. So we chose for our modeling the following ones:
# 
# * 1x ITT => Vanguard Intermediate-Term Treasury Fund Investor Shares (`VFITX`)
# * 2x ITT => ProShares Ultra 7-10 Year Treasury (`UST`)
# * 3x ITT => Direxion Daily 7-10 Year Treasury Bull 3X Shares (`TYD`)
# 
# Keep in mind, that our ITT (US) data was modelled to fit to a maturity duration between 5-10 years. Thus the 2x and 3x leverage ETFs do not fit exaclty to this.

# In[126]:


vfitx = download_from_yahoo("VFITX", adjust=True)
vfitx


# In[127]:


n = normalize(vfitx, assets['itt_us'])
draw_growth_chart(
    {
        'VFITX (ITT 1x)': n,
        'ITT (US, 10-5 years)': assets['itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# Let's model the 1x leveraged ETF with an expension rate of 0.20%.

# In[128]:


etfs['1x_itt_us'] = calc_growth(calc_letf(
    assets_daily_returns['itt_us'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.2, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[129]:


n = normalize(vfitx, etfs['1x_itt_us'])
draw_growth_chart(
    {
        'VFITX (ITT 1x)': n,
        '1x ITT (model)': etfs['1x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x ITT (model)': etfs['1x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: VFITX)",
    overlapping_only = True,
)


# Our model is still diverging from the ETF, so we add an adjustment factor of -0.5%.

# In[130]:


etfs['1x_itt_us'] = calc_growth(calc_letf(
    assets_daily_returns['itt_us'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.2, 
    adjustment_factor=-0.5,
    percent=100
), percent=1)
etfs


# In[131]:


n = normalize(vfitx, etfs['1x_itt_us'])
draw_growth_chart(
    {
        'VFITX (ITT 1x)': n,
        '1x ITT (model)': etfs['1x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x ITT (model)': etfs['1x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: VFITX)",
    overlapping_only = True,
)


# Now we have a quite good fit, thus we can focus on UST.

# In[132]:


ust = download_from_yahoo("UST", adjust=True)
ust


# In[133]:


n = normalize(ust, assets['itt_us'])
draw_growth_chart(
    {
        'UST (ITT 2x)': n,
        'ITT (US, 10-5 years)': assets['itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# UST has an expense ratio of 0.95%.

# In[134]:


etfs['2x_itt_us'] = calc_growth(calc_letf(
    assets_daily_returns['itt_us'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=0,
    percent=100
), percent=1)
etfs


# In[135]:


n = normalize(ust, etfs['2x_itt_us'])
draw_growth_chart(
    {
        'UST (ITT 2x)': n,
        '2x ITT (model)': etfs['2x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x ITT (model)': etfs['2x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: UST)",
    overlapping_only = True,
)


# As we can see our ITT fund is underformorming. The reason for this difference is most probably the different average maturity duration between our model and the real ETF. Thus we chose the european ITT variant, which we modelled with band between 7-10 years and add small positive adjustment factor of 0.1%.

# In[136]:


etfs['2x_itt_us'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=0.1,
    percent=100
), percent=1)
etfs


# In[137]:


n = normalize(ust, etfs['2x_itt_us'])
draw_growth_chart(
    {
        'UST (ITT 2x)': n,
        '2x ITT (model)': etfs['2x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x ITT (model)': etfs['2x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: UST)",
    overlapping_only = True,
)


# Now we have a quite good fit.
# 
# As last example we look at TYD and here we directly compare it to the `itt_eu` model, because of the better fitting maturity duration.

# In[138]:


tyd = download_from_yahoo("TYD", adjust=True)
tyd


# In[139]:


n = normalize(tyd, assets['itt_eu'])
draw_growth_chart(
    {
        'TYD (ITT 2x)': n,
        'ITT (EU, 10-7 years)': assets['itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# We create here a model with an expense ration of 1.09%.

# In[140]:


etfs['3x_itt_us'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=1.09, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[141]:


n = normalize(tyd, etfs['3x_itt_us'])
draw_growth_chart(
    {
        'TYD (ITT 3x)': n,
        '3x ITT (model)': etfs['3x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x ITT (model)': etfs['3x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: TYD)",
    overlapping_only = True,
)


# As we can see, the error is mostly stable. Just in the years before 2011, the error starts increasing a lot and afterwards it is keeping its level. If we would not try to fit the curve with an adjustment factor, we would just introduce a huge negative drift to our model. Instead we look at the curve just from 2011 and keep away the years before from comparison. Maybe the cost structure was much higher in those years, but without historical data, we cannot check this. 

# In[142]:


tyd = tyd.loc['2011':]


# In[143]:


n = normalize(tyd, etfs['3x_itt_us'])
draw_growth_chart(
    {
        'TYD (ITT 3x)': n,
        '3x ITT (model)': etfs['3x_itt_us'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x ITT (model)': etfs['3x_itt_us'],
    },
    "Intermidiate Term Treasury Bonds (reference: TYD)",
    overlapping_only = True,
)


# We can see, that the error is now mostly constant (there is a lot of noise and a huge glitch in 2014). 

# In europe, we have the following fitting ETFs available:
# 
# * 1x ITT => iShares $ Treasury Bd 7-10y ETF USD Acc (`SXRM`)
# * 3x ITT => WisdomTree US Treasuries 10Y 3x Daily Leveraged (`3TYL`)
# 
# For the 2x ITT, we just copy the values from the US ETF. 

# In[144]:


sxrm = download_from_yahoo("SXRM.DE", adjust=True)
sxrm


# In[145]:


n = normalize(sxrm, assets['itt_eu'])
draw_growth_chart(
    {
        'SXRM (ITT 1x)': n,
        'ITT (EU, 10-7 years)': assets['itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# We see huge glitches before 2012, thus we just take the data afterwards into account. Furthermore we model the ETF with an expense ratio of 0.07%.

# In[146]:


sxrm = sxrm.loc['2012':]


# In[147]:


etfs['1x_itt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.07, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[148]:


n = normalize(sxrm, etfs['1x_itt_eu'])
draw_growth_chart(
    {
        'SXRM (ITT 1x)': n,
        '1x ITT (model)': etfs['1x_itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x ITT (model)': etfs['1x_itt_eu'],
    },
    "Intermidiate Term Treasury Bonds (reference: SXRM)",
    overlapping_only = True,
)


# We still diverge from the ETF, thus we introduce an adjustment-factor of -0.2%.

# In[149]:


etfs['1x_itt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.07, 
    adjustment_factor=-0.15,
    percent=100
), percent=1)
etfs


# In[150]:


n = normalize(sxrm, etfs['1x_itt_eu'])
draw_growth_chart(
    {
        'SXRM (ITT 1x)': n,
        '1x ITT (model)': etfs['1x_itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x ITT (model)': etfs['1x_itt_eu'],
    },
    "Intermidiate Term Treasury Bonds (reference: SXRM)",
    overlapping_only = True,
)


# The error curve is now quite float and the error is low. So we focus on the leveraged ETFs. Since there is no europeen 2x leveraged ETF available, we just copy the data from the US ETF (which has been modelled with europeen ITT data anyway) and directly focus on 3TYL as 3x leveraged ITT ETN. 

# In[151]:


etfs['2x_itt_eu'] = etfs['2x_itt_us'].copy()


# In[152]:


tyl3 = to_usd(download_from_yahoo("3TYL.L", adjust=True))
tyl3


# In[153]:


n = normalize(tyl3, assets['itt_eu'])
draw_growth_chart(
    {
        '3TYL (ITT 2x)': n,
        'ITT (EU, 10-7 years)': assets['itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# As we can see the data-quality is very bad. We have a huge spike in Nov. 2021 and the data before Aug. 2017 does also not look correct. So we have to restrict the comparison periode to Aug. 2017 until Nov. 2021.

# In[154]:


tyl3 = tyl3.loc['2017-08-01':'2021-11-01']


# In[155]:


n = normalize(tyl3, assets['itt_eu'])
draw_growth_chart(
    {
        '3TYL (ITT 2x)': n,
        'ITT (EU, 10-7 years)': assets['itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)


# It seems that there are still glitches in the year 2018 with long periodes without data, but we will now model our ETF and then look if we can use the data for comparison. As expense ratio we chose a value of 0.3%.

# In[156]:


etfs['3x_itt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.3, 
    adjustment_factor=-0.0,
    percent=100
), percent=1)
etfs


# In[157]:


n = normalize(tyl3, etfs['3x_itt_eu'])
draw_growth_chart(
    {
        '3TYL (ITT 3x)': n,
        '3x ITT (model)': etfs['3x_itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x ITT (model)': etfs['3x_itt_eu'],
    },
    "Intermidiate Term Treasury Bonds (reference: 3TYL)",
    overlapping_only = True,
)


# To flatten the curve, we add an adjustment-factor of -2.5%, which is a high factor, but we already know that the WidomTree ETNs have very high tracking errors.

# In[158]:


etfs['3x_itt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['itt_eu'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=0.3, 
    adjustment_factor=-2.5,
    percent=100
), percent=1)
etfs


# In[159]:


n = normalize(tyl3, etfs['3x_itt_eu'])
draw_growth_chart(
    {
        '3TYL (ITT 3x)': n,
        '3x ITT (model)': etfs['3x_itt_eu'],
    },
    "Intermidiate Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x ITT (model)': etfs['3x_itt_eu'],
    },
    "Intermidiate Term Treasury Bonds (reference: 3TYL)",
    overlapping_only = True,
)


# The fit is not perfect, but our model mostly follows the reference. 

# ## Long Term Treasury Bonds
# 
# As reference for the long term treasury bonds we select the following U.S. funds:
# 
# * 1x LTT => Vanguard Long-Term Treasury Fund Investor Shares (`VUSTX`)
# * 2x LTT => ProShares Ultra 20+ Year Treasury (`UBT`)
# * 3x LTT => Direxion Daily 20+ Year Treasury Bull 3X Shares (`TMF`)
#     
# Also here, we have to notice that the maturity duration of UBT and TMF is not 10-30 years but 20-30 years, which means that also here the european LTT models fits better. 

# In[160]:


vustx = download_from_yahoo("VUSTX", adjust=True)
vustx


# In[161]:


n = normalize(vustx, assets['ltt_us'])
draw_growth_chart(
    {
        'VUSTX (LTT 1x)': n,
        'LTT (US, 10-30 years)': assets['ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)


# For modelling our ETF we chose an expense ratio of 0.20%.

# In[162]:


etfs['1x_ltt_us'] = calc_growth(calc_letf(
    assets_daily_returns['ltt_us'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.2, 
    adjustment_factor=-0,
    percent=100
), percent=1)
etfs


# In[163]:


n = normalize(vustx, etfs['1x_ltt_us'])
draw_growth_chart(
    {
        'VUSTX (LTT 1x)': n,
        '1x LTT (model)': etfs['1x_ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x LTT (model)': etfs['1x_ltt_us'],
    },
    "Long Term Treasury Bonds (reference: VUSTX)",
    overlapping_only = True,
)


# We have a quite good fit here. Between 2000 and 2015 the model is drifting ahead of the fund, so maybe in those years the expense ratio was higher, but in 2020 the error curve is coming back to the reference. 
# 
# For the UBT, we use the european LTT model as base.

# In[164]:


ubt = download_from_yahoo("UBT", adjust=True)
ubt


# In[165]:


n = normalize(ubt, assets['ltt_eu'])
draw_growth_chart(
    {
        'UBT (LTT 2x)': n,
        'LTT (EU, 20-30 years)': assets['ltt_eu'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)


# We model the ETF with an expense ratio of 0.95%.

# In[166]:


etfs['2x_ltt_us'] = calc_growth(calc_letf(
    assets_daily_returns['ltt_eu'], 
    borrowing_rate=borrowing,
    leverage=2,
    er=0.95, 
    adjustment_factor=-0,
    percent=100
), percent=1)
etfs


# In[167]:


n = normalize(ubt, etfs['2x_ltt_us'])
draw_growth_chart(
    {
        'UBT (LTT 2x)': n,
        '2x LTT (model)': etfs['2x_ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '2x LTT (model)': etfs['2x_ltt_us'],
    },
    "Long Term Treasury Bonds (reference: UBT)",
    overlapping_only = True,
)


# This is out of the box a very good fit. So we can dirctly focus on TMF.

# In[168]:


tmf = download_from_yahoo("TMF", adjust=True)
tmf


# In[169]:


n = normalize(tmf, assets['ltt_eu'])
draw_growth_chart(
    {
        'TMF (LTT 3x)': n,
        'LTT (EU, 20-30 years)': assets['ltt_eu'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)


# Here we use an expense ratio of 1.06%.

# In[170]:


etfs['3x_ltt_us'] = calc_growth(calc_letf(
    assets_daily_returns['ltt_eu'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=1.06, 
    adjustment_factor=-0,
    percent=100
), percent=1)
etfs


# In[171]:


n = normalize(tmf, etfs['3x_ltt_us'])
draw_growth_chart(
    {
        'TMF (LTT 3x)': n,
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasury Bonds (reference: TMF)",
    overlapping_only = True,
)


# Our model is diverging a lot over time, so we have to add an adjustment-factor of 1%.

# In[172]:


etfs['3x_ltt_us'] = calc_growth(calc_letf(
    assets_daily_returns['ltt_eu'], 
    borrowing_rate=borrowing,
    leverage=3,
    er=1.06, 
    adjustment_factor=-1.0,
    percent=100
), percent=1)
etfs


# In[173]:


n = normalize(tmf, etfs['3x_ltt_us'])
draw_growth_chart(
    {
        'TMF (LTT 3x)': n,
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasury Bonds (reference: TMF)",
    overlapping_only = True,
)


# As we can see the strongest drift is between 2009 and 2011. Afterwards the curve is mostly flat. Let's restrict the comparison to the time afterwards.

# In[174]:


tmf = tmf.loc['2011':]


# In[175]:


n = normalize(tmf, etfs['3x_ltt_us'])
draw_growth_chart(
    {
        'TMF (LTT 3x)': n,
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '3x LTT (model)': etfs['3x_ltt_us'],
    },
    "Long Term Treasury Bonds (reference: TMF)",
    overlapping_only = True,
)


# This is a very good fit. It is unclear, why from 2009 to 2011 the curve was growing so strong. Maybe the costs where 

# For europe we only have one Lont Term Treasury Fund, which is DTLA. This fund has not leverage factor, thus for the 2x and 3x leverage factors, we just can copy the values from the US ETFs. 

# In[176]:


dtla = download_from_yahoo("DTLA.L", adjust=True)
dtla


# In[177]:


n = normalize(dtla, assets['ltt_eu'])
draw_growth_chart(
    {
        'DTLA (LTT 1x)': n,
        'LTT (EU, 20-30 years)': assets['ltt_eu'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)


# We already have a very good fit. However we still model the ETF with an expense ratio of 0.07%.

# In[178]:


etfs['1x_ltt_eu'] = calc_growth(calc_letf(
    assets_daily_returns['ltt_eu'], 
    borrowing_rate=borrowing,
    leverage=1,
    er=0.07, 
    adjustment_factor=0.0,
    percent=100
), percent=1)
etfs


# In[179]:


n = normalize(dtla, etfs['1x_ltt_eu'])
draw_growth_chart(
    {
        'DTLA (LTT 1x)': n,
        '1x LTT (model)': etfs['1x_ltt_eu'],
    },
    "Long Term Treasuries",
    overlapping_only = True,
)
draw_telltale_chart(
    n,
    {
        '1x LTT (model)': etfs['1x_ltt_eu'],
    },
    "Long Term Treasury Bonds (reference: DTLA)",
    overlapping_only = True,
)


# This looks fine. The remaining ETFs can be copied from the US, since we anyway do not have any reference to compare with.

# In[182]:


etfs['2x_ltt_eu'] = etfs['2x_ltt_us']
etfs['3x_ltt_eu'] = etfs['3x_ltt_us']


# Let's normalize all ETFs to a start of $100 in 1943 and then we draw them all in one graph.

# In[180]:


for c in etfs.columns:
    etfs[c] = normalize(etfs[c], start_value=100)
etfs


# ## Review: S&P 500 ETFs
# 
# Let's now review all assets class by class. We first start with S&P 500.

# In[181]:


draw_growth_chart(
    {
        '1x S&P 500': etfs['1x_sp500_us'],
        '2x S&P 500': etfs['2x_sp500_us'],
        '3x S&P 500': etfs['3x_sp500_us'],
    },
    "S&P 500 ETFs (US)",
    overlapping_only = True,
)   


# ## Review: Nasdaq-100 ETFs
# 

# In[183]:


draw_growth_chart(
    {
        '1x Nasdaq-100': etfs['1x_ndx100_us'],
        '2x Nasdaq-100': etfs['2x_ndx100_us'],
        '3x Nasdaq-100': etfs['3x_ndx100_us'],
    },
    "Nasdaq-100 (US)",
    overlapping_only = True,
)   


# In[184]:


draw_growth_chart(
    {
        '1x Nasdaq-100': etfs['1x_ndx100_eu'],
        '2x Nasdaq-100': etfs['2x_ndx100_eu'],
        '3x Nasdaq-100': etfs['3x_ndx100_eu'],
    },
    "Nasdaq-100 (EU)",
    overlapping_only = True,
) 


# ## Review: Gold ETFs

# In[185]:


draw_growth_chart(
    {
        '1x Gold': etfs['1x_gold_us'],
        '2x Gold': etfs['2x_gold_us'],
    },
    "Gold (US)",
    overlapping_only = True,
)   


# The leveraged Gold ETFs is hardly making any returns. Due to long phases of sidewards movement, the volatility decay combined with the costs is eating up all returns. 

# In[186]:


draw_growth_chart(
    {
        '1x Gold': etfs['1x_gold_eu'],
        '2x Gold': etfs['3x_gold_eu'],
    },
    "Gold (US)",
    overlapping_only = True,
)   


# This effect is even worse for the 3x leveraged Gold fund in europe. 

# ## Review: Long Term Treasury ETFs

# In[187]:


draw_growth_chart(
    {
        '1x LTT': etfs['1x_ltt_us'],
        '2x LTT': etfs['2x_ltt_us'],
        '3x LTT': etfs['3x_ltt_us'],
    },
    "Lont Term Treasurys (US)",
    overlapping_only = True,
)   


# In[188]:


draw_growth_chart(
    {
        '1x LTT (EU)': etfs['1x_ltt_eu'],
        '1x LTT (US)': etfs['1x_ltt_us'],
    },
    "Lont Term Treasurys",
    overlapping_only = True,
)   


# It seems, that the EU LTT ETF is a little bit ahead of the US version. The reason for that is the reference we have used: The US reference was a normal fund from the times, where ETFs have not exist. Such a fund has normally much higher costs compared to modern ETFs. 

# ## Review: Intermidiate Term Treasury ETFs

# In[189]:


draw_growth_chart(
    {
        '1x ITT': etfs['1x_itt_us'],
        '2x ITT': etfs['2x_itt_us'],
        '3x ITT': etfs['3x_itt_us'],
    },
    "Intermidiate Term Treasurys (US)",
    overlapping_only = True,
)   


# This is interesting: While the leveraged LTT ETFs were lacking behind the unleveraged reference over such a long periode of time, the leveraged ITT ETFs perform much better then the unleveraged reference. But also here the reason is the strong periode of growth from 1985 until today. During the years 1965 to 1985 betting on leveraged bond funds would have been a bad idea. 

# In[190]:


draw_growth_chart(
    {
        '1x ITT': etfs['1x_itt_eu'],
        '2x ITT (same as US)': etfs['2x_itt_eu'],
        '3x ITT': etfs['3x_itt_eu'],
    },
    "Intermidiate Term Treasurys (EU)",
    overlapping_only = True,
)  


# For the european ETFs the situation is different. Keep in mind, that the 2x ITT ETF does not exist in Europe, it is just the US version as reference. So the 3x ITT ETN has a very bad performance compared to the unleveraged one. The reason for this are clearly the high costs of the WisdomTree ETN, which makes it hard for this ETN to recover from the years 1965 t0 1985. Let's restrict the graph to the years of strong growth beginnin in 1985.

# In[191]:


draw_growth_chart(
    {
        '1x ITT': normalize(etfs['1x_itt_eu'].loc['1985':], start_value=10000),
        '2x ITT (same as US)': normalize(etfs['2x_itt_eu'].loc['1985':], start_value=10000),
        '3x ITT': normalize(etfs['3x_itt_eu'].loc['1985':], start_value=10000),
    },
    "Intermidiate Term Treasurys (EU)",
    overlapping_only = True,
)  


# So we can see that the 3x leveraged ETN has the highest gain in an ideal growth environment for bonds. 
# 
# However, my hypothesis is: We most probably do not have an ideal growth environment for bonds in the next years. 

# ## Review: Short Term Treasury ETFs

# In[193]:


draw_growth_chart(
    {
        '1x STT': etfs['1x_stt_us'],
    },
    "Short Term Treasurys (US)",
    overlapping_only = True,
) 


# And now we store the ETFs as excel file.

# In[194]:


etfs.to_excel(clean_data_path / "etfs.xlsx")


# In[ ]:




