#!/usr/bin/env python
# coding: utf-8

# # Yield Curve Calculation
# 
# This notebook calculates daily yield curves for US Treasury Bonds. It takes data from two sources:
# 
# * Bogleheads, yield curves book data: https://drive.google.com/file/d/1azbWYdUDHjjtgxJ-logORbsGOmKanqxJ/view
#     * This excel sheet was created by using two sources:
#         * Historical US Treasury Yield Curves, 1993 Edition, Thomas Coleman and al.
#         * Table 9-2, Estimated PAR Bond Yields, Fully Taxable, pages 116 to 129
# * Market Yield on U.S. Treasury Securities at x-Year Constant Maturity (DGSx) from FRED (https://fred.stlouisfed.org/categories/22)
# 
# The data of both sources are combined in this notebook, to generate the yield curve for 1 year, 3 years, 5 years, 7 years, 10 years, 20 years and 30 years treasury bonds. In order to verify, if the data from one sources aligns with the data from the other source, the overlapping years are accumulated and shown in a growth chart.
# 
# The data is combined by using a linear interpolation between two data-points inside the overlapping region.

# In[1]:


from pathlib import Path
import pandas as pd
import pandas.tseries.offsets as pd_offsets
import numpy as np
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from typing import Dict


# In[2]:


from utils.math import reindex_and_fill, reindex_and_interpolate, calc_growth, normalize
from utils.data import download_from_fred, read_csv, merge_series
from utils.plots import draw_growth_chart, draw_telltale_chart


# The first step is to load all data into memory.

# In[3]:


raw_data_path = Path("raw_data")
clean_data_path = Path("clean_data")
bogleheads_yield_curve_path = raw_data_path / "bogleheads_yield_curves.xlsx"
gs1_path = raw_data_path / "DGS1.csv"
gs3_path = raw_data_path / "DGS3.csv"
gs5_path = raw_data_path / "DGS5.csv"
gs7_path = raw_data_path / "DGS7.csv"
gs10_path = raw_data_path / "DGS10.csv"
gs20_path = raw_data_path / "DGS20.csv"
gs30_path = raw_data_path / "DGS30.csv"


# In[4]:


bg_yield_curve = pd.read_excel(bogleheads_yield_curve_path, skiprows=1)
bg_yield_curve['date'] = pd.to_datetime(bg_yield_curve['date'], format="%Y")
bg_yield_curve.index = bg_yield_curve['date']
bg_yield_curve.drop(columns=['date'], inplace=True)
bg_yield_curve.head()


# The bogleheads yield curves are just given as monthly data. Thus, we need to bring it to daily data somehow. For this we have actually 3 alternatives:
# 1. We can simply forward fill the last valid value (from the first day of the month) for the whole month. This solution would introduce a huge step for every new month, which is not nice and could lead in further analysis to misinterpretations.
# 2. We can interpolate linearly between two values. This solution does not lead to a huge step and is very smooth. It should not harm further analysis. However, with this solution we introduce the assumption into the data, that there have not been any extreme events within the month. For example a strong dip with a V-shaped recovery.
# 3. Additionally, it would be possible to overlay the linear interpolation with random values, based on a distribution, which has been calculated out of the existing daily values. This is not very easy, since it must start at a certain point and also end at a certain point (the next datapoint), thus a simple random walk is not possible. Furthermore, we must ensure, that we do not artificially introduce extreme events, which are not reflected by the existing daily data.
# 
# For the sake of simplicity, we will just use the solution number 2. The yields for treasury bonds are not falling out of heaven, thus the assumption, that there are no extreme events between two data points is not completely wrong. Furthermore, we will later use real daily data, so any error, introduced by our interpolation, is just existing in the early years, where the volatility at the market was not as high as today.

# In[5]:


bg_yield_curve = reindex_and_interpolate(bg_yield_curve, min(bg_yield_curve.index), max(bg_yield_curve.index), 'D')
bg_yield_curve.head()


# The data from FRED is already daily, however it contains for every day, since on some days the market was closed or data is sometimes just missing. In our further analysis, we don't want to take care about days, where the market was closed. Thus, we also reindex those data to keep valid values for every day in the year. However, since the gaps are quite small, we don't need to use linear interpolation for that. We can just forward fill missing data-points, which introduced the (correct) assumption, that on those days, the change in value was just 0%.
# 
# On the days, where the values are missing, even through the market should have been open, there is just a dot `.` inside the dataframe. We must substitute this dot by a `NAN` value, before we fill up the gaps.

# In[6]:


def read_and_clean_fred_data(file_path, column_name, fred_name = None):
    if fred_name is None:
        fred_name = column_name
        
    gs_a = read_csv(file_path, column_name=column_name)
    gs_a = reindex_and_fill(gs_a, min(gs_a.index), max(gs_a.index), freq="D")
    
    gs_b = download_from_fred(fred_name)
    gs_b = reindex_and_fill(gs_b, min(gs_b.index), max(gs_b.index), freq="D")
        
    return merge_series(gs_a, gs_b)


