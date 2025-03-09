#!/usr/bin/env python
# coding: utf-8

# # Basic Analysis of the ETF Data
# 
# In this notebook, we will analyze the different ETF variants in the same way as we did it with the asset classes. We want to find out, which ETF is under which conditation a good investment choice. 

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import pandas.tseries.offsets as pd_offsets
import pickle
import plotly.graph_objects as go


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart, draw_risk_reward_chart, draw_periodic_return
from utils.plots import draw_correlations
from utils.math import gmean, calc_min_returns, calc_max_drawdown, calc_correlations_over_time, normalize, calc_returns
from utils.data import cached


# In[3]:


clean_data_path = Path("clean_data")
cache_path = Path("cached_data")


# In[4]:


input_path = clean_data_path / "etfs.xlsx"
etfs = pd.read_excel(input_path, index_col=0)
etfs.index = pd.to_datetime(etfs.index)
etfs


# In[5]:


min_returns, min_returns_date = cached(cache_path / "06_min_returns.pkl")(calc_min_returns)(
    etfs,
    list(range(1,31)),
)
min_returns


# In[6]:


def get_annual_roi(roi, years):
    return (np.power(1 + roi/100, 1/years) - 1) * 100


# In[7]:


max_drawdown, max_drawdown_start, max_drawdown_end = cached(cache_path / "06_max_drawdown")(calc_max_drawdown)(etfs)


# In[8]:


def draw_max_drawdown(c, name):
    print(f"'{name}' max. drawdown: {max_drawdown[c]:.2f}% (from {max_drawdown_start[c]} to {max_drawdown_end[c]})")
    draw_growth_chart(
        {
            name: etfs.loc[max_drawdown_start[c]:max_drawdown_end[c], c]
        },
        f"Max. Drawdown of {name}"
    )


# In[9]:


yearly_returns = etfs.pct_change(1, freq="Y")
yearly_returns = yearly_returns.dropna()
yearly_returns


# In[10]:


risk_reward = pd.DataFrame(
    index = max_drawdown.index,
    columns = ['risk', 'reward']
)
for asset in risk_reward.index:
    risk_reward.loc[asset, 'risk'] = max_drawdown[asset] * -1
    risk_reward.loc[asset, 'reward'] = gmean(yearly_returns[asset]) * 100
    risk_reward


# In[11]:


max_drawdown_1986, max_drawdown_start_1986, max_drawdown_end_1986 = cached(cache_path / "06_max_drawdown_1986")(calc_max_drawdown)(etfs.loc['1986':,:])
yearly_returns_1986 = etfs.loc['1986':,:].pct_change(1, freq="Y")
yearly_returns_1986 = yearly_returns_1986.dropna()
risk_reward_1986 = pd.DataFrame(
    index = max_drawdown_1986.index,
    columns = ['risk', 'reward']
)
for asset in risk_reward_1986.index:
    risk_reward_1986.loc[asset, 'risk'] = max_drawdown_1986[asset] * -1
    risk_reward_1986.loc[asset, 'reward'] = gmean(yearly_returns_1986[asset]) * 100
risk_reward_1986


# ## Volatilty-Decay of Leveraged ETFs
# 
# An often mentioned argument against leveraged ETFs is the volatility-decay. This decay cames from the fact, that if an asset is on the one day loosing 1% and on the other day gaining 1%, the total value is still less on the second day. Thus every kind of investment has this decay. However, due to the leverage factor the decay is stronger for leveraged ETFs, thus they suffer stronger from it.
# 
# For asset classes, which do not grow strongly and for periodes of times, where the value goes more or less sidewards, we just lose money due to the volatility-decay. 
# 
# However does this mean, we should avoid leveraged ETFs in general? We will now investigate the leveraged ETFs compared to unleveraged ETFs in different asset classes for different time periods. The first time period is from 1943 until 1986. The second from 1986 to 2021. We chose this sepration, because Hedgefundie has done his original backtests from 1986 to 2018. The third is taking the whole period from 1943 until 2021 into account.

# In[12]:


def analyze_gains(data, assets, title, additional_data = None, show=True):
    first_asset = list(assets.keys())[0]
    first = normalize(data[first_asset], start_value=1000)
    data_to_show = {}
    for a, n in assets.items():
        data_to_show[n] = normalize(data[a], first)
    if additional_data is not None:
        for n, d in additional_data.items():
            data_to_show[n] = d
    fig = draw_growth_chart(
        data_to_show,
        title,
        show = show,
    )
    yearly_returns = calc_returns(data, freq="Y").iloc[1:]
    for a, n in assets.items():
        print(f"{n}: Average Return: {gmean(yearly_returns[a])*100:.2f}% (min. {yearly_returns[a].min()*100:.2f}%, max. {yearly_returns[a].max()*100:.2f}%)")
    return fig
    


# ### S&P 500 (U.S. ETFs)

# In[13]:


assets = {
    '1x_sp500_us': "1x S&P 500", 
    '2x_sp500_us': "2x S&P 500", 
    '3x_sp500_us': "3x S&P 500",
}


# In[14]:


analyze_gains(etfs.loc['1943':'1986'], assets, "Growth of S&P 500 (US) ETFs from 1943 to 1986")


# In[15]:


analyze_gains(etfs.loc['1986':], assets, "Growth of S&P 500 (US) ETFs from 1986 until today")


# While the 3x leveraged S&P 500 has outperformed from 1943 to 1985 without any exception, it dropped several times below the value of the normal S&P 500 ETF during crisis started after 1985. Expecially 2007-2009 was a very bad crisis for leveraged ETFs. However in the end it is outperforming the the other ETFs due to the fast growth after any crisis. 

# In[16]:


analyze_gains(etfs.loc[:], assets, "Growth of S&P 500 (US) ETFs from 1943 until today")


# In the whole periode from 1943 until today, the 3x leveraged ETFs is clearly outperforming the remaining ETFs. This is because of the strong start in the years after 1950, which gives the 3x leveraged ETF such a strong advantage over the others, that upcoming crisis cannot change the excellet performance. So in the end we can conclude, that for the US market and S&P 500 the 3x leveraged ETFs is giving the stronged performance. 

# As a next step, we look at the minimum-return of different U.S. S&P 500 ETFs when we invest for a fixed periode of years.

