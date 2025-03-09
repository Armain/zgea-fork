#!/usr/bin/env python
# coding: utf-8

# # Prepare Data for Anaylsis
# 
# In the last notebooks, we created simulated U.S. Treausry Bond fund values from beginngin 1943 until today. Now we collect also the data from other data-sources, like S&P500, Nasdaq-100 and Gold.

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import pandas.tseries.offsets as pd_offsets
from dateutil.relativedelta import relativedelta


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart
from utils.data import read_csv, download_from_yahoo, download_from_investing, read_excel, download_from_nasdaq
from utils.data import download_from_fred
from utils.math import reindex_and_fill, normalize, calc_growth, calc_returns, add_dividends, to_float, gmean
from utils.math import reindex_and_interpolate


# In[3]:


data = pd.DataFrame()


# ## Add Treasury Bond Data 

# In[4]:


clean_data_path = Path("clean_data")
raw_data_path = Path("raw_data")


# In[5]:


bonds_path = clean_data_path / "bond_funds.xlsx"
bonds = pd.read_excel(bonds_path, index_col = 0)
bonds.index = pd.to_datetime(bonds.index)
bonds.head()


# In[6]:


data['stt_us'] = bonds['stt_us']
data['itt_us'] = bonds['itt_us']
data['ltt_us'] = bonds['ltt_us']
data['stt_eu'] = bonds['stt_eu']
data['itt_eu'] = bonds['itt_eu']
data['ltt_eu'] = bonds['ltt_eu']
data.head()


# In[7]:


first_date = min(data.index)
last_date = max(data.index)
print(f"First Date is: {first_date}")
print(f"Last Date is: {last_date}")


# In[8]:


draw_growth_chart(
    {
        'ltt': data['ltt_eu'],
        'itt': data['itt_eu'],
        'stt': data['stt_eu'],
    },
    "Growth of U.S. Treasury Bond Funds"
)


# ## Add S&P500 Data
# 
# For the S&P 500 data, we have a CSV file with historical data from 1927 until 2021 without dividends. But we will also load the latest data from yahoo directly and concat this to an S&P 500 series without dividends. 
# 
# Afterwards we create a time-series with the same length, which has dividends included (reinvested), which corresponds to the S&P 500 Total Return index. 

# In[9]:


sp500_1 = read_csv(raw_data_path / "s&p500_raw.csv", "Adj Close**", sep=";")
sp500_1


# In[10]:


sp500_2 = download_from_yahoo("^GSPC", name="s&p500_raw")
sp500_2


# All S&P 500 data is given as daily data. However, also here some days have missing values and also days, where the market was closed is missing. Thus we will fill the gaps.

# In[11]:


sp500_1 = reindex_and_fill(sp500_1, min(sp500_1.index), max(sp500_1.index), freq="D")
sp500_1


# In[12]:


sp500_2 = reindex_and_fill(sp500_2, min(sp500_2.index), max(sp500_2.index), freq="D")
sp500_2


# Now we check, if both are aligned with eachother.

# In[13]:


draw_growth_chart(
    {
        'sp500_1': sp500_1,
        'sp500_2': sp500_2
    },
    "Compare S&P 500 from two sources (Growth Chart)",
    overlapping_only = True
)
draw_telltale_chart(
    sp500_1,
    {
        'sp500_2': sp500_2
    },
    "Compare S&P 500 from two sources (Telltale Chart) ",
    overlapping_only = True,
    y_range = [-1,1],
    y_log = False
)


# In the overlapping region this is a perfect fit. But this is clear, since both datasets are coming from yahoo finance. Not we can combine both to get the whole history and also the most recent values. 

# In[14]:


sp500 = pd.Series(
    index=pd.date_range(
        min(min(sp500_1.index), min(sp500_2.index)),
        max(max(sp500_1.index), max(sp500_2.index)),
        freq="D",
    ),
    dtype=np.float64,
    name="sp500"
)
sp500.loc[min(sp500_1.index):max(sp500_1.index)] = sp500_1
sp500.loc[min(sp500_2.index):max(sp500_2.index)] = sp500_2
sp500


# In[15]:


data['sp500'] = normalize(sp500.loc[first_date:last_date], start_value=100)
data.head()


# In[16]:


draw_growth_chart(
    {
        'ltt': data['ltt_eu'],
        's&p500': data['sp500'],
    },
    "Growth LTT vs. S&P 500"
)


