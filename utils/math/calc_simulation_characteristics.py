import pandas as pd
from typeguard import typechecked


@typechecked
def calc_simulation_characteristics(simulations: pd.DataFrame):
    characteristics = pd.DataFrame()
    characteristics['mean'] = simulations.mean(axis=1)
    characteristics['min'] = simulations.min(axis=1)
    characteristics['max'] = simulations.max(axis=1)
    characteristics['stddev_up'] = simulations.mean(axis=1) + simulations.std(axis=1)
    characteristics['stddev_low'] = simulations.mean(axis=1) - simulations.std(axis=1)
    return characteristics
