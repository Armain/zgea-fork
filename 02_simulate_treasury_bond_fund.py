#!/usr/bin/env python
# coding: utf-8

# # Simulate Treasury Bond Funds
# 
# The HFEA strategy is based on treasury bond funds as hedge for the growth part of the portfolio. Thus, it is important to have the value of all interesting treasury bond funds available for many years. Ideally even before 1970, where the oil crises started. However, all treasury bond funds, just exist since some years. So the oldest fund was available around 2010. Therefore, we have to simulate such a fond to do a long term backtest with this kind of hedge.
# 
# In the bogleheads thread https://www.bogleheads.org/forum/viewtopic.php?t=179425 the user `longinvest` explains how a treasury bond fund could be simulated. In this notebook we try out different approaches, compare them with each other and calculate the simulated treasury bond fund values on daily base beginning of 1943.

# In[1]:


from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import numpy_financial as npf
import pandas.tseries.offsets as pd_offsets
from dateutil.relativedelta import relativedelta
from typing import List, Optional, Dict


# In[2]:


from utils.plots import draw_growth_chart, draw_telltale_chart
from utils.data import cached, read_csv
from utils.math import normalize, reindex_and_fill


# In order to check our simulated values, we have to compare those values, with the simulated values from the backtest (https://www.bogleheads.org/forum/viewtopic.php?p=5815123#p5815123), available at bogleheads. I combined the interesting long term treasury (ltt), intermediate term treasury (itt) and short term treasury (stt) in a single excel file. The first step is to load this file and to restrict the values to the time period, which fits to our treasury yield curves.

# In[3]:


raw_data_path = Path("raw_data")
clean_data_path = Path("clean_data")
cached_data_path = Path("cached_clean_data")

simba_path = raw_data_path  / "simba_data.xlsx"
simba = pd.read_excel(simba_path, skiprows=1, index_col=0)
simba.index = pd.to_datetime(simba.index, format="%Y")
simba = simba.loc['1943':,:]
simba.head()


# This data is just yearly available, but we can use it to compare our calculated daily values with the yearly values from Simba. So the next step is to calculate the portfolio growth we would have by investing on the first day on those funds.

# In[4]:


def calc_growth(gain_series, start_value=100, ticks_per_year=1):
    growth = pd.Series(index = gain_series.index, dtype=np.float64)
    capital = start_value
    for i in gain_series.index:
        growth.loc[i] = capital
        capital = capital * (1 + (gain_series.loc[i]/ticks_per_year)/100)
    return growth

simba['stt_g'] = calc_growth(simba['stt'])
simba['itt_g'] = calc_growth(simba['itt'])
simba['ltt_g'] = calc_growth(simba['ltt'])
simba.head()


# In[5]:


draw_growth_chart(
    {
        'ltt (30-10y)': simba['ltt_g'],
        'itt (10-5y)': simba['itt_g'],
        'stt (3-1y)': simba['stt_g'],
    },
    "Growth of different U.S. treasury bonds (Simba's Data)"
)


# Now, we can load our precalculated treasury yields and start with the simulation of a treasury bond fund. 

# In[6]:


yield_curves_path = clean_data_path / "yield_curve.xlsx"
yields = pd.read_excel(yield_curves_path, index_col=0)
yields.head()


# Our first try is to simulate the yearly values of the treasury bond. This can better be comapared witht he yearly values from Simbas backtest sheet. Therefore, we just take the value from the first day of the first month.

# In[7]:


yearly_yields = yields[(yields.index.month == 1) & (yields.index.day == 1)]
yearly_yields.head()


# ## Simulate 10-5 Years Bond Fund
# 
# We first focus an simulating the 10-5 years bond fund and compare it to the ITT growth of Simbas Spreadsheet.
# 

# ### Accumulating Approach
# 
# The first approach is to accumulate the yields as they would be gains. This is the most simply approach but it ignores completly the math and theory behind a treasury bond. We chose the 10 years yields for the aggregation.
# 

# In[8]:


itt_sim = pd.DataFrame(index=yearly_yields.index)
itt_sim['agg'] = calc_growth(yearly_yields['10y'])
itt_sim['agg'].head()


# In[9]:


draw_growth_chart(
    {
        'itt (simba)': simba['itt_g'],
        'aggregated yields 10y': itt_sim['agg']
    },
    "Compare ITT (10-5 years) bond growth",
)