# ## Add S&P 500 Total Return
# 
# Many stocks inside the S&P 500 index are paying dividends along the year. However those dividends are not reinvested inside the S&P 500. If we want to know the total returns of the S&P 500, we have to take those dividends into account and also reinvest them for upcoming days and years. 
# 
# On yahoo finance the S&P 500 Total Return index is available. However the starting time of this time-series is not 1943 but 1988. So, we have to simulate the years before 1988 by adding the payed dividends to the normal S&P 500 returns. Then we can compare our constructed total return index in the overlapping area with the real one and merge them together.

# In the first step, we download the real S&P 500 Total Return index from yahoo.

# In[17]:


sp500_tr_1 = download_from_yahoo("^SP500TR", name="s&p500_tr")
sp500_tr_1


# Here again, we have to reindex and fill missing values, like weekends or bank holidays.

# In[18]:


sp500_tr_1 = reindex_and_fill(sp500_tr_1, min(sp500_tr_1.index), max(sp500_tr_1.index), "D")
sp500_tr_1


# Then we load the dividend payments of the S&P 500 from the past. It is stored in a CSV file.

# In[19]:


def map_month_names(indices):
    month={
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
    }
    def map_single_index(index):
        index = str(index)
        for month_name, month_number in month.items():
            if month_name in index:
                return index.replace(month_name, str(month_number)+',').strip()
        return index.strip()
    return pd.to_datetime([map_single_index(i) for i in indices], format="%m, %d, %Y")
    

def convert_percent(value):
    return float(str(value).replace("%",""))/100
    

sp500_div = read_csv(
    raw_data_path / "s&p500_dividends.csv", 
    column_name = 'percent',
    sep = ";", 
    index_mapping = map_month_names,
    value_mapping = convert_percent,
)
sp500_div


# The dividends are defined monthly as percentage. We will now calculate the daily returns of the S&P 500. Then we can iterate over the dividends and add 1/365 of every the percentage-dividends to the returns of the same month. This logic is done in function, since we might need this logic later also for other assets. 

# In[20]:


sp500_tr_sim = add_dividends(calc_returns(sp500), sp500_div)
sp500_tr_sim = calc_growth(sp500_tr_sim, start_value=sp500.iloc[0])
sp500_tr_sim


# In[21]:


draw_growth_chart(
    {
        'S&P 500 Total Return': normalize(sp500_tr_1, sp500_tr_sim),
        's&p 500 + Div': sp500_tr_sim,
    },
    "Growth Chart S&P 500",
    overlapping_only=True,
)
draw_telltale_chart(
    normalize(sp500_tr_1, sp500_tr_sim),
    {        
        's&p 500 + Div': sp500_tr_sim,
    },
    "Telltale Chart S&P 500 (Reference: Total Return Index)",
    overlapping_only=True,
    y_log=False,
)


# As we can see, we are now reaching the right magnitude, but our simulated total return index is diverging a little bit.  The reason for that is unclear. Maybe the dividend tracking is slightly wrong, or the day, when the dividends must be added is not 100 percent correct. After trying different possibilities, I decided to just add a very small positive adjustment factor to the dividends. The factor is 0.075% per year. 

# In[22]:


sp500_tr_sim = add_dividends(calc_returns(sp500), sp500_div, adjustment_factor=0.075/100)
sp500_tr_sim = calc_growth(sp500_tr_sim, start_value=sp500.iloc[0])
sp500_tr_sim


# In[23]:


draw_growth_chart(
    {
        'S&P 500 Total Return': normalize(sp500_tr_1, sp500_tr_sim),
        's&p 500 + Div': sp500_tr_sim,
    },
    "Growth Chart S&P 500",
    overlapping_only=True,
)
draw_telltale_chart(
    normalize(sp500_tr_1, sp500_tr_sim),
    {        
        's&p 500 + Div': sp500_tr_sim,
    },
    "Telltale Chart S&P 500 (Reference: Total Return Index)",
    overlapping_only=True,
    y_log=False,
)


# We have almost a perfect fit. So we can combine the simulated total return index with the real one.

# In[24]:


sp500_tr = pd.Series(
    index=pd.date_range(
        min(min(sp500_tr_1.index), min(sp500_tr_sim.index)),
        max(max(sp500_tr_1.index), max(sp500_tr_sim.index)),
        freq="D",
    ),
    dtype=np.float64,
    name="sp500+div"
)
sp500_tr.loc[min(sp500_tr_sim.index):max(sp500_tr_sim.index)] = sp500_tr_sim
sp500_tr.loc[min(sp500_tr_1.index):max(sp500_tr_1.index)] = normalize(sp500_tr_1, sp500_tr_sim)
sp500_tr


# In[25]:


