#!/usr/bin/env python
# coding: utf-8

# # Basic Data Analysing
# 
# In this notebook we analyse our input data on very basic levels, like calculating the yearly return, the correlation or seasonal returns of different assets. 

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import numpy_financial as npf
import pandas.tseries.offsets as pd_offsets
from typing import List, Optional, Dict
import plotly.figure_factory as ff
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart, draw_risk_reward_chart, draw_periodic_return
from utils.plots import draw_correlations
from utils.math import gmean, calc_min_returns, calc_max_drawdown, calc_correlations_over_time
from utils.math import calc_average_return_over_time
from utils.data import cached


# The first step is to load the data, we have prepared for our backtest.

# In[3]:


clean_data_path = Path("clean_data")
cache_path = Path("cached_clean_data")


# In[4]:


input_path = clean_data_path / "assets.xlsx"
assets = pd.read_excel(input_path, index_col=0)
assets.index = pd.to_datetime(assets.index)
assets


# In[5]:


inflation = pd.read_excel(clean_data_path / "inflation.xlsx", index_col=0)
inflation.index = pd.to_datetime(inflation.index)
inflation


# In[6]:


ffr = pd.read_excel(clean_data_path / "ffr.xlsx", index_col=0)
ffr.index = pd.to_datetime(ffr.index)
ffr


# In[7]:


draw_growth_chart(
    {
        'long term treasury bonds': assets['ltt_eu'],
        'short term treasury bonds': assets['stt_eu'],
        'gold': assets['gold'],
        'nasdaq-100': assets['ndx100'],
        's&p 500': assets['sp500'],
        'nasdaq-100 (incl. div)': assets['ndx100+div'],
        's&p 500 (incl. div)': assets['sp500+div'],
    },
    "Growth of Assets from 1943 to 2021"
)


# In this chart we see the growth of different asset classes we have in our data. The short term treasury bonds (stt) have the slowest growths over a period of almost 80 years. Gold and long term treasury bonds also have a rather slow growth.
# 
# A very good growth has the S&P 500 (especially when taking the dividends into account), but it is even outperformed by the Nasdaq-100, which was introduced in 1985. The volatility of the Nasdaq-100 is higher, but in the end in 2021, the value of this investment is 5 times higher then the value of s&p 500. 

# ## Mininum Returns and Maximum Drawdown
# 
# We can now also calculate the minimum return, we expect, if we buy an assets at the worst time ever and hold it for a fixed amout of years, until we need it back.

# In[8]:


min_returns, min_returns_date = cached(cache_path / "04_min_retruns.pkl")(calc_min_returns)(
    assets,
    list(range(1,31)),
)
min_returns


# In[9]:


def get_annual_roi(roi, years):
    return (np.power(1 + roi/100, 1/years) - 1) * 100

zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
draw_growth_chart(
    {
        'zero': zero,
        'STT (EU)': get_annual_roi(min_returns['stt_eu'], min_returns.index),
        'ITT (EU)': get_annual_roi(min_returns['itt_eu'], min_returns.index),
        'LTT (EU)': get_annual_roi(min_returns['ltt_eu'], min_returns.index),
        'gold': get_annual_roi(min_returns['gold'], min_returns.index),
        'S&P 500 (incl. dividends)': get_annual_roi(min_returns['sp500+div'], min_returns.index),
        'Nasdaq-100 (incl. dividends)': get_annual_roi(min_returns['ndx100+div'], min_returns.index),
    },
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-5, 10],
)


# As we can see, the only short term investment, where we do not lose money if we invest at the worst time ever (ATH of markets directly before a crisis starts) are the Short Term Treasury bounds. If we hold this for a minimum of 2 years, we will still get a small positive return out of it. And if we are willing to hold it at least 15 years a 1.8% average return is the minimum we should expect. For 30 years, the worst case is an average return of 3%. 
# 
# The Intermediate Term Treasuries (ITT) are much worse then the STTs, since in worst case it would take at least 5 years to reach breakeven and even for 15 or 30 years, the worst case return of STTs is slightly higher. 
# 
# Gold and LTTs are performing even more worse, if we invest at the wrong time.
# 
# S&P 500 and Nasdaq-100 have extremly high losses in the first years. But after around 12-15 years they reach breakeven and on the long term (thanks to the dividends), the minimum return of both is almost 9% for 30 years. 
# 
# This graph illustrates, why it is a bad idea to invest a huge amount of money at once at a single asset. This increases the risk of being a bagholder for at least 12 years drastically. In those cases, it is better to just invest it in STT and you are most probably safe with your investment. Or split it into smaller amounts and invest it over several month and years to avoid directly investing everything at the highest point directly before a crises starts. 