# As we can see, our simulated bond fund follows the comparison line, but it is in general too smooth and has for many years a high positive offset and later a negative offset.

# In the thread "Historical Bond Returns - From Rates to Returns [Bond Fund Simulator]" from user `longinvest` of the bogleheads forum (https://www.bogleheads.org/forum/viewtopic.php?t=179425), the user describes three different approaches how to simulate a bond fund.
# 
# The first approach is based on the idea, that the bond fund buys every year a single 10 years bond. On the next year the fund collects the coupon (yield) and sells the bond. For calculating the remaining price of the bond, the function "present value" (PV in excel) is used. This calculation introduced two errors: First of all, for calculating the present value of the bond, we would need the 9 years bond yield, which is not available for us. Thus we have to use the 10 years bond yield, which tends to lead to lower values. The second issue is, that this is not the way a real bond fund works. Thus the characteristics of the simulates bond fund is different to the reality. But it is still a nice starting point.
# 
# To implement this, we create a class, which models a single bond. It has a method to calculate the current value of the bond, based on the currend date (remaining time to maturity) and the current bond interest rate for such type of bond. It also has a method to collect the gains of this bond, since the last call. Thus we can also collect partly coupons (within a year).
# 
# It also provides two convenience methods, for calculating the ramining years until the bond matures and to interpolate between two bond interest rates. Those methods are needed later for the more complex approaches. 

# In[10]:


class Bond():
    def __init__(self, buy_date: pd.Timestamp, buy_value: float, current_yield: float, years: int):
        self._buy_date = buy_date
        self._buy_value = buy_value
        self._yield = current_yield
        self._last_gain_collect = buy_date
        self._last_date = buy_date + relativedelta(years=years)
        
        
    def _get_fractional_years(self, start: pd.Timestamp, end: pd.Timestamp) -> float:
        delta = relativedelta(end, start)
        return delta.years + delta.months/12 + delta.days/365.25
        
               
    def current_value(self, current_date: pd.Timestamp, current_interest: float) -> float:
        diff_years = int(self.remaining_years(current_date))
        interest_bought = self._yield / 100
        interest_sold = current_interest / 100
        return -npf.pv(interest_sold, diff_years, self._buy_value * interest_bought, self._buy_value)
        
        
    def collect_gain(self, current_date: pd.Timestamp) -> float:
        if (current_date > self._last_date) or (current_date < self._last_gain_collect):
            return 0.0
        diff_years = self._get_fractional_years(self._last_gain_collect, current_date)
        self._last_gain_collect = current_date
        return diff_years * (self._yield * self._buy_value) / 100
    
    
    def remaining_years(self, current_date: pd.Timestamp) -> float:
        diff_years = self._get_fractional_years(current_date, self._last_date)
        return diff_years
    
    
    @staticmethod
    def calc_interest(rate1: float, years1: int, rate2: float, years2: int, current_years: float) -> float:
        return rate2 + (rate1 - rate2) * (current_years - years2) / (years1 - years2)


# We test the bond with the example, provided by user `longinvest`: In 1960, we buy a 10-year-bond with a bond rate of 4.72%. Then we collect until 1969 the coupon and sell it in 1969 for the remining price, which can be calculated by the 1-year-bond rate, which was 8.05%.

# In[11]:


buy_date = pd.Timestamp(year=1960, month=1, day=1)

bond = Bond(
    buy_date = buy_date,
    buy_value = 100,
    current_yield = 4.72,
    years = 10,
)

for y in range(10):
    current_date = buy_date + pd_offsets.YearBegin(y)
    coupon = bond.collect_gain(current_date)
    remaining_years = bond.remaining_years(current_date)
    remaining_value = bond.current_value(
        current_date, 
        bond.calc_interest(
            4.72, 
            10, 
            8.05, 
            1, 
            remaining_years,
        ))
    print(f"Year: {current_date}, Coupon: ${coupon:.2f}, Years to mature: {remaining_years}, Value: ${remaining_value:.2f}")


# With our bond-class we can calculate exactly the same values, as `longinvest` presented in the first post of the thread. Now we implement a naiive bond simulator, which always holds a single bond.
# 
# In the beginning of the a calculation-tick (once a year for example), it collects the coupon from the bond as sells it for the price, which is calculated out of the current 10-years-bond yield. Then it is reinvesting the collected money in a new 10-years-bond.

