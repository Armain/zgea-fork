import pandas as pd
from typeguard import typechecked

from utils.math import calc_growth
from utils.plots import draw_growth_chart


@typechecked
def draw_applied_simulations(simulations: pd.DataFrame, start_value: float = 10000):
    p = {}
    for i, c in enumerate(simulations.columns):
        p[str(i)] = simulations[c]
    draw_growth_chart(p)


@typechecked
def draw_simulations(simulations: pd.DataFrame, start_value: float = 10000):
    p = {}
    for i, c in enumerate(simulations.columns):
        p[str(i)] = calc_growth(simulations[c], start_value=10000)
    draw_growth_chart(p)