# In[17]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
draw_growth_chart(
    {
        'zero': zero,
        '1x S&P 500 (US)': get_annual_roi(min_returns['1x_sp500_us'], min_returns.index),
        '2x S&P 500 (US)': get_annual_roi(min_returns['2x_sp500_us'], min_returns.index),
        '3x S&P 500 (US)': get_annual_roi(min_returns['3x_sp500_us'], min_returns.index),
    },
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# It is not surprisingly that the higher the leverage factor is, the longer we must wait in the worst case until we are back to breakeven. While the 1x leveraged S&P 500 ETF is at breakeven after 12 years, the 2x leveraged S&P 500 ETF already takes 21 years and the 3x leveraged S&P 500 ETF even 25 years. After 30 years of waiting, the 1x S&P 500 ETFs is still far ahead from the other ETFs by at least give a performance of 8.6% per year. The 2x S&P 500 ETFs just dilivers 6.1% per year and the 3x leveraged S&P 500 ETF has just 2.6% per year.

# Let's look at the maximum drawdown of all those ETFs:

# In[18]:


draw_max_drawdown('1x_sp500_us', "1x S&P 500 (US)")


# The max. drawdown of the unleveraged ETF was the finincial crisis started in October 2007 and lasted until March 2009. During this time the ETF had a total los of 55%.

# In[19]:


draw_max_drawdown('2x_sp500_us', "2x S&P 500 (US)")


# In[20]:


draw_max_drawdown('3x_sp500_us', "3x S&P 500 (US)")


# For the leveraged ETFs the max. drawdown was the dot-com crisis. Afterwards the leveraged ETFs did not recover before the next crisis (financial crisis) started. So in total it took 9 years, until the floor was reached and during this time the 2x leveraged S&P 500 ETF was losing almost 90% of its value and the 3x leveraged S6P 500 ETF even 98%. 
# 
# This explains very well the extreme risk of leveraged ETFs, when those are used in a buy-and-hold strategy.
# 
# Also this is very well reflected by the risk/reward chart, where the 3x leveraged ETF has with 16% the highest average annual gain, but also the highest possible loss.

# In[21]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# ### S&P 500 (EU ETFs)
# 
# Now let's repeat this analysis for the european market and see, if we get here to the same conclusion.

# In[22]:


assets = {
    '1x_sp500_eu': "1x S&P 500", 
    '2x_sp500_eu': "2x S&P 500", 
    '3x_sp500_eu': "3x S&P 500",
}


# In[23]:


analyze_gains(etfs.loc['1943':'1986'], assets, "Growth of S&P 500 (EU) ETFs from 1943 to 1986")


# We can clearly see that all ETFs have a smaller average return. The reason for that are the higher costs of ETFs in Europe. But especially the 3x S&P 500 ETF (3USL from WisdomTree) is performing much more worse then the US one (UPRO). During the modelling of this ETF, we already noticed, that the costs are almost twice as much as for the US ETF. This reduced the gain drastically in the years after 1970.
# 
# Thanks to the strong growth after 1950 the 3x leveraged ETN is still higher then the others in 1986, but we can clearly see how the strong sideward periode between 1970 and 1984 is reducing the the gap between the 2x leveraged and 3x leveraged ETN. 

# In[24]:


analyze_gains(etfs.loc['1986':], assets, "Growth of S&P 500 (EU) ETFs from 1986 until today")


# This effect gets even more worse in the years after 1986. Here the 2x leveraged ETF is clearly outperforming both other products. The 3x leveraged ETN can hardly reach the same level of the unleveraged ETF and its average performance is almost similar, but for a more than 2x lover minimum return. 

# In[25]:


analyze_gains(etfs.loc[:], assets, "Growth of S&P 500 (EU) ETFs from 1943 until today")


# Also when taking the whole time periode from 1943 until today into account, the 3x leveraged ETN is just at the same level as the 2x leveraged ETF. Surprisingly the 2x leveraged ETF in Europe performs much better then the 2x leveraged ETF in US. 
# 
# Thus the conclusion is: Due to the high costs of the 3x leveraged ETN, the 2x leveraged ETF is the better choice in Europe. 

# In[26]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
draw_growth_chart(
    {
        'zero': zero,
        '1x S&P 500 (EU)': get_annual_roi(min_returns['1x_sp500_eu'], min_returns.index),
        '2x S&P 500 (EU)': get_annual_roi(min_returns['2x_sp500_eu'], min_returns.index),
        '3x S&P 500 (EU)': get_annual_roi(min_returns['3x_sp500_eu'], min_returns.index),
    },
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# We see similar results for the worst case performance: While the unleveraged ETF behaves similar and reaches break even after 12 years, the 2x leveraged ETF in Europe is a little better than the US ETF. It already reached breakeven after 19 yers instead of 21 and after 30 years the worst case performance is 7% instead of 6%. The 3x leveraged ETN is with 27 years for breakeven and 1% worst case performance after 30 years much worse than the US ETF. 

# In[27]:


draw_max_drawdown('1x_sp500_eu', "1x S&P 500 (EU)")


# In[28]:


draw_max_drawdown('2x_sp500_eu', "2x S&P 500 (EU)")


# In[29]:


draw_max_drawdown('3x_sp500_eu', "3x S&P 500 (EU)")


# The maximum drawdown for european ETFs and ETNs is very similar to the US ones. But also here the 2x leveraged ETF slightly better and the 3x leveraged ETN is slightly worse. 

# In[30]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# In the risk/reward chart we can clearly see, that the 2x leveraged ETF in Europe is the better choice. It is delivering the same average performance for much lower risk. 

# ## Nasdaq-100 ETF in US
# 
# For the Nasdaq-100 we don't need to investigate into the periode from 1943 to 1986, since it has just been introduced in 1985 and before the time-series is just the same as the S&P 500. 

# In[31]:


assets = {
    '1x_ndx100_us': "1x Nasdaq-100", 
    '2x_ndx100_us': "2x Nasdaq-100", 
    '3x_ndx100_us': "3x Nasdaq-100",
}


# In[32]:


analyze_gains(etfs.loc['1986':], assets, "Growth of Nasdaq-100 (US) ETFs from 1986 until today")


# The 3x Nasdaq-100 ETF (TQQQ) suffers drastically from volatility decay during the dot-com crisis. Here the 2x Nasdaq-100 ETF has a clearly better performance. It has recovered faster from the crisis and reches an average performance of 17% per year, which is almost as good as the 3x S&P 500 ETF (US) in the strong years from 1943 to 1986. 

# In[33]:


analyze_gains(etfs.loc[:], assets, "Growth of Nasdaq-100 (US) ETFs from 1943 until today")


# Even if we look at the full periode (with S&P 500 instead of Nasdaq-100 before 1985) the 3x leveraged ETF is hardly reaching the same performance as the 2x leveraged ETF. 

# In[34]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# If we consider the worst case performance of the Nasdaq-100 ETFs, we can see that investing in Nasdaq-100 is in general more risky than in S&P 500. The unleveraged ETF takes 16 years until reaching breakeven. And after 30 years the performance is with 8.5% in the same region as for S&P 500. The 2x leveraged ETFs need 21 years for breakeven, which is similar to the 2x leveraged S&P 500 ETF and the 3x leveraged ETF is not reaching breakeven within 30 years. 
# 
# So from this chart it is clear, that the 2x leveraged ETF is for Nasdaq-100 the better choice. 

# In[35]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# The periode of the max. drawdown is for all ETFs the same as for S&P 500. However here already the 2x leverged ETF has a maximum drawdown of 99%, while the 3x leveraged ETF reaches even 99.98%. 

# In[36]:


draw_risk_reward_chart(
    risk_reward_1986.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# In[37]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# The preference for the 2x leveraged ETF can also be seen in the risk/reward chart, where the 2x levereaged ETF is getting a much higher average yearly return then the others, with a slightly less max. drawdown as the 3x leveraged ETF. 

# ## Nasdaq-100 ETF in EU

# In[38]:


assets = {
    '1x_ndx100_eu': "1x Nasdaq-100", 
    '2x_ndx100_eu': "2x Nasdaq-100", 
    '3x_ndx100_eu': "3x Nasdaq-100",
}


# In[39]:


analyze_gains(etfs.loc['1986':], assets, "Growth of Nasdaq-100 (EU) ETFs from 1986 until today")


# For the european ETFs/ETNs, we can see the same pattern: The 3x leveraged ETN is performing very bad, even worse then the 3x leveraged US ETF. But the 2x leveraged ETF in Europe is performing better then the 2x leveraged in US. It is already clear, that the 2x leveraged ETF is also in Europe the best choice. 

# In[40]:


analyze_gains(etfs.loc[:], assets, "Growth of Nasdaq-100 (EU) ETFs from 1943 until today")


# In[41]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# In the worst case, the european ETFs are behaving similar to the US ones: The unleveraged ETF is reaching breakeven after 17 years and the 2x leveraged one after 21 years. After 30 years, the 2x leveraged ETF has a similar performance as the unleveraged one. The 3x leveraged ETF is not reaching breakeven within 30 years. 

# In[42]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# In[43]:


draw_risk_reward_chart(
    risk_reward_1986.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# Of course also the risk/reward chart is showing clearly the advantage of the 2x leveraged ETF over the 3x leveraged one. 

# ## Gold ETF (US)

# In[44]:


assets = {
    '1x_gold_us': "1x Gold", 
    '2x_gold_us': "2x Gold", 
}


# In[45]:


analyze_gains(etfs.loc['1943':'1986'], assets, "Growth of Gold (US) ETFs from 1943 to 1986")


# We can see that gold suffers strongly from high costs for leveraged ETFs in the years before 1970 where the Gold price was mostly stable. Since the time of stable gold price is over, we start the comparison of Gold ETFs from 1970.

# In[46]:


analyze_gains(etfs.loc['1970':'1986'], assets, "Growth of Gold (US) ETFs from 1970 to 1986")


# But even if we start at 19767, the 2x leveraged Gold ETC is performing worse than the unleveraged ETC. The reason is that the slow growth of the gold price cannot compensate the volatility decay and high costs of such an ETC. 

# In[47]:


analyze_gains(etfs.loc['1986':], assets, "Growth of Gold (US) ETFs from 1986 until today")


# In the years after 1986 the Gold price was slowly decreasing until 2001. Thus also in this periode the volatility decay and the high costs for an leveraged ETC cannot be compensated by a stronger growth due to leverage factor. 

# In[48]:


analyze_gains(etfs.loc['1970':], assets, "Growth of Gold (US) ETFs from 1970 until today")


# In[49]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# As we already know from our basic asset analysis, on worst case Gold is reaching breakeven just after 29 years. The leveraged Gold ETC is not reaching breakeven whithin 30 years. 

# In[50]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# The max. drawdown of Gold happened from 1980 until year 2000. Giving Gold investers a two decades long time of pain. 

# In[51]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# Also from the risk/reward chart it is clear, that leveraged Gold ETF are not an option. 

# ## Gold ETFs (EU)
# 
# In the EU we don't have 2x leveraged Gold ETCs. But we have a 3x leveraged Gold ETN from WisdomTree. We do not expect that this performs better then the 2x leveraged Gold ETC from US. 

# In[52]:


assets = {
    '1x_gold_eu': "1x Gold", 
    '3x_gold_eu': "3x Gold", 
}


# In[53]:


analyze_gains(etfs.loc['1970':'1986'], assets, "Growth of Gold (EU) ETFs from 1967 to 1986")


# In[54]:


analyze_gains(etfs.loc['1986':], assets, "Growth of Gold (EU) ETFs from 1986 until today")


# In[55]:


analyze_gains(etfs.loc['1970':], assets, "Growth of Gold (EU) ETFs from 1967 until today")


# In[56]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# In[57]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# In[58]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# So it is clear, that also for Europe leveraged Gold ETCs are not an option. 

# ## Long Term Treasury ETFs (US)

# In[59]:


ffr = pd.read_excel(clean_data_path / "ffr.xlsx", index_col=0)
ffr.index = pd.to_datetime(ffr.index)
ffr = ffr['ffr']
ffr


# In[60]:


assets = {
    '1x_ltt_us': "1x LTT", 
    '2x_ltt_us': "2x LTT", 
    '3x_ltt_us': "3x LTT", 
}


# In[61]:


fig = analyze_gains(
    etfs.loc[:'1986'], 
    assets, 
    "Growth of LTT (US) ETFs from 1943 to 1986", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc[:'1986'].index,
        y=ffr.loc[:'1986'],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# As we can see the long term treasury ETFs with leverage factor are suffering enormously from volatility-decay in the years from 1943 to 1986. While the 2x leveraged ETF is still reaching a slightly positive return at 1986, the 3x leveraged ETF is not even reaching breakeven. 
# 
# The strongest downward trend for the leveraged ETFs is starting between 1975 and 1980. This was a time of drastically rising interest rates. 

# In[62]:


fig = analyze_gains(
    etfs.loc['1986':], 
    assets, 
    "Growth of LTT (US) ETFs from 1986 until today", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc['1986':].index,
        y=ffr.loc['1986':],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# In the years after 1986, we can see the oposite effect: interest rates are decreasing and thus long term treasury ETFs are growing. Since it is a time of steady growth the leveraged ETFs are outperfroming the unleveraged ETF drastically. Here the 3x leveraged ETF is the best. 

# In[63]:


analyze_gains(
    etfs.loc[:], 
    assets, 
    "Growth of LTT (US) ETFs from 1943 until today", 
    show=True,
)


# Despite this strong growth of treasury funds after 1986, the leveraged ETFs are not recovering until today from the decline in the years before 1986. Thus it seems, that in general the unleveraged ETF is the best choice. At least without rebalancing. 

# In[64]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# We can see this also in the worst case return over a variable number of investment years: only the unleveraged ETF is able to reach breakeven within 30 years (it takes 17 years), but the worst case performance is with 0.7% very low at year 30. 

# In[65]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# We also see long times of drawdown for all leveraged ETFs. While the unleveraged ETF has just a bad drawdown from 1980 to 1981, the leveraged ETFs show this issue from 1950 or 1949 onwards with 78% and 97% loss in value. 

# In[66]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# The good performance of the unleveraged ETF compared to the leveraged ones can also be seen in the risk/reward chart.

# ## Long Term Treasury ETF (EU)
# 
# In the EU, we don't have leveraged ETFs for LTT. Thus we just look at the unleveraged one and compare it with the US version.

# In[67]:


assets = {
    '1x_ltt_eu': "1x LTT (EU)", 
    '1x_ltt_us': "2x LTT (US)", 
}


# In[68]:


analyze_gains(
    etfs.loc[:'1986'], 
    assets, 
    "Growth of LTT (US/EU) ETFs from 1943 to 1986", 
    show=True,
)


# In[69]:


analyze_gains(
    etfs.loc['1986':], 
    assets, 
    "Growth of LTT (US/EU) ETFs from 1986 until today", 
    show=True,
)


# In[70]:


analyze_gains(
    etfs.loc[:], 
    assets, 
    "Growth of LTT (US/EU) ETFs from 1943 until today", 
    show=True,
)


# We can see that the EU LTT ETFs has a slightly better formance than the US ETF. 

# In[71]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# In[72]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# All other characteristics are more or less the same. 

# ## Intermediate Term Treasury ETFs (US)

# In[73]:


assets = {
    '1x_itt_us': "1x ITT", 
    '2x_itt_us': "2x ITT", 
    '3x_itt_us': "3x ITT", 
}


# In[74]:


fig = analyze_gains(
    etfs.loc[:'1986'], 
    assets, 
    "Growth of ITT (US) ETFs from 1943 to 1986", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc[:'1986'].index,
        y=ffr.loc[:'1986'],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# It is quite hard to see, but the ITT ETFs show a much faster recovery after the interest rates are decreasing than the LTTs. Thus all ETFs have a positive return on 1986, eventhough the leveraged ETFs drop a lot in the years of high interest rates. 

# In[75]:


fig = analyze_gains(
    etfs.loc['1986':], 
    assets, 
    "Growth of LTT (US) ETFs from 1986 until today", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc['1986':].index,
        y=ffr.loc['1986':],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# For the years after 1986 we also see here a strong growth. The 3x leveraged ETF is growing very fast with more than 11% average annual return, which is similar to the unleveraged S&P 500 ETF. 

# In[76]:


analyze_gains(
    etfs.loc[:], 
    assets, 
    "Growth of LTT (US) ETFs from 1943 until today", 
    show=True,
)


# When we combine both periods, the 3x leveraged ETF is still the stronged one. But it had a very hard loss in the beginning of the 1980s.

# In[77]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# The worst case analysis shows a negative image about the leverged ETFs: Only the unleveraged ETF is reaching breakeven, but this already after 7 years. However even after 30 years the worst case return is just 2% per year. 

# In[78]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# The maximum drawdown is for all ETFs during the time of mid. 1970s to beginning 1980s. The 3x leveraged ETF is just losing 75% of its value, which is not too bad compared with other assets. 

# In[79]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# We can clearly see, that every ETF has advantages and disadvantages. With growing leverage factor the risk is increasing and but also the reward. Thus for ITT, there is no clear winner. If we assume a high interest phase is ahead, we should probably take the unleveraged ETF. If we assume the interest rates will still be low in the next years, the 3x leveraged ETF might be a good choise. And if don't know, maybe the 2x leveraged ETF is a good compromise. 

# ## Intermediate Term Treasury ETFs (EU)
# 
# For Europe, we do not have a 2x leveraged ETF, thus we do our analysis only with unleveraged and 3x leveraged ETN. 

# In[80]:


assets = {
    '1x_itt_eu': "1x ITT", 
    '3x_itt_eu': "3x ITT", 
}


# In[81]:


analyze_gains(
    etfs.loc[:'1986'], 
    assets, 
    "Growth of ITT (EU) ETFs from 1943 to 1986", 
    show=True,
)


# Also in Europe the 3x leveraged ETF is able to archive a positive performance end of 1986. However it's gain is almost just the half of the gain from the US ETF. This is due to the high costs of the ETN. 

# In[82]:


analyze_gains(
    etfs.loc['1986':], 
    assets, 
    "Growth of ITT (EU) ETFs from 1986 until today", 
    show=True,
)


# In[83]:


analyze_gains(
    etfs.loc[:], 
    assets, 
    "Growth of ITT (EU) ETFs from 1943 until today", 
    show=True,
)


# Even long term, the 3x leveraged ETN is not able to catch up with the unleveraged ETF. Thus it is more or less clear, that this ETN is not a good investment, unless it is somehow hedged. 

# In[84]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# The worst case analysis is very simialar to the one from the US ETFs. However the unleveraged ETF is already reaching breakeven after 6 instead of 7 years and the 30 years worst case performance is 2.4% per year instead of 2%. So also here the European unleveraged ETF is performing slightly better than the US one. 

# In[85]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# The unleveraged ETF has a maximum drawdown of only 19% while the leveraged ETF has a drawdown of 81% for more than 30 years. 

# In[86]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# So also the risk/reward chart makes it clear, that the unleveraged ETF is the better choice. 

# ## Short Term Treasury ETFs (US vs. EU)
# 
# Since there is no leveraged ETF available for STT, we just compare the EU ETF with the US one. 

# In[87]:


assets = {
    '1x_stt_us': "1x STT (US)", 
    '1x_stt_eu': "1x STT (EU)", 
}


# In[88]:


fig = analyze_gains(
    etfs.loc[:'1986'], 
    assets, 
    "Growth of STT (US/EU) ETFs from 1943 to 1986", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc[:'1986'].index,
        y=ffr.loc[:'1986'],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# And once again: The european ETF is slightly better performaing than the US ETF. In the years from 1943 to 1986 the average annual return was always positive and around 5%, which is similar to the average annual return onf ITT and LTT. 

# In[89]:


fig = analyze_gains(
    etfs.loc['1986':], 
    assets, 
    "Growth of STT (US/EU) ETFs from 1986 until today", 
    show=False,
)
fig.update_yaxes(title_text="interest rate in %", secondary_y=True, showgrid=False, type="linear")
fig.add_trace(
    go.Scatter(
        x=ffr.loc['1986':].index,
        y=ffr.loc['1986':],
        mode='lines',
        name="interest rate",
    ),
    secondary_y=True
)

fig.show()


# In the years after 1986 the returns decreases a little bit to 4-5% While in those years ITT and LTT has an average return of 8% to 11%. 

# In[90]:


analyze_gains(
    etfs.loc[:], 
    assets, 
    "Growth of STT (US/EU) ETFs from 1943 until today", 
    show=True,
)


# Thus also the average return over the whole peride is 4%-5%.

# In[91]:


zero = pd.Series(index=min_returns.index, dtype=np.float64)
zero.loc[:] = 0
data = {
    'zero': zero,
}
for a, n in assets.items():
    data[n] = get_annual_roi(min_returns[a], min_returns.index)    
draw_growth_chart(
    data,
    "Minimum Returns over Years",
    y_log = False,
    y_title = "returns in %",
    x_title = "years holding",
    y_range = [-10, 10],
)


# The good think about STTs is that they reach breakeven very fast. Only 2 (EU) or 3 (EU) yeras are necessary to reach breakeven in the worst case. After 30 years the worst case performance is around 3%, which is higher then the worst case performance of unleveraged LTT and ITT. 

# In[92]:


for a, n in assets.items():
    draw_max_drawdown(a, n)


# In[93]:


draw_risk_reward_chart(
    risk_reward.loc[list(assets.keys()),:],
    "Average Annual Returns vs. Max. Drawdown",
    x_title = "max. drawdown in %",
    y_title = "average annual returns in %"
)


# So it is clear, that the STTs are extremly low risk investments with also low reward. But it is still better to invest in STTs than keeping Cash, which is just burned from inflation. 