# In[12]:


class NaiveBondSimulator():
    def __init__(self, start_value: float, years: int):
        self._start_value = start_value
        self._bond = None
        self._years = years
        
        
    def calculate_tick(self, date: pd.Timestamp, current_yield: float):
        self._last_yield = current_yield
        self._last_tick_date = date
        
        income = self._start_value
        self._start_value = 0
        
        if self._bond is not None:
            income += self._bond.collect_gain(date)
            income += self._bond.current_value(date, current_yield)
            self._bond = None
            
        self._bond = Bond(
            buy_date = date,
            buy_value = income,
            current_yield = current_yield,
            years = self._years,
        )
        
        return income
        
        
    @property
    def current_value(self) -> float:
        if self._last_tick_date is None:
            return 0
        
        return self._bond.current_value(
            self._last_tick_date, 
            self._last_yield,
        )


# In[13]:


itt_sim['naive'] = None
bond_fund = NaiveBondSimulator(100, 10)

for i, row in yearly_yields.iterrows():
    income = bond_fund.calculate_tick(row.name, row['10y'])
    itt_sim.loc[i, 'naive'] = bond_fund.current_value
    print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
    
itt_sim['naive'].head()


# In[14]:


draw_growth_chart(
    {
        'itt (simba)': simba['itt_g'],
        'aggregated yields 10y': itt_sim['agg'],
        'naiive simulation 10y': itt_sim['naive'],
    },
    "Compare ITT (10-5 years) bond growth",
)


# As we can see the naiive approach is following the blue reference line very well, but it has mostly a negative offset to this line. This offset is espeacially getting worse in the last years. 

# The next approach user `longinvest` describes introduces a simple improvement compared to the first apporach. We will call it now "simple approach". Here we simulate a bond fund, which buys every year two bonds: A 10-years bond and a 1-years bond. Next year it collects the coupon from both bonds and the remaining value of both and invest it again into two bonds. The ramaining value of the 9-years bond is interpolated from the 10-years yield. But the remaining value of the former 1-years bond can be directly taken be calculated. 
# 
# The advantage of this approach is, that characteristics of this bond follow stronger a real bond fund, but it still accumulates an error due to the 9-years yield approximation and it still works different to a real bond fund.

# In[15]:


class SimpleBondSimulator():
    def __init__(self, start_value: float, years1: int, years2: int):
        self._start_value = start_value
        self._bonds = []
        self._years1 = years1
        self._years2 = years2
        
        
    def calculate_tick(self, date: pd.Timestamp, current_yield1: float, current_yield2: float):
        self._last_yield1 = current_yield1
        self._last_yield2 = current_yield2
        self._last_tick_date = date
        
        income = self._start_value
        self._start_value = 0
        
        assert len(self._bonds) == 2 or len(self._bonds) == 0

        if len(self._bonds) == 2:
            bond_coupon1 = self._bonds[0].collect_gain(date)
            bond_value1 = self._bonds[0].current_value(date, self._bonds[0].calc_interest(
                self._last_yield1, 
                self._years1, 
                self._last_yield2, 
                self._years2, 
                self._bonds[0].remaining_years(date),
            ))
            #print(f"Value of bond 1: ${bond_value1:.2f} + ${bond_coupon1:.2f}(years: {self._bonds[0].remaining_years(date)})")
            income += (bond_value1 + bond_coupon1)
            
            bond_coupon2 = self._bonds[1].collect_gain(date)
            bond_value2 = self._bonds[1].current_value(date, current_yield2)
            #print(f"Value of bond 2: ${bond_value2:.2f} + ${bond_coupon2:.2f} (years: {self._bonds[1].remaining_years(date)})")
            income += (bond_value2 + bond_coupon2)
            
        self._bonds = []        
        self._bonds.append(Bond(
            buy_date = date,
            buy_value = income/2,
            current_yield = current_yield1,
            years = self._years1,
        ))
        self._bonds.append(Bond(
            buy_date = date,
            buy_value = income/2,
            current_yield = current_yield2,
            years = self._years2,
        ))
        
        return income
        
        
    @property
    def current_value(self) -> float:
        if self._last_tick_date is None:
            return 0
        
        value = 0
        value += self._bonds[0].current_value(
            self._last_tick_date, 
            self._last_yield1,
        )
        value += self._bonds[1].current_value(
            self._last_tick_date, 
            self._last_yield2,
        )
        return value