draw_growth_chart(
    {
        'S&P 500 + Div': sp500_tr,
        's&p 500 + Div (sim)': sp500_tr_sim,
        's&p 500 + Div (real)': normalize(sp500_tr_1, sp500_tr_sim),
    },
    "Growth Chart S&P 500",
)


# We can now normalize the simulated total return index and store it in our data-set.

# In[26]:


data['sp500+div'] = normalize(sp500_tr_sim.loc[first_date:last_date], start_value=100)
data.head()


# In[27]:


draw_growth_chart(
    {
        's&p500': data['sp500'],
        's&p500+div': data['sp500+div'],
    },
    "Growth S&P 500 with and without dividends"
)


# ## Add Nasdaq-100 Data
# 
# As next step, we prepare the Nasdaq-100 data. We have file with historical data and we also can reload most recent data from yahoo. Both data-sets can easily combined with eachother. 
# 
# Both data-sets contain daily data, but here again we have several gaps inside. So before combining the data we reindex it to every day data and fill the gaps as we did it with S&P 500.

# In[28]:


nd100_1 = read_csv(raw_data_path / "nasdaq-100.csv", "Adj Close")
nd100_1


# In[29]:


nd100_1 = reindex_and_fill(nd100_1, min(nd100_1.index), max(nd100_1.index), "D")
nd100_1


# In[30]:


nd100_2 = download_from_yahoo("NDX")
nd100_2


# In[31]:


nd100_2 = reindex_and_fill(nd100_2, min(nd100_2.index), max(nd100_2.index), "D")
nd100_2


# In[32]:


draw_growth_chart(
    {
        'nasdaq-100 (source 1)': nd100_1,
        'nasdaq-100 (source 2)': nd100_2,
    },
    "Growth Chart of Nasdaq-100"
)
draw_telltale_chart(
    nd100_1,
    {
        'nasdaq-100 (source 2)': nd100_2,
    },
    "Telltale Chart Nasdaq-100 (reference: source 1)",
    overlapping_only=True,
    y_range=[-2, 2]
)


# We habe an almost perfect fit. Only on some days in November and December 2021 there is a small difference of 1%. This does not change the overall result. So we can easily fit the data and just overwrite the most recent dates with the most recent data.

# In[33]:


nd100 = pd.Series(
    index=pd.date_range(
        min(min(nd100_1.index), min(nd100_2.index)),
        max(max(nd100_1.index), max(nd100_2.index)),
        freq="D",
    ),
    dtype=np.float64,
)
nd100.loc[min(nd100_1.index):max(nd100_1.index)] = nd100_1
nd100.loc[min(nd100_2.index):max(nd100_2.index)] = nd100_2
nd100


# The next problem is, that the nasdaq-100 is just available from October 1985. Before the index did not exist. So if we want to use this index directly in our data, we would have a huge gap from 1944 to 1985 without data for it. This would make backtesting with the nasdaq-100 quite complicated. Thus we will fill the data just with the data from S&P 500. With this we bring in a huge assumption, we must not forget later, when we interpret our results: The assumption is, that everyone who invested later in the nasdaq-100 would have chosen the s&p 500 as substitute before. 

# In[34]:


data['ndx100'] = data['sp500']
data


# In[35]:


first_ndx100_date = min(nd100.index)
data.loc[first_ndx100_date:, 'ndx100'] = normalize(nd100, data['sp500'])
data


# In[36]:


draw_growth_chart(
    {
        'ltt': data['ltt_eu'],
        'nasdaq-100': data['ndx100'],
        's&p500': data['sp500'],
    },
    "Growth LTT vs. S&P 500 vs. Nasdaq-100"
)


# ## Nasdaq-100 Total Return Index
# 
# Also some companies in the Nasdaq-100 are paying dividends. Thus we have to create a total return index for it, which contains those dividends. Unfortunately the history of the Nasdaq-100 Total Return Index is not available on yahoo-finance, but on investing.com. 
# 
# On investing.com, we can download the Nasdaq-100 Total Return index starting from 1999. Unfortunately, the system only divers at maximum 20 years. So I prepared two csv files from investing.com, which contains the years 1999-2019 and 2009 until beginning of 2022. Furthermore we can load the most recent changes of this index, directly from investing.com to update the data. 
# 
# Afterwards we have to reindex, fill and combine the data from all three sources.

# In[37]:


nd100_tr_1 = read_csv(raw_data_path / "nasdaq-100-tr_1.csv", column_name="Price")
nd100_tr_1


# In[38]:


nd100_tr_2 = read_csv(raw_data_path / "nasdaq-100-tr_2.csv", column_name="Price")
nd100_tr_2


# In[39]:


nd100_tr_3 = download_from_investing('nasdaq-100-tr', start_date="01-01-2019")
nd100_tr_3


# In[40]:


nd100_tr_1 = reindex_and_fill(nd100_tr_1, min(nd100_tr_1.index), max(nd100_tr_1.index), freq="D")
nd100_tr_1


# In[41]:


nd100_tr_2 = reindex_and_fill(nd100_tr_2, min(nd100_tr_2.index), max(nd100_tr_2.index), freq="D")
nd100_tr_2


# In[42]:


nd100_tr_3 = reindex_and_fill(nd100_tr_3, min(nd100_tr_3.index), max(nd100_tr_3.index), freq="D")
nd100_tr_3


# In[43]:


nd100_tr_real = pd.Series(
    index=pd.date_range(
        min(min(nd100_tr_1.index), min(nd100_tr_2.index), min(nd100_tr_3.index)),
        max(max(nd100_tr_1.index), max(nd100_tr_2.index), max(nd100_tr_3.index)),
    ),
    dtype=np.float64,
    name = "nd100_tr",
)
nd100_tr_real.loc[min(nd100_tr_1.index):max(nd100_tr_1.index)] = nd100_tr_1
nd100_tr_real.loc[min(nd100_tr_2.index):max(nd100_tr_2.index)] = nd100_tr_2
nd100_tr_real.loc[min(nd100_tr_3.index):max(nd100_tr_3.index)] = nd100_tr_3
nd100_tr_real


# In[44]:


draw_growth_chart(
    {
        'nasdaq-100': nd100,
        'nasdaq-100 total return (real)': nd100_tr_real,
    },
    "Nasdaq-100 (with and without dividends)"
)
first_common_date = max(min(nd100.index), min(nd100_tr_real.index))
print(f"Value on first day ({first_common_date}): ${nd100.loc[first_common_date]:.2f} vs. ${nd100.loc[first_common_date]:.2f}")


# As we can see the Total Return index of the Nasdaq-100 starts at the same value as the normal Nasdaq-100 index at it first day and is then adding up dividends. To get a realistic total return growth from the beginning of the Nasdaq-100 in 1985, we would at least need the yearly dividends, which have been payed for the Nasdaq-100. However I was not able to find this information anywhere.
# 
# Thus we have to simulate a realistic dividend time-line for the years from 1985 to 1999. As proxy for the dividends in this year, we could use the S&P 500 dividends. However, we need to scale them that they are fitting to the ranges of the Nasdaq-100. For this we calculate first the dividends payed in Nasdaq-100 as monthly percentage values. Then we can calcualte the annual average of the payed dividends. 
# 
# We do the same for the S&P 500 in the same periode and this helps us to calculate a scaling factor out of it. Then we apply the S&P 500 dividends with this scaling factor to the Nasdaq-100 without dividends.
# 
# Is is absolutly clear, that this will not give us a accurate Total Return index for the Nasdaq-100. However it will give us at least reasonable numbers. The good think about this is, that exactly when the year 2000 dot-com crisis started, we can switch over to the real Total Retrun index.

# In[45]:


first_common_date = max(min(nd100.index), min(nd100_tr_real.index)) + pd_offsets.MonthEnd(0)
nd100_dividends_real = calc_returns(nd100_tr_real.loc[first_common_date:], freq="M") - calc_returns(nd100.loc[first_common_date:], freq="M")
nd100_average_dividends = gmean(nd100_dividends_real)
nd100_average_dividends


# In[46]:


sp500_dividends = calc_returns(sp500_tr_sim, freq="M") - calc_returns(sp500, freq="M")
sp500_dividends


# In[47]:


sp500_average_dividends = gmean(sp500_dividends.loc[first_common_date:])
sp500_average_dividends


# In[48]:


nd100_dividends = sp500_dividends.loc[min(nd100.index):]
nd100_dividends = (nd100_dividends * nd100_average_dividends)/sp500_average_dividends
nd100_dividends


# In[49]:


nd100_dividends.loc[first_common_date:] = nd100_dividends_real
nd100_dividends


# In[50]:


nd100_tr_sim = add_dividends(calc_returns(nd100, freq="D"), nd100_dividends, monthly=True)
nd100_tr_sim = calc_growth(nd100_tr_sim, start_value=nd100.iloc[0])
nd100_tr_sim


# In[51]:


draw_growth_chart(
    {
        'nasdaq-100': nd100,
        'nasdaq-100 total return (sim)': nd100_tr_sim,
        'nasdaq-100 total return (real)': normalize(nd100_tr_real, nd100_tr_sim),
    },
    "Nasdaq-100 (with and without dividends)"
)
draw_telltale_chart(
    normalize(nd100_tr_real, nd100_tr_sim),
    {
        'nasdaq-100 total return (sim)': nd100_tr_sim,
    },
    "Nasdaq-100 Telltale Chart (Reference: real total return index)",
    overlapping_only=True,
)