# * The worst time to invest in gold was 1980, directly before the gold-price crashed. It did not recover for many years.
# * The worst time for Nasdaq-100 was 2000, directly before the dot-com bubble. It tool 17 years to recover.
# * The worst time for S&P 500 was 2008, directly before the financial crises. But it recovered quite fast. Investing in S&P 500 directly before the dot-com bubble took 13 years to recover. 
# * For the LTTs there was not a single event, but more a periode of years before 1980 where those assets did not have any positive returns for many years.

# In[10]:


min_returns_date


# Now let's calculate the maximum drawdown of our assets. 

# In[11]:


max_drawdown, max_drawdown_start, max_drawdown_end = cached(cache_path / "04_max_drawdown.pkl")(calc_max_drawdown)(
    assets
)


# In[12]:


def draw_max_drawdown(c, name):
    print(f"'{name}' max. drawdown: {max_drawdown[c]:.2f}% (from {max_drawdown_start[c]} to {max_drawdown_end[c]})")
    draw_growth_chart(
        {
            name: assets.loc[max_drawdown_start[c]:max_drawdown_end[c], c]
        },
        f"Max. Drawdown of {name}"
    )


# In[13]:


draw_max_drawdown('stt_eu', "STT")


# In[14]:


draw_max_drawdown('itt_eu', "ITT")


# In[15]:


draw_max_drawdown('ltt_eu', "LTT")


# In[16]:


draw_max_drawdown('gold', "Gold")


# In[17]:


draw_max_drawdown('sp500+div', "S&P 500 (incl. dividends)")


# In[18]:


draw_max_drawdown('ndx100+div', "Nasdaq-100 (incl. dividends)")


# ## Yearly Returns

# Now let's calculate the yearly return of all our assets. 

# In[19]:


yearly_returns = assets.pct_change(1, freq="Y")
yearly_returns = yearly_returns.dropna()
yearly_returns


# In[20]:


for c in yearly_returns.columns:
    ret = gmean(yearly_returns[c])
    print(f"Average Annual Return of '{c}': {ret * 100:.2f}%")


# Also those numbers reflect our interpretation from the growth chart above: All treasury bonds and gold have an anverage annual return in the same region around 5-6%. S&P 500 reaches an average annual return of 8% without dividends and 12% with dividends. Thus it is drastically outperforming the bonds and gold. But Nasdaq-100 has with 10% without dividends and 13% with dividends the highest average annual return.
# 
# Keep in mind, that we calculated those numbers vom 1944, where the Nasdaq-100 did not exist. If we calcualte it form 1985, the average annual return of the Nasdaq-100 is even much higher. 

# In[21]:


for c in yearly_returns.columns:
    ret = gmean(yearly_returns.loc['1985':,c])
    print(f"Average Annual Return of '{c}': {ret * 100:.2f}%")


# Now the Nasdaq-100 average annual return with dividends above 15%.

# In[22]:


for c in yearly_returns.columns:
    ret = yearly_returns[c].max()
    print(f"Max Annual Return of '{c}': {ret * 100:.2f}%")


# In[23]:


for c in yearly_returns.columns:
    ret = yearly_returns[c].min()
    print(f"Min Annual Return of '{c}': {ret * 100:.2f}%")


# Let's review our average annual return and the max. drawdown in a risk/reward chart to get a better understanding of our assets.

# In[24]:


risk_reward = pd.DataFrame(
    index = max_drawdown.index,
    columns = ['risk', 'reward']
)
for asset in risk_reward.index:
    risk_reward.loc[asset, 'risk'] = max_drawdown[asset] * -1
    risk_reward.loc[asset, 'reward'] = gmean(yearly_returns[asset]) * 100
    risk_reward