# In[16]:


itt_sim['simple'] = None
bond_fund = SimpleBondSimulator(100, 10, 1)

for i, row in yearly_yields.iterrows():
    income = bond_fund.calculate_tick(row.name, row['10y'], row['1y'])
    itt_sim.loc[i, 'simple'] = bond_fund.current_value
    print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
    
itt_sim['simple'].head()


# In[17]:


draw_growth_chart(
    {
        'itt (simba)': simba['itt_g'],
        'aggregated yields 10y': itt_sim['agg'],
        'naiive simulation 10y': itt_sim['naive'],
        'simple simulation 10-1y': itt_sim['simple'],
    },
    "Compare ITT (10-5 years) bond growth",
)


# In the first half of the chart, until 1985 the simple approach is very well following the blue reverence line, but then it diverges away from it and it ends up with a small negative offset. The reason for this, could be that the difference bettween 1-year and 10-year yields gets higher after 1985, which leads to a more step yield curve and thus to a higher approximation error.
# 
# In order to check this, we can simply plot the difference between both values in a diagram. In the following diagram the difference is smoothed by using a moving average of 10 years.

# In[18]:


draw_growth_chart(
    {
        "difference (10y - 1y)": (yearly_yields['10y'] - yearly_yields['1y']).rolling(window=10).mean()
    },
    "Difference between 10 and 1 year yields over time.",
    y_title = "difference in %",
    y_log = False,
)


# We can clearly see how the moving average of the difference started to increase strongly after 1985, which explains why the simple and naive approach faded away in those years. 

# To workaround those approximiation errors, the user `longinvest` came up with a new idea: Why not simulating bond funds as they are actually work?
# 
# Let's say we want to simulate a bond fund, which holds bonds with 5-10 years maturity. The bond fund would collect all the coupons from all bonds, it holds and invest it into a new bond with 10 years matrurity. If any of the hold bonds falls to 5 year maturity, it sells this bond for the actual value of this bond. In short a bond fund is working like a bond ladder: It holds for every year a bond with decreasing maturity from 10 to 6. 
# 
# We can exactly calculate the buy value of a 10 years bond and we can also exactly calculate the sell value of a 5 year bond. Only the current value of the whole fund, which contains also 9, 8, 7, and 6 years bonds needs an approximation, but this approximation does not accumulate over time: the current value of the bond fund is not used for reinvestment, only the coupons and sell-values of the bonds are used and those can be calculates exactly. 

# In[19]:


class BondFundSimulator():
    def __init__(self, start_value: float, start_year: int, end_year: int):
        self._start_value = start_value
        self._bonds = []
        self._year1 = start_year
        self._year2 = end_year
        self._interest1 = 0
        self._interest2 = 0
        self._last_tick_date = None
        
        
        
    def calculate_tick(self, current_date: pd.Timestamp, interest1: float, interest2: float):
        if self._last_tick_date == current_date:
            return
        
        self._interest1 = interest1
        self._interest2 = interest2
        self._last_tick_date = current_date
        
        new_bonds = []
        income = self._start_value
        self._start_value = 0
        
        for b in self._bonds:
            income += b.collect_gain(current_date)
            if b.remaining_years(current_date) <= self._year2:
                income +=b.current_value(current_date, self._interest2)
            else:
                new_bonds.append(b)
            
        new_bonds.append(Bond(
            buy_date=current_date, 
            buy_value=income, 
            current_yield=self._interest1, 
            years=self._year1
        ))
                
        self._bonds = new_bonds
        
        #for b in self._bonds:
        #    print(b.remaining_years(current_date))
        
        return income
        
        
        
    @property
    def current_value(self) -> float:
        if self._last_tick_date is None:
            return 0
        
        value = self._start_value
        for b in self._bonds:
            value += b.current_value(
                self._last_tick_date, 
                b.calc_interest(
                    self._interest1, 
                    self._year1, 
                    self._interest2, 
                    self._year2, 
                    b.remaining_years(self._last_tick_date)
                )
            )
        return value


# In[20]:


itt_sim['fund'] = None
bond_fund = BondFundSimulator(100, 10, 5)

