import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from typeguard import typechecked
from utils.math import normalize, calc_returns

@typechecked
def calc_monte_carlo_simulations(portfolio: pd.DataFrame, number_of_sims: int, time_interval: relativedelta):
    returns = calc_returns(portfolio['sum'], "D")
    end_date = max(returns.index) - time_interval
    possible_start_dates = [d for d in returns.index if d < end_date]
    chosen_start_dates = np.random.choice(possible_start_dates, number_of_sims)

    simulations = pd.DataFrame()
    for start_date in chosen_start_dates:
        end_date = start_date + time_interval
        simulation = returns.loc[start_date:end_date].copy()
        days = len(simulation.index)
        simulation = simulation.set_axis(range(0, days))
        simulations.loc[:, str(start_date)] = simulation

    return simulations.dropna()