draw_risk_reward_chart(
    risk_reward,
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# This chart gives us a good understanding about the risk and reward of different assets. In the left buttom corner we find the U.S. Treasury Bonds with very small average annual returns, but also not so much maximum drawdown. On the right side we can see those assets which are more risky. Surprisingly we see here Gold, which had a huge drawdown beginning of 1980 until 2000. Even S&P 500 has a better risk/reward ratio then gold. The best average annual returns delivers the Nasdaq-100, but this comes with an extreme huge max. drawdown of over 80% (which happened during the dot-com bubble). 

# In[25]:


draw_periodic_return(
    {
        'ltt': yearly_returns['ltt_eu'],
        'stt': yearly_returns['stt_eu'],
        'gold': yearly_returns['gold'],
        's&p 500 (incl. dividends)': yearly_returns['sp500+div'],
        'nasdaq-100 (incl. dividends)': yearly_returns['ndx100+div'],
    },
    "Yearly Returns"
)


# In this graph, we can see that in the 1970th until the 1980th gold had a very high annual return. But after the 1980th the return of gold was generally lower than for the other assets. The return of the S&P 500 seems to be quite steady without high peaks in the positive or negative direction. The Nasdaq-100 had very high returns in the years befor 2000 and in the years after, the return was strongly negative. This was the dot-com-bubble. We can also clearly see the 2008 financial crisis, where almost all assets had negative returns, except of the treasury bonds. The long term treasury bonds had their highest returns in the years after the 1980. 
# 
# Now, we will look closer at the years from 1965 to 1990 and compare this with the inflation rate at this time.

# In[26]:


fig = draw_periodic_return(
    {
        'ltt': yearly_returns.loc['1965':'1990', 'ltt_eu'],
        'gold': yearly_returns.loc['1965':'1990', 'gold'],
        's&p 500 (incl. dividends)': yearly_returns.loc['1965':'1990', 'sp500+div'],
    },
    "Yearly Returns",
    show=False
)
fig.update_yaxes(title_text="inflation in % (yoy)", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc['1965':'1990', 'yoy'].index,
        y=inflation.loc['1965':'1990', 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.show()


# In this graph we can see, that gold had extremly high gains in those years where the inflation was increasing a lot. On years where the inflation was decreasing, gold has very small or even negative returns. This might be important in case the inflation is further increasing in the upcomming years. 

# ## Seasonal Returns
# 
# In the next section, we investigate into seasonal returns of our assets.

# In[27]:


monthly_returns = assets.pct_change(1, freq="M")
monthly_returns = monthly_returns.dropna()
monthly_returns


# For investigating into seasonal effects, we should delete years, which has crisis. So we delete the years 1973, 1974, 2000, 2001, 2002, 2008 and 2020.

# In[28]:


years_to_delete = [1973, 1974, 2000, 2001, 2002, 2008, 2020]
monthly_returns_corrected = monthly_returns[~(monthly_returns.index.year.isin(years_to_delete))]
monthly_returns_corrected


# In[29]:


seasonal_returns = monthly_returns_corrected.groupby(monthly_returns_corrected.index.month).mean()
fig = draw_periodic_return(
    {
        'ltt': seasonal_returns['ltt_eu'],
        'gold': seasonal_returns['gold'],
        's&p 500 (incl. dividends)': seasonal_returns['sp500+div'],
    },
    "Seasonal Returns",
    show=True
)


# In[30]:


month = 2
month_returns = monthly_returns_corrected.loc[monthly_returns_corrected.groupby(monthly_returns_corrected.index.month).groups[month], :]
returns_over_time = cached(cache_path / "04_average_return_over_time_feb.pkl")(calc_average_return_over_time)(
    month_returns,
    relativedelta(years=10),
    relativedelta(months=1),
    ['stt_eu', 'itt_eu', 'ltt_eu', 'gold', 'sp500+div']
)    
draw_growth_chart(
    {
        'Average Return (all years)': pd.Series(index = month_returns.index, data = month_returns['sp500+div'].mean() * 100),
        #'ltt': month_returns['ltt_us'] * 100,
        #'gold': month_returns['gold'] * 100,
        'S&P 500 (incl. Dividends)': month_returns['sp500+div'] * 100,        
    },
    "Average Returns for February over Years (10 Years Moving Average)",
    y_log=False,
    y_title="Return in %"
)


# In[31]:


month = 12
month_returns = monthly_returns_corrected.loc[monthly_returns_corrected.groupby(monthly_returns_corrected.index.month).groups[month], :]
returns_over_time = cached(cache_path / "04_average_return_over_time_dec.pkl")(calc_average_return_over_time)(
    month_returns,
    relativedelta(years=10),
    relativedelta(months=1),
    ['stt_eu', 'itt_eu', 'ltt_eu', 'gold', 'sp500+div']
)    
draw_growth_chart(
    {
        'Average Return (all years)': pd.Series(index = month_returns.index, data = month_returns['sp500+div'].mean() * 100),
        #'ltt': month_returns['ltt_us'] * 100,
        #'gold': month_returns['gold'] * 100,
        'S&P 500 (incl. Dividends)': month_returns['sp500+div'] * 100,        
    },
    "Average Returns for December over Years (10 Years Moving Average)",
    y_log=False,
    y_title="Return in %"
)


# ## Daily Returns 
# 
# Now we concentrate on analysis, for which we use daily return rates.

# In[32]:


daily_returns = assets.pct_change(1, freq="D")
daily_returns = daily_returns.dropna()
daily_returns


# In[33]:


correlations_long = daily_returns.corr()


# In[34]:


draw_correlations(correlations_long, daily_returns, "daily", ['stt_eu', 'stt_us'], 1)


# In[35]:


draw_correlations(correlations_long, daily_returns, "daily", ['itt_eu', 'itt_us'], 1)


# In[36]:


draw_correlations(correlations_long, daily_returns, "daily", ['ltt_eu', 'ltt_us'], 1)


# As we can see, the US and EU treasury bonds are very high correlated to eachother. This is expected, since they are based on the same yields, just with slightly different maturity durations. 

# In[37]:


draw_correlations(correlations_long, daily_returns, "daily", ['stt_eu', 'itt_eu', 'ltt_eu'], 2)


# But also to eachother (STT vs. ITT vs. LTT) the correlation is very high. However, with increasing maturity duration the correlations is decreasing.

# In[38]:


draw_correlations(correlations_long, daily_returns, "daily", ['stt_eu', 'itt_eu', 'ltt_eu', 'gold'], 3)


# Gold is very less correlated to the Treasury Bonds. This makes gold to a good hedge inside the hedge. 

# In[39]:


draw_correlations(correlations_long, daily_returns, "daily", ['stt_eu', 'itt_eu', 'ltt_eu', 'sp500'], 3)


# Also the correlation between Treasury bonds and the S&P 500 is very low. 

# In[40]:


draw_correlations(correlations_long, daily_returns, "daily", ['ltt_eu', 'gold', 'sp500'], 2)


# Also the correlation between Gold and S&P 500 is very low. With LTT, Gold and S&P 500, we have 3 almost completly uncorrelated assets. 

# For analysing the correlations of Nasdaq-100, we need to start from 1986, instead of 1944. Otherwise the the correlations between S&P 500 and Nasdaq-100 is too high, because it is overlapping half of the time.

# In[41]:


correlations_short = daily_returns.loc['1986':, :].corr()


# In[42]:


draw_correlations(correlations_long, daily_returns, "daily", ['ndx100', 'sp500'], 1)


# Since the introduction of the Nasdaq-100, the correlation between S&P 500 and Nasdaq-100 is quite high.

# In[43]:


draw_correlations(correlations_long, daily_returns, "daily", ['ltt_eu', 'gold', 'sp500', 'ndx100'], 3)


# However, Nasdaq-100 seems to be in the same way uncorrelated to LTT and Gold as S&P 500 is. 

# In[44]:


draw_correlations(daily_returns.corr(), daily_returns, "daily", ['ltt_eu', 'gold', 'sp500', 'ndx100'], 3)


# In[45]:


draw_correlations(monthly_returns.corr(), monthly_returns, "monthly", ['ltt_eu', 'gold', 'sp500', 'ndx100'], 3)


# In[46]:


draw_correlations(yearly_returns.corr(), yearly_returns, "annual", ['ltt_eu', 'gold', 'sp500', 'ndx100'], 3)


# We can also see, that the correlation does not change much when we calculate it on the monthly or yearly returns. Only the correlation between Gold and S&P500/Nasdaq-100 is increasing slightly, but in the negative way, thus when S&P 500 is shrinking gold is slightly increasing.

# ## Effect of Inflation on Returns
# 
# Now let's investigate in the correlation between inflation and returns of different asset classes. First we print the inflation over all years together with Gold, S&P500 and LTTs. 

# In[47]:


fig = draw_periodic_return(
    {
        'ltt': yearly_returns.loc[:, 'ltt_eu'],
        'gold': yearly_returns.loc[:, 'gold'],
        's&p 500': yearly_returns.loc[:, 'sp500'],
    },
    "Yearly Returns",
    show=False
)
fig.update_yaxes(title_text="inflation in % (yoy)", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=inflation.loc[:, 'yoy'].index,
        y=inflation.loc[:, 'yoy'],
        mode='lines',
        name="inflation",
    ),
    secondary_y=True
)
fig.show()


# On a first glance, it looks like small inflation is better for S&P 500 and high inflation is better for Gold. Let's now calculate the correlation.

# In[48]:


correlation = yearly_returns.copy()
correlation.index = correlation.index - pd_offsets.MonthBegin(0)
correlation['inflation'] = inflation[(inflation.index.day == 1) & (inflation.index.month==1)]['yoy']
draw_correlations(correlation.corr(), correlation, "yearly", ['ltt_eu', 'gold', 'sp500', 'inflation'], 3)


# On the yearly data, we can see a small negative correlation on S&P 500 and a small positive on Gold. Thus when the inflation increases Gold returns are more likly to increase as well and S&P 500 returns are more likly to decrease. But the effect is very weak.

# ## Effect of Interest Rates on Asset Returns
# 
# Now we do the same investigation for interest rates. First we look at the returns and try to detect patterns.

# In[49]:


fig = draw_periodic_return(
    {
        'ltt': yearly_returns.loc[:, 'ltt_eu'],
        'gold': yearly_returns.loc[:, 'gold'],
        's&p 500': yearly_returns.loc[:, 'sp500'],
    },
    "Yearly Returns",
    show=False
)
fig.update_yaxes(title_text="federal funds return in %", secondary_y=True, showgrid=False)
fig.add_trace(
    go.Scatter(
        x=ffr.index,
        y=ffr['ffr'],
        mode='lines',
        name="federal funds return",
    ),
    secondary_y=False
)
fig.show()


# It looks like when the interest rate is decreasing, also Gold returns are decreasing. Furthermore the S&P 500 returns seems to increase at the same time. This makes sense, because of the small negative correlation between Gold and S&P 500 on yearly returns data. 

# In[50]:


correlation = yearly_returns.copy()
correlation.index = correlation.index - pd_offsets.MonthBegin(0)
ffr_yearly = ffr.groupby(ffr.index.year).mean()['ffr']
for i in correlation.index:
    correlation.loc[i, 'interest'] = ffr_yearly.loc[i.year]
draw_correlations(correlation.corr(), correlation, "yearly", ['ltt_eu', 'gold', 'sp500', 'interest'], 3)


# The effect on Gold and S&P 500 is even weaker as it was for the inflation rate. This is a sign that the asset returns is maybe a little bit sensitive to inflation, and since inflation and interest rate has some kind of correlation, it is also sensitive (but not so much) on the interest rate.

# In[51]:


correlations_over_time = cached(cache_path / "04_correlation_over_time_5_years.pkl")(calc_correlations_over_time)(
    daily_returns,
    relativedelta(years=5),
    relativedelta(months=1),
    ['stt_eu', 'itt_eu', 'ltt_eu', 'gold', 'sp500']
)    
correlations_over_time    


# In[52]:


draw_growth_chart(
    {
        'ltt vs. sp500': correlations_over_time['ltt_eu vs. sp500'] * 100,
        'itt vs. sp500': correlations_over_time['itt_eu vs. sp500'] * 100,
        'stt vs. sp500': correlations_over_time['stt_eu vs. sp500'] * 100,
        'gold vs. sp500': correlations_over_time['gold vs. sp500'] * 100,
        'ltt vs. gold': correlations_over_time['ltt_eu vs. gold'] * 100,        
    },
    "Correlation over Years (5 Years Correlation)",
    y_log=False,
    y_title="correlation in %"
)


# As we can see the correlation between stocks and bonds is changing drastically over time. There were periods of years, where the correlation was almost 40% and on other periods the correlation was negative.
# 
# The correlation between gold and stocks and gold and bonds is almost the whole time very low below absolute 20%.

# In[53]:


correlations_over_time = cached(cache_path / "04_correlation_over_time_3_month.pkl")(calc_correlations_over_time)(
    daily_returns,
    relativedelta(months=3),
    relativedelta(months=1),
    ['stt_eu', 'itt_eu', 'ltt_eu', 'gold', 'sp500']
)    
correlations_over_time    


# In[54]:


draw_growth_chart(
    {
        'ltt vs. sp500': correlations_over_time['ltt_eu vs. sp500'] * 100,
        'itt vs. sp500': correlations_over_time['itt_eu vs. sp500'] * 100,
        'stt vs. sp500': correlations_over_time['stt_eu vs. sp500'] * 100,        
        'gold vs. sp500': correlations_over_time['gold vs. sp500'] * 100,
        'ltt vs. gold': correlations_over_time['ltt_eu vs. gold'] * 100,        
    },
    "Correlation over Years (3 Month Correlation)",
    y_log=False,
    y_title="correlation in %"
)