for i, row in yearly_yields.iterrows():
    income = bond_fund.calculate_tick(row.name, row['10y'], row['5y'])
    itt_sim.loc[i, 'fund'] = bond_fund.current_value
    print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
    
itt_sim['fund'].head()


# In[21]:


draw_growth_chart(
    {
        'itt (simba)': simba['itt_g'],
        'aggregated yields 10y': itt_sim['agg'],
        'naiive simulation 10y': itt_sim['naive'],
        'simple simulation 10-1y': itt_sim['simple'],
        'fund simulation 10-5y': itt_sim['fund'],
    },
    "Compare ITT (10-5 years) bond growth",
)


# It is obvoise that the simulated bond-fund almost exactly follows the blue line. It is clearly the most exact model.

# Just for completness we now draw also a telltale diagram. A telltale diagram has been used my Mr. Bogle to better highlight phases of strong and weak performance of investments compared a reference investment. In our case we chose the ITT values from the Simba Backtest Sheet as reference, thus we can clearly see how well our simulated bond values follow this reference.

# In[22]:


draw_telltale_chart(
    simba['itt_g'],
    {
        'aggregated yields 10y': itt_sim['agg'],
        'naiive simulation 10y': itt_sim['naive'],
        'simple simulation 10-1y': itt_sim['simple'],
        'fund simulation 10-5y': itt_sim['fund'],
    },
    "Compare ITT (10-5 years) bond simulations (reference: ITT from Simba Backtest Sheet)",
)


# Also from this image, it is obvoise, that the simulated bond fund is following the values from Simbas Backtest Sheet the best. Thus for all further calculations, we will chose this model.
# 

# ## Simulate 3-1 Years Bond Fund
# 
# In the next step, we simulate a short term treasury bond, which holds bonds from 3 to 1 years. In the simba dataset it is called stt. We directly simulate it with the bond fund simulator and compare the result with a growth chart and a telltale shart.

# In[23]:


stt_sim = pd.DataFrame(index=yearly_yields.index)
stt_sim['fund'] = None
bond_fund = BondFundSimulator(100, 3, 1)

for i, row in yearly_yields.iterrows():
    income = bond_fund.calculate_tick(row.name, row['3y'], row['1y'])
    stt_sim.loc[i, 'fund'] = bond_fund.current_value
    print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
    
stt_sim['fund'].head()


# In[24]:


draw_growth_chart(
    {
        'stt (simba)': simba['stt_g'],
        'fund simulation 3-1y': stt_sim['fund'],
    },
    "Compare STT (3-1 years) bond growth",
)
draw_telltale_chart(
    simba['stt_g'],
    {
        'fund simulation 3-1y': stt_sim['fund'],
    },
    "Compare STT (3-1 years) bond simulations (reference: STT from Simba Backtest Sheet)",
)


# Also here we archive similar performance than with 10-5 years bonds (note the different scaling of the y-axis in the telltale chart).
# 

# ## Simulate 30-10 Years Bond Fund
# 
# In the next step, we simulate a long term treasury bond, which holds bonds from 30 to 10 years. In the simba dataset it is called ltt. We directly simulate it with the bond fund simulator and compare the result with a growth chart and a telltale shart.

# In[25]:


ltt_sim = pd.DataFrame(index=yearly_yields.index)
ltt_sim['fund'] = None
bond_fund = BondFundSimulator(100, 30, 10)

for i, row in yearly_yields.iterrows():
    income = bond_fund.calculate_tick(row.name, row['30y'], row['10y'])
    ltt_sim.loc[i, 'fund'] = bond_fund.current_value
    print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
    
ltt_sim['fund'].head()


# In[26]:


draw_growth_chart(
    {
        'ltt (simba)': simba['ltt_g'],
        'fund simulation 30-10y': ltt_sim['fund'],
    },
    "Compare LTT (30-10 years) bond growth",
)
draw_telltale_chart(
    simba['ltt_g'],
    {
        'fund simulation 30-10y': ltt_sim['fund'],
    },
    "Compare LTT (30-10 years) bond simulations (reference: LTT from Simba Backtest Sheet)",
)