# In[7]:


gs1 = read_and_clean_fred_data(gs1_path, "DGS1")
gs1


# We can now do this for all FRED data.

# In[8]:


gs3 = read_and_clean_fred_data(gs3_path, 'DGS3')
gs3


# In[9]:


gs5 = read_and_clean_fred_data(gs5_path, 'DGS5')
gs5


# In[10]:


gs7 = read_and_clean_fred_data(gs7_path, 'DGS7')
gs7


# In[11]:


gs10 = read_and_clean_fred_data(gs10_path, 'DGS10')
gs10


# In[12]:


gs20 = read_and_clean_fred_data(gs20_path, 'DGS20')
gs20


# In[13]:


gs30 = read_and_clean_fred_data(gs30_path, 'DGS30')
gs30


# Now we have all data as daily data available without any gaps. Thus, we can check if the data aligns within the overlapping regions.

# In[14]:


b = calc_growth(bg_yield_curve['1y']/36500)
f = normalize(calc_growth(gs1/36500), b)
draw_growth_chart(
    {
        "bogleheads 1y": b,
        "FRED 1y": f,
    },
    "1 year to maturity growth comparison",
    overlapping_only = True,
)


# In[15]:


b = calc_growth(bg_yield_curve['3y']/36500)
f = normalize(calc_growth(gs3/36500), b)
draw_growth_chart(
    {
        "bogleheads 3y": b,
        "FRED 3y": f,
    },
    "3 years to maturity growth comparison",
    overlapping_only = True,
)


# In[16]:


b = calc_growth(bg_yield_curve['5y']/36500)
f = normalize(calc_growth(gs5/36500), b)
draw_growth_chart(
    {
        "bogleheads 5y": b,
        "FRED 5y": f,
    },
    "5 years to maturity growth comparison",
    overlapping_only = True,
)


# In[17]:


b = calc_growth(bg_yield_curve['7y']/36500)
f = normalize(calc_growth(gs7/36500), b)
draw_growth_chart(
    {
        "bogleheads 7y": b,
        "FRED 7y": f,
    },
    "7 years to maturity growth comparison",
    overlapping_only = True,
)


# In[18]:


b = calc_growth(bg_yield_curve['10y']/36500)
f = normalize(calc_growth(gs10/36500), b)
draw_growth_chart(
    {
        "bogleheads 10y": b,
        "FRED 10y": f,
    },
    "10 years to maturity growth comparison",
    overlapping_only = True,
)


# In[19]:


b = calc_growth(bg_yield_curve['20y']/36500)
f = normalize(calc_growth(gs20/36500), b)
draw_growth_chart(
    {
        "bogleheads 20y": b,
        "FRED 20y": f,
    },
    "20 years to maturity growth comparison",
    overlapping_only = True,
)


# In[20]:


b = calc_growth(bg_yield_curve['Long']/36500)
f = normalize(calc_growth(gs30/36500), b)
draw_growth_chart(
    {
        "bogleheads 30y": b,
        "FRED 30y": f,
    },
    "30 years to maturity growth comparison",
    overlapping_only = True,
)


# We can clearly see, that both time-series are mostly aligned, when we accumulate the value growth over all years. Thus, our assumption from the beginning, that the yield values can safely interpolate between the monthly data points seems to hold. The next step is now to merge both time-series for every yield category. Even though, the overlapping between both data-sources is very high, we will do a smooth fading from one data-source to the other in the first 2 month.

# In[21]:


def calc_data1_weight(date, first_common_date, last_common_date):
    if date < first_common_date:
        return 1.0

    elif date > last_common_date:
        return 0.0

    else:
        delta = relativedelta(first_common_date, last_common_date)
        total = delta.years + delta.months/12 + delta.days/365.25
        delta = relativedelta(first_common_date, date)
        current = delta.years + delta.months/12 + delta.days/365.25
        return 1 - current/total


def merge_data(data1, data2):
    assert min(data1.index) < min(data2.index), "Data 1 must be the data with the earlier start date!"
    assert max(data1.index) < max(data2.index), "Data 2 must be the data with the later end date!"

    first_common_date = max(min(data1.index), min(data2.index))
    last_merge_date = first_common_date + pd_offsets.MonthEnd(2)
    print(f"First overlapping date: {first_common_date}")
    print(f"Last merge date: {last_merge_date}")

    combined = pd.Series(
        index=pd.date_range(min(data1.index), max(data2.index), freq="D"),
        dtype=np.float64
    )
    for i in combined.index:
        data1_weight = calc_data1_weight(i, first_common_date, last_merge_date)

        if data1_weight >= 0.999:
            combined.loc[i] = data1.loc[i]

        elif data1_weight <= 0.001:
            combined.loc[i] = data2.loc[i]

        else:
            combined.loc[i] = data1_weight * data1.loc[i] + (1 - data1_weight) * data2.loc[i]

    return combined


# In[22]:


yield_curve = pd.DataFrame()
yield_curve['1y'] = merge_data(bg_yield_curve['1y'], gs1)
yield_curve['3y'] = merge_data(bg_yield_curve['3y'], gs3)
yield_curve['5y'] = merge_data(bg_yield_curve['5y'], gs5)
yield_curve['7y'] = merge_data(bg_yield_curve['7y'], gs7)
yield_curve['10y'] = merge_data(bg_yield_curve['10y'], gs10)
yield_curve['20y'] = merge_data(bg_yield_curve['20y'], gs20)
yield_curve['30y'] = merge_data(bg_yield_curve['Long'], gs30)
yield_curve


# In[23]:


assert not yield_curve.isna().any().any()


# Finally, we check if our combined curve is aligned with both input curves.

# In[24]:


c = calc_growth(yield_curve['1y']/36500)
b = normalize(calc_growth(bg_yield_curve['1y']/36500), c)
f = normalize(calc_growth(gs1/36500), c)
draw_growth_chart(
    {
        "combined 1y": c,
        "boglehead 1y": b,
    },
    "1 year to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 1y": c,
        "FRED 1y": f,
    },
    "1 year to maturity growth comparison",
    overlapping_only = True,
)


# In[39]:


c = calc_growth(yield_curve['3y']/36500)
b = normalize(calc_growth(bg_yield_curve['3y']/36500), c)
f = normalize(calc_growth(gs3/36500), c)
draw_growth_chart(
    {
        "combined 3y": c,
        "boglehead 3y": b,
    },
    "3 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 3y": c,
        "FRED 3y": f,
    },
    "3 years to maturity growth comparison",
    overlapping_only = True,
)


# In[40]:


c = calc_growth(yield_curve['5y']/36500)
b = normalize(calc_growth(bg_yield_curve['5y']/36500), c)
f = normalize(calc_growth(gs5/36500), c)
draw_growth_chart(
    {
        "combined 5y": c,
        "boglehead 5y": b,
    },
    "5 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 5y": c,
        "FRED 5y": f,
    },
    "5 years to maturity growth comparison",
    overlapping_only = True,
)


# In[41]:


c = calc_growth(yield_curve['7y']/36500)
b = normalize(calc_growth(bg_yield_curve['7y']/36500), c)
f = normalize(calc_growth(gs7/36500), c)
draw_growth_chart(
    {
        "combined 7y": c,
        "boglehead 7y": b,
    },
    "7 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 7y": c,
        "FRED 7y": f,
    },
    "7 years to maturity growth comparison",
    overlapping_only = True,
)


# In[42]:


c = calc_growth(yield_curve['10y']/36500)
b = normalize(calc_growth(bg_yield_curve['10y']/36500), c)
f = normalize(calc_growth(gs10/36500), c)
draw_growth_chart(
    {
        "combined 10y": c,
        "boglehead 10y": b,
    },
    "10 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 10y": c,
        "FRED 10y": f,
    },
    "10 years to maturity growth comparison",
    overlapping_only = True,
)


# In[43]:


c = calc_growth(yield_curve['20y']/36500)
b = normalize(calc_growth(bg_yield_curve['20y']/36500), c)
f = normalize(calc_growth(gs20/36500), c)
draw_growth_chart(
    {
        "combined 20y": c,
        "boglehead 20y": b,
    },
    "20 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 20y": c,
        "FRED 20y": f,
    },
    "20 years to maturity growth comparison",
    overlapping_only = True,
)


# In[44]:


c = calc_growth(yield_curve['30y']/36500)
b = normalize(calc_growth(bg_yield_curve['Long']/36500), c)
f = normalize(calc_growth(gs30/36500), c)
draw_growth_chart(
    {
        "combined 30y": c,
        "boglehead 30y": b,
    },
    "30 years to maturity growth comparison",
    overlapping_only = True,
)
draw_growth_chart(
    {
        "combined 30y": c,
        "FRED 30y": f,
    },
    "30 years to maturity growth comparison",
    overlapping_only = True,
)


# As we can see, all time-series are very well aligned. We now have daily U.S. treasury yields for 1, 3, 5, 7, 10, 20 and 30 years. Especially in the early years, the values are not always 100% correct (just interpolated), but they are at least reasonable. For our goal of backtesting treasury bond fund returns over a long periode of time, this should be good enough. Thus we can store the data as cleaned.

# In[25]:


draw_growth_chart(
    {
        "combined 1y": yield_curve['1y'],
        "combined 3y": yield_curve['3y'],
        "combined 5y": yield_curve['5y'],
        "combined 7y": yield_curve['7y'],
        "combined 10y": yield_curve['10y'],
        "combined 20y": yield_curve['20y'],
        "combined 30y": yield_curve['30y'],
    },
    "Yields over Time",
    y_log = False,
    y_title = "yields in %",
)


# In[45]:


output_file_path = clean_data_path / "yield_curve.xlsx"
yield_curve.to_excel(output_file_path)