# The overlapping region between the simulated and real Total Return index looks very good. From 2012 on it diverges a little bit, but the error is very small at max. 0.2% after more then 30 years. Also the simulated timeline before 1999 looks reasonable. Eventhough we know, that we cannot get accurate numbers with it, it will give us a good feeling about the theoretical performance the Nasdaq-100 Total Return index could have at that time. 
# 
# Now we can concat the simulated and real Total Return index.

# In[52]:


nd100_tr = pd.Series(
    index=pd.date_range(
        min(min(nd100_tr_real.index), min(nd100_tr_sim.index)),
        max(max(nd100_tr_real.index), max(nd100_tr_sim.index)),
        freq="D",
    ),
    dtype=np.float64,
    name="nd100+div"
)
nd100_tr.loc[min(nd100_tr_sim.index):max(nd100_tr_sim.index)] = nd100_tr_sim
nd100_tr.loc[min(nd100_tr_real.index):max(nd100_tr_real.index)] = normalize(nd100_tr_real, nd100_tr_sim)
nd100_tr


# The last step is to concat the time before 1985 with the S&P 500 Total Return index, as we did this already with the pure Nasdaq-100 and then we can store the time-series inside our data-frame. 

# In[53]:


data['ndx100+div'] = data['sp500+div']
first_ndx100_tr_date = min(nd100_tr.index)
data.loc[first_ndx100_tr_date:, 'ndx100+div'] = normalize(nd100_tr, data['sp500+div'])
data


# In[54]:


draw_growth_chart(
    {
        'ltt': data['ltt_eu'],
        'nasdaq-100 total return': data['ndx100+div'],
        's&p500 total return': data['sp500+div'],
    },
    "Growth LTT vs. S&P 500 vs. Nasdaq-100"
)


# ## Add Gold Data
# 
# For the Gold data, we have 4 different sources:
# * annual data from http://www.nma.org/pdf/gold/his_gold_prices.pdf, which contains the gold price starting from 1833 to 2011
# * daily data from an unknown web source starting from 1970 to Nov. 2021
# * daily data from the nasdaq api starting from 2012 until today
# 
# We have to combine all those sources to a single source. First we load the annual data and interpolate it to daily data. Especially in the early years the gold price was anyway very stable, so interpolating it to daily data, should not harm our later analysis.

# In[55]:


gold = pd.DataFrame()


# In[56]:


gold1 = read_excel(
    raw_data_path / "gold_yearly.xlsx", 
    column_name="gold",
    index_mapping= lambda v: pd.to_datetime(v, format="%Y"),
    skiprows=1,
)
gold1


# In[57]:


gold1 = reindex_and_interpolate(gold1, min(gold1.index), max(gold1.index), "D")
gold1


# In[58]:


draw_growth_chart(
    {
        'gold1': gold1,
    },
    "Growth of Gold depending on Source"
)


# In[59]:


gold = gold1.copy()
gold


# Now we load the data from the unknown web source. This data is already daily, thus we just need to fill the gaps. Then we bring the data to the same scale as the current data and compare it in a growth chart with our current curve. If it fits the current curve, we substitute the data inside our target dataframe by the new data, starting from the first date of the new data.

# In[60]:


gold2 = read_excel(
    raw_data_path / "gold_web.xlsx", 
    column_name="value",
    index_mapping=lambda v: pd.to_datetime(pd.to_datetime(v).date)
)
gold2 = reindex_and_fill(gold2, min(gold2.index), max(gold2.index), "D")
gold2


# In[61]:


assert not gold2.isna().any().any()


# In[62]:


gold2 = normalize(gold2, gold)
gold2


# In[63]:


draw_growth_chart(
    {
        'gold1': gold1,
        'gold2': gold2,
    },
    "Growth of Gold depending on Source"
)


# In[64]:


gold = gold.reindex(pd.date_range(min(gold.index), max(gold2.index), freq="D"))
gold.loc[min(gold2.index):] = gold2
gold


# As a last step we load the data from the nasdaq. Also here we fill the gaps and scale it to the same values as our current data. Then we compare it in a growth graph with the other sources and add it to the target dataframe.

# In[66]:


gold3 = download_from_nasdaq("LBMA/GOLD", column_name="USD (PM)")
gold3 = reindex_and_fill(gold3, min(gold3.index), max(gold3.index), "D")
gold3