# The 30-10 years simulation is not as good as the other bond simulations. The error remains small until beginning of the 1970s and is then increasing to up to -20%. When looking at the data-sheet of simba we can see, that the time-series for LTT is switching from longinvest's simulation to real fund values in 1972, which fits perfect to the year, where the error get so strong. The fund data, which is used by Simbas Sheet is later the VUSUX fund from Vanguard. In the portfomio page of the homepage, we can see, that half of the bonds in the fund have 25 years maturity and almost the whole other half has more then 15 years maturity. Thus our fund model does not fit exactly to this fund.

# ## Calculate Daily Values
# 
# Our goal was not to calculate yearly values but to calculate daily values for a more detailed analysis and backtest then Simbas Backtest Worksheet would allow. Now we have a proper model for yearly values and we can adapt it to also generate monthly values.
# 
# Our bond fund simulator needs to collect only 1/365 of the coupon each tick (day) and it must buy a new bond every new day and sell bonds, which are out of the bond maturity range. The current class, should already provide all those changes, we simply need to test it against the current data.
# 
# Let's start with the 3-1 year bond fund simulation.

# In[27]:


bond_fund_sim = pd.DataFrame(index=yields.index)


# In[28]:


def simulate_bond_fund(start_years, end_years):
    bond_fund_series = pd.Series(index=yields.index, dtype=np.float64)
    bond_fund = BondFundSimulator(100, start_years, end_years)

    last_print = None
    for i, row in yields.iterrows():
        income = bond_fund.calculate_tick(row.name, row[f'{start_years}y'], row[f'{end_years}y'])
        bond_fund_series.loc[i] = bond_fund.current_value
        if (last_print is None) or (relativedelta(row.name, last_print).months > 0):
            last_print = row.name
            print(f"{row.name}: income: ${income:.2f}, value: ${bond_fund.current_value:.2f}")
            
    return bond_fund_series


# In[29]:


bond_fund_sim['stt_us'] = cached(cached_data_path / "02_stt_us_bond.pkl")(simulate_bond_fund)(3, 1)    
bond_fund_sim['stt_us']


# In[30]:


draw_growth_chart(
    {
        'stt (simba)': simba['stt_g'],
        'fund simulation 3-1y': bond_fund_sim['stt_us'],
    },
    "Compare STT (3-1 years) bond growth",
)


# We can see, that the daily bond fund simulation is following mostly the same way as the yearly simulation. However mid of the 1980th the daily simulation starts to diverge from the yearly simulation. This was a time of high bond yields and thus the daily calculation could have an advantage over the yearly calculation, by reinvesting coupons already in the middle of the year in new high yield bonds. 

# In[31]:


bond_fund_sim['itt_us'] = cached(cached_data_path / "02_itt_us_bond.pkl")(simulate_bond_fund)(10, 5)    
bond_fund_sim['itt_us']


# In[32]:


draw_growth_chart(
    {
        'itt (simba)': simba['itt_g'],
        'fund simulation 10-5y': bond_fund_sim['itt_us'],
    },
    "Compare ITT (10-5 years) bond growth",
)


# The ITT bonds shows the same behavior. 

# In[33]:


bond_fund_sim['ltt_us'] = cached(cached_data_path / "02_ltt_us_bond.pkl")(simulate_bond_fund)(30, 10)    
bond_fund_sim['ltt_us']


# In[34]:


draw_growth_chart(
    {
        'ltt (simba)': simba['ltt_g'],
        'fund simulation 30-10y': bond_fund_sim['ltt_us'],
    },
    "Compare LTT (30-10 years) bond growth",
)


# This time, our simulation machtes the LTT values from Simba almost perfectly. 

# ## Simulate Europe Treasury Bond ETFs
# 
# In europe, we cannot buy the ETFs, used by bogleheads (stt, itt and ltt) but we can buy other ETFs. For my further analysis I decide to select the following ETFs:
# 
# * `iShares $ Treasury Bond 20+yr UCITS ETF` (DTLA) => LTT
# * `iShares $ Treasury Bond 7-10yr UCITS ETF` (SXRM) => ITT
# * `iShares $ Treasury Bond 1-3yr UCITS ETF` (IBTA) => STT
# 
# In this section, we simulate the bond funds for those ETFs and compare it with the real values.

# First we try to simulate the IBTA ETF, which contains bonds with maturity duration of 1-3 years. We simulate it with a bond fund, which contains bonds from 3 to 1 years. So the first step is to load the data for IBTA, which is also given as daily data. Afterwards we fill some gaps in it.

# In[35]:


ibta = read_csv(raw_data_path / "IBTA.csv", column_name="Adj Close")
ibta = reindex_and_fill(ibta, min(ibta.index), max(ibta.index), freq="D")
ibta


# In[36]:


bond_fund_sim['stt_eu'] = cached(cached_data_path / "02_stt_eu_bond.pkl")(simulate_bond_fund)(3, 1)    
bond_fund_sim['stt_eu']


# In[37]:


reference = normalize(ibta, bond_fund_sim['stt_eu'])
draw_growth_chart(
    {
        'IBTA ETF (3-1y)': reference,
        'fund simulation 3-1y': bond_fund_sim['stt_eu'],
    },
    "Compare STT (3-1 years) bond growth",
    overlapping_only = True,
)
draw_telltale_chart(
    reference,
    {
        'fund simulation 3-1y': bond_fund_sim['stt_eu'],
    },
    "Compare STT (3-1 years) bond growth (Reference: IBTA ETF)",
    overlapping_only = True,
)


# Our bond fund simulation of the IBTA ETF, follows the ETF almost perfectly. The abslute maximum error is below 1%, which is extremly good.

# As the next step, we simulate an europeen ITT fund, for which SXRM seems to be the perfect coparison candidate. So, again, we load the SXRM data, fill the gaps, calculate our simulation and compare it in a growth and telltale chart.

# In[38]:


sxrm = read_csv(raw_data_path / "SXRM.csv", column_name="Adj Close")
sxrm = reindex_and_fill(sxrm, min(sxrm.index), max(sxrm.index), 'D')
sxrm


# In[39]:


bond_fund_sim['itt_eu'] = cached(cached_data_path / "02_itt_eu_bond.pkl")(simulate_bond_fund)(10, 7)    
bond_fund_sim['itt_eu']


# In[40]:


reference = normalize(sxrm, bond_fund_sim['itt_eu'])
draw_growth_chart(
    {
        'SXRM ETF (10-7y)': reference,
        'fund simulation 10-7y': bond_fund_sim['itt_eu'],        
    },
    "Compare ITT (10-7 years) bond growth",
    overlapping_only=True,
)
draw_telltale_chart(
    reference,
    {
        'fund simulation 10-7y': bond_fund_sim['itt_eu'],
    },
    "Compare ITT (10-7 years) bond growth (Reference: SXRM ETF)",
    overlapping_only=True,
)


# As we can see, our simulated 10-7 years bond fund is a good match for the SXRM ETF. It tracks very well the overall curve. In the beginning we have big errors, since we are missing some SXRM data points here. But aftewards the error is below 4%, which is a very good result. However, we also see a trend of our simulated bond fund, of growing a little bit too fast compared to the ETF. Maybe this is because of the TER. We will investigate in this later, when we model ETFs in more detail. 

# Now, we can simulate an europeen LTT fund, for which DTLA seems to be the the ETF equavalent. Also here, we load the DTLA data, fill the gaps, calculate our simulation and compare it in a growth and telltale chart.

# In[41]:


dtla = read_csv(raw_data_path / "DTLA.csv", column_name="Adj Close")
dtla = reindex_and_fill(dtla, min(dtla.index), max(dtla.index), 'D')
dtla


# In[42]:


bond_fund_sim['ltt_eu'] = cached(cached_data_path / "02_ltt_eu_bond.pkl")(simulate_bond_fund)(30, 20)    
bond_fund_sim['ltt_eu']


# In[43]:


reference = normalize(dtla, bond_fund_sim['ltt_eu'])
draw_growth_chart(
    {
        'DTLA ETF (30-20y)': reference,
        'fund simulation 30-20y': bond_fund_sim['ltt_eu'],
    },
    "Compare LTT (30-20 years) bond growth",
    overlapping_only=True,
)
draw_telltale_chart(
    reference,
    {
        'fund simulation 30-20y': bond_fund_sim['ltt_eu'],
    },
    "Compare LTT (30-20 years) bond growth (Reference: DTLA ETF)",
    overlapping_only=True,
)


# We have here almost a perfect fit. Only during the Corona crisis, the error jumps to around 6%, which is still very good.

# Now we can store our results and proceed with the analysis. 

# In[44]:


bond_fund_sim.head()


# In[45]:


output_path = clean_data_path / "bond_funds.xlsx"
bond_fund_sim.to_excel(output_path)

