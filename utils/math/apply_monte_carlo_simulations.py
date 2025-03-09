from typeguard import typechecked
import pandas as pd
from typing import Optional

from utils.math import calc_growth_with_periodic_rate


@typechecked
def apply_monte_carlo_sim(
        simulations: pd.DataFrame,
        start_value: float,
        periodic_rate: float = 0,
        rate_interval: Optional[int] = None
):
    applied_simulations = pd.DataFrame()
    for c in simulations.columns:
        applied_simulations[c] = calc_growth_with_periodic_rate(
            simulations[c],
            start_value = start_value,
            periodic_rate = periodic_rate,
            rate_interval = rate_interval,
        )

    return applied_simulations