# In[67]:


assert not gold3.isna().any().any()


# In[68]:


gold3 = normalize(gold3, gold)


# In[70]:


draw_growth_chart(
    {
        'gold1': gold1,
        'gold2': gold2,
        'gold3': gold3,
    },
    "Growth of Gold depending on Source"
)


# In[71]:


gold = gold.reindex(pd.date_range(min(gold.index), max(gold3.index), freq="D"))
gold.loc[min(gold3.index):] = gold3
gold


# Now we can scale add it to the existing data.

# In[72]:


data['gold'] = normalize(gold.loc[min(data.index):max(data.index)], start_value=100)
data


# In[73]:


draw_growth_chart(
    {
        'ltt': data['ltt_eu'],
        's&p500': data['sp500'],
        'nasdaq-100': data['ndx100'],
        's&p500 (incl. dividends)': data['sp500+div'],
        'nasdaq-100 (incl. dividends)': data['ndx100+div'],
        'gold': data['gold'],
    },
    "Growth LTT vs. S&P 500 vs. Nasdaq-100 vs. Gold"
)


# We have collected all data we need for our analysis and can now store the data.

# In[74]:


assets_output_path = clean_data_path / "assets.xlsx"
data.to_excel(assets_output_path)


# ## Inflation Rate
# 
# Beside of the assets data, we might also need some other data for our analysis, like the inflation rate. 
# 
# The U.S. inflation rate is also given from two sources: 
#  * A table with monthly year-over-year values, where the years are the rows and the month are columns. 
#  * From the Nasdaq, we can query the most recent data directly as dataframe.
# 
# We start with the first souce, the table. Here we will transform it from a wide table to a long table, where we have a value for every month. Furthermore we interpolate it for daily data.

# In[76]:


inflation_path = raw_data_path / "us_inflation.csv"
inflation1 = pd.read_csv(inflation_path, sep=';', index_col=0)
inflation1


# In[77]:


inflation1 = inflation1.rename(columns=lambda c: c.strip())
month_mapping = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
}
inflation1 = inflation1.rename(columns=month_mapping)
inflation1 


# In[78]:


inflation1 = inflation1.drop(columns=["Ave"])
inflation1 = inflation1.stack()
inflation1.index = [f'{y}-{m}' for y, m in inflation1.index]
inflation1


# In[79]:


inflation1.index = pd.to_datetime(inflation1.index, format="%Y-%m")
inflation1


# In[80]:


inflation1.name = "yoy"
inflation1 = inflation1.apply(to_float)
inflation1 = reindex_and_interpolate(inflation1, min(inflation1.index), max(inflation1.index), freq="D")
inflation1


# Now we load the most recent data from Nasdaq and combine it with this inflation data.

# In[81]:


inflation2 = download_from_nasdaq("RATEINF/INFLATION_USA", column_name="Value")
inflation2 = reindex_and_interpolate(inflation2, min(inflation2.index), max(inflation2.index), freq="D")
inflation2


# In[82]:


inflation_yoy = pd.Series(
    index = pd.date_range(
        min(min(inflation1.index), min(inflation2.index)),
        max(max(inflation2.index), max(inflation2.index)),
        freq="D",
    ),
    name = "yoy",
    dtype = np.float64,
)
inflation_yoy.loc[min(inflation1.index):max(inflation1.index)] = inflation1
inflation_yoy.loc[min(inflation2.index):max(inflation2.index)] = inflation2
inflation_yoy


# In[83]:


draw_growth_chart(
    {
        'inflation (yoy)': inflation_yoy
    },
    "Inflation Rate (YoY)",
    y_log=False,
)


# Now, we load and add the CPI (customer price index). Also here we have two sources: 
#  * A file from FRED with historical data.
#  * The current data, directly downloaded from FRED.
#  
# We start by reading the stroed hinstorical data.

# In[85]:


cpi1 = read_csv(raw_data_path / "CPIAUCNS.csv", column_name="CPIAUCNS")
cpi1 = reindex_and_interpolate(cpi1, min(cpi1.index), max(cpi1.index), freq="D")
cpi1


# Now we load the most recent data directly from FRED.

# In[86]:


cpi2 = download_from_fred("CPIAUCNS")
cpi2 = reindex_and_interpolate(cpi2, min(cpi2.index), max(cpi2.index), freq="D")
cpi2


# In[87]:


cpi = pd.Series(
    index=pd.date_range(
        min(min(cpi1.index), min(cpi2.index)),
        max(max(cpi1.index), max(cpi2.index)),
        freq="D",
    ),
    name="cpi",
    dtype=np.float64,
)
cpi.loc[min(cpi1.index):max(cpi1.index)] = cpi1
cpi.loc[min(cpi2.index):max(cpi2.index)] = cpi2
cpi


# In[88]:


inflation = pd.DataFrame(
    index=pd.date_range(
        min(data.index),
        max(data.index),
        freq="D",
    ),
    columns=['yoy', 'cpi']
)
inflation['yoy'] = inflation_yoy.loc[min(data.index):max(data.index)]
inflation['cpi'] = normalize(cpi.loc[min(data.index):max(data.index)], start_value=100)
inflation = reindex_and_fill(inflation, min(inflation.index), max(inflation.index), freq="D")
inflation


# In[89]:


draw_growth_chart(
    {
        'inflation in % (yoy)': inflation['yoy'],
    },
    "Inflation in % (YoY)",
    y_log = False,
    y_title = "percent",
)
draw_growth_chart(
    {
        'cpi': inflation['cpi'],
    },
    "Inflation (CPI)",
)


# In[90]:


inflation_output_path = clean_data_path / "inflation.xlsx"
inflation.to_excel(inflation_output_path)


# ## Federal Funds Rate (U.S. base interest rate)
# 
# We also could need the federal funds rate (ffr) for our analysis. The effective federal funds rate from 1954 until today is given as monthly data. For the years before, there is only the low and high federaul funds rate as monthly data. Due to a lack of knowledge about the system behind, it is hard to understand the differences between both.
# However, for the sake of simplicity, we will just assume the low federal funds rate is the same as the effective federal funds rate, thus we can combine both data. Eventually the low federal funds rate, just needs to be scaled to the same value region as the effective one.
# 
# We start to load the effective federal funds rate. As usual, we are using two sources. First a file and then we query the latest data from FRED directly and combine both.

# In[91]:


effr1 = read_csv(raw_data_path / "FEDFUNDS.csv", column_name="FEDFUNDS")
effr1 = reindex_and_interpolate(effr1, min(effr1.index), max(effr1.index), freq="D")
effr1


# In[92]:


effr2 = download_from_fred("FEDFUNDS")
effr2 = reindex_and_interpolate(effr2, min(effr2.index), max(effr2.index), freq="D")
effr2


# In[93]:


draw_growth_chart(
    {
        'effr1': effr1,
        'effr2': effr2,
    },
    "The effective federal funds rate (comparison of sources)"
)


# In[94]:


effr = pd.Series(
    index=pd.date_range(
        min(min(effr1.index), min(effr2.index)),
        max(max(effr1.index), max(effr2.index)),
        freq="D",
    ),
    dtype=np.float64,
    name="effr"
)
effr.loc[min(effr1.index):max(effr1.index)] = effr1
effr.loc[min(effr2.index):max(effr2.index)] = effr2
effr


# Now we load the low federal funds rate in the same way.

# In[95]:


lffr = read_csv(raw_data_path / "FFWSJLOW.csv", column_name="FFWSJLOW")
lffr = lffr.ffill().bfill()
lffr


# As we can see, the low federal funds rate is sometimes given daily with quite different values. We will smooth this, by calculating the monthly average value.

# In[96]:


lffr = lffr.groupby([lffr.index.year, lffr.index.month]).mean()
lffr.index = lffr.index = [f'{y}-{m}' for y, m in lffr.index]
lffr


# In[97]:


lffr.index = pd.to_datetime(lffr.index, format="%Y-%m")
lffr


# In[98]:


lffr = reindex_and_interpolate(lffr, min(lffr.index), max(lffr.index), freq="D")
lffr


# In[99]:


draw_growth_chart(
    {
        'lffr': lffr,
        'effr': effr,
    },
    "Federal Funds Rate (in %)",
    y_log = False,
    y_title = "percent",
)


# The transition between both rates in 1954 does not look very nice, but at least reasonable. Maybe the concept behind the low ferderal funds rate is a little bit different than the effective one, but at least it is in the same value range and thus gives an qualitative understanding how the effective federal funds rate was at that time. We now can merge both series, forward fill it to daily data and restrict the range to the same range we use for the assets data.

# In[100]:


ffr = pd.DataFrame(
    index = pd.date_range(
        min(lffr.index), 
        max(effr.index), 
        freq="D"
    )
)
ffr.loc[min(lffr.index):max(lffr.index),'ffr'] = lffr
ffr.loc[min(effr.index):max(effr.index),'ffr'] = effr
ffr


# In[101]:


ffr = reindex_and_fill(ffr, min(data.index), max(data.index), "D")
ffr


# In[102]:


draw_growth_chart(
    {
        'ffr': ffr['ffr'],
    },
    "Federal Funds Rate (in %)",
    y_log = False,
    y_title = "percent",
)


# In[103]:


ffr_output_path = clean_data_path / "ffr.xlsx"
ffr.to_excel(ffr_output_path)


# ## The Overnight Borrowing Rate
# 
# Since we want to model leveraged ETFs later, we need the overnight borrowing rate to estimate the borrowing costs of a leveraged ETF. This data is given by the LIBOR overnight values from FRED. However the history is quite short. But since the values are more or less in the same region like the effective federal funds rate, we can use the EFFR as proxy for the years before. 
# 
# Here again, we read the LIBOR data from a csv file and load the most recent data from FRED directly. 

# In[105]:


libor1 = read_csv(raw_data_path / "USDONTD156N.csv", column_name="USDONTD156N")
libor1 = reindex_and_fill(libor1, min(libor1.index), max(libor1.index), freq="D")
libor1


# In[106]:


libor2 = download_from_fred("USDONTD156N")
libor2 = reindex_and_fill(libor2, min(libor2.index), max(libor2.index), freq="D")
libor2


# In[107]:


draw_growth_chart(
    {
        'libor1': libor1,
        'libor2': libor2,
    },
    "The overnight LIBOR (comparison between sources)"
)


# In[108]:


borrowing_rate = pd.DataFrame(
    index=pd.date_range(
        min(min(ffr.index), min(libor1.index), min(libor2.index), min(data.index)),
        max(max(ffr.index), max(libor1.index), max(libor2.index), max(data.index)),
        freq="D",
    ),
    dtype=np.float64,
    columns=["borrowing_rate"]
)
borrowing_rate.loc[min(ffr.index):max(ffr.index), "borrowing_rate"] = ffr['ffr']
borrowing_rate.loc[min(libor1.index):max(libor1.index), "borrowing_rate"] = libor1
borrowing_rate.loc[min(libor2.index):max(libor2.index), "borrowing_rate"] = libor2
borrowing_rate = borrowing_rate.loc[min(data.index):max(data.index),:]
borrowing_rate = reindex_and_fill(borrowing_rate, min(data.index), max(data.index), freq="D")
borrowing_rate


# In[109]:


draw_growth_chart(
    {
        'ffr': ffr['ffr'],
        'borrowing rate': borrowing_rate["borrowing_rate"],
    },
    "FFR vs. Borrowing Rate"
)
draw_telltale_chart(
    ffr['ffr'],
    {        
        'borrowing rate': borrowing_rate["borrowing_rate"],
    },
    "Telltale Chart Borrowing Rate (reference: FFR)"
)


# While both curves are in general following each other, there are sometimes huge differences, which spikes in the telltale chart. Especially the in finanical crises 2008 we see very huge spikes. Thus using the borrowing rate instead of the FFR, will give us a higher accuracy at thos days, when we model leveraged ETFs. 

# In[110]:


borrowing_rate.to_excel(clean_data_path / "borrowing_rate.xlsx")


# ## Original HFEA Data
# 
# Headefundie added the original data for his/her backtest to the thread https://www.bogleheads.org/forum/viewtopic.php?f=10&t=272007 and for comparison reasons, we now add this data to our clean data. In this way we always have some kind of reference.

# In[112]:


upro = read_csv(
    raw_data_path / "UPROSIM.csv", 
    column_name="UPRO", 
    value_mapping=lambda v: to_float(v.replace("%", ""))/100
)
upro = upro.reindex(pd.date_range(min(upro.index), max(upro.index), freq="D"))
upro = upro.fillna(value=0)
upro = calc_growth(upro)
upro = normalize(upro.loc['1986-12-31':'2019-01-31'], start_value=100)
upro


# In[113]:


raw_data_path = Path("raw_data")
tmf = read_csv(
    raw_data_path / "TMFSIM.csv", 
    column_name="TMF", 
    value_mapping=lambda v: to_float(v.replace("%", ""))/100
)
tmf = tmf.reindex(pd.date_range(min(upro.index), max(upro.index), freq="D"))
tmf = tmf.fillna(value=0)
tmf = calc_growth(tmf)
tmf = normalize(tmf.loc['1986-12-31':'2019-01-31'], start_value=100)
tmf


# In[114]:


hfea_data = pd.DataFrame(columns=['TMF', 'UPRO'])
hfea_data.loc[:, 'TMF'] = tmf
hfea_data.loc[:, 'UPRO'] = upro
hfea_data


# In[115]:


hfea_data.to_excel(clean_data_path / "hfea_data.xlsx")

