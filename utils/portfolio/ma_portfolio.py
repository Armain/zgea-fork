import pandas as pd
from typing import Dict, Optional, Union, Any, List
from typeguard import typechecked
from dateutil.relativedelta import relativedelta

from utils.math import normalize
from utils.portfolio.asset import Asset
from utils.portfolio.tax_model import TaxModel

from .null_tax_model import NullTaxModel


class MAPortfolio():
    @typechecked()
    def __init__(
            self,
            setup: Dict[str, Dict[str, Union[str, float]]],
            start_value: float = 10000,
            rebalancing: Optional[relativedelta] = None,
            rebalancing_offset: Optional[relativedelta] = None,
            detailed_output: bool = False,
            details_memory: Optional[Dict[str, Any]] = None,
            spread = 0,
            tax_model = NullTaxModel(),
    ):
        assert len(setup.keys()) >= 1, "You must specify at least one ETF."
        assert len(setup.keys()) == len(set(setup.keys())), "Every ETF must be unique in your portfilio."
        for name, v in setup.items():
            assert 'dist' in v, "Every asset needs a key 'dist'!"
            if 'ma' not in v or v['ma'] == 1:
                v['ma'] = 1
                v['ma_asset'] = name
            assert 'ma_asset' in v, "Every asset needs a key 'ma_asset'!"
        assert sum([v['dist'] for v in setup.values()]) <= 100, f"Your Portfolio has an allocation of {sum([d for d in distribution.values()])}%"

        self._setup = setup
        self._start_value = start_value
        self._detailed_output = detailed_output
        self._details_memory = details_memory if details_memory is not None else {}
        self._rebalancing = rebalancing
        self._rebalancing_offset = rebalancing_offset
        self._spread = spread / 2
        self._tax_model = tax_model


    def backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        asset_names = list(self._setup.keys())
        assets = {}
        print(f"Backtest of portfolio with assets: {[str(s['dist'])+'% '+str(n) for n, s in self._setup.items()]}")

        mas = pd.DataFrame(columns=asset_names)
        self._values = {}

        max_ma_length = max([v['ma'] for v in self._setup.values()])

        self._details_memory['asset'] = {}
        for name, setup in self._setup.items():
            assert name in data.columns, f"Asset with the name {name} does not exist in data ({data.columns})."
            self._details_memory['asset'][name] = dict(buys=[], sells=[])

            value_to_buy = (self._start_value * setup['dist'])/100
            self._values[name] = value_to_buy
            assets[name] = Asset(name, detailed_output = False)
            mas[name] = data[self._setup[name]['ma_asset']].rolling(window=setup['ma']).mean()

        portfolio_values = pd.DataFrame(columns=asset_names+['sum'], index=mas.index[max_ma_length:])

        if self._rebalancing is not None:
            next_rebalancing = min(portfolio_values.index) + self._rebalancing + self._rebalancing_offset

        for i in portfolio_values.index:
            if (self._rebalancing is not None) and (i > next_rebalancing):
                next_rebalancing = next_rebalancing + self._rebalancing
                self._do_rebalancing(assets, data.loc[i, :])

            for name in asset_names:
                asset_price = data.loc[i, name]
                compare_asset_price = data.loc[i, self._setup[name]['ma_asset']]
                if (compare_asset_price >= mas.loc[i, name]):
                    if self._values[name] is not None:
                        real_asset_price = asset_price * (1 + self._spread)
                        self._log(f"** {i}: [{self._setup[name]['ma_asset']}] Base-Value (${compare_asset_price:.2f}) >= MA (${mas.loc[i, name]:.2f})")

                        amount = self._values[name]/real_asset_price
                        self._log(f" => Buy {amount:.2f}x {name} for ${real_asset_price:.2f} each (total: ${self._values[name]:.2f})")

                        self._details_memory['asset'][name]['buys'].append(i)
                        assets[name].buy(amount, real_asset_price)
                        self._values[name] = None

                elif (compare_asset_price < mas.loc[i, name]):
                    if self._values[name] is None:
                        real_asset_price = asset_price * (1 - self._spread)
                        self._log(f"** {i}: [{self._setup[name]['ma_asset']}] Base-Value (${compare_asset_price:.2f}) < MA (${mas.loc[i, name]:.2f})")
                        self._log(f" => Sell {assets[name].amount:.2f}x {name} for ${real_asset_price:.2f} each (total: ${assets[name].amount * real_asset_price:.2f})")

                        self._values[name] = assets[name].amount * real_asset_price
                        _, gain = assets[name].sell(assets[name].amount, real_asset_price)
                        self._tax_model.add_gain(name, gain)
                        self._details_memory['asset'][name]['sells'].append(i)

                portfolio_values.loc[i, name] = assets[name].amount * asset_price + self._get_value(name)

            while self._tax_model.open_tax > 1.0:
                self._sell(assets, data.loc[i, :], self._tax_model.open_tax)

        portfolio_values['sum']= portfolio_values.apply(lambda r: r.sum(), axis=1)

        self._details_memory['chart'] = {}
        for name, _ in self._setup.items():
            n = data[name]
            self._details_memory['chart'][name+'_ma'] = mas[name]
            self._details_memory['chart'][name+'_ma_asset'] = data[self._setup[name]['ma_asset']]
            self._details_memory['chart'][name] = n
            self._details_memory['chart'][name+'_value'] = normalize(portfolio_values[name], n)

        return portfolio_values


    def _sell(self, assets, prices, target: float):
        self._log(f" * Sell assets to get ${target:.2f} for tax.")
        sum_value = sum([(prices[name] * asset.amount + self._get_value(name)) for name, asset in assets.items()])
        for name, asset in assets.items():
            value = asset.amount * prices[name] + self._get_value(name)
            percent = (value / sum_value) * 100
            asset_target = (target * percent) / 100
            if asset_target < 0.1:
                self._log(f"Ignore selling [{name}] since amount ${asset_target:.2f} is too small.")
                continue

            if self._values[name] is None:
                amount = asset_target/prices[name]
                self._log(f"Sell {amount} (from {assets[name].amount}) of [{name}] to pay ${asset_target:.2f} of tax.")
                _, gain = asset.sell(amount, prices[name])
                self._tax_model.pay_tax(name, asset_target)
                self._tax_model.add_gain(name, gain)

            else:
                assert self._values[name] >= asset_target
                self._values[name] -= asset_target
                self._tax_model.pay_tax(name, asset_target)


    def _do_rebalancing(self, assets: Dict[str, Asset], prices: pd.Series):
        self._log(f"** Rebalancing: {prices.name}")

        sum_value = sum([(prices[name] * asset.amount) + self._get_value(name) for name, asset in assets.items()])
        for name, asset in assets.items():
            value = asset.amount * prices[name] + self._get_value(name)
            percent = (value / sum_value) * 100
            diff = percent - self._setup[name]['dist']
            self._log(f" * current state [{name}]: ${value:.2f} (percent: {percent:.2f}%, diff: {diff:.2f}%)")

            target_value = (self._setup[name]['dist'] * sum_value)/100
            diff_value = value - target_value

            if diff_value > 0:
                if self._values[name] is None:
                    asset_price = prices[name] * (1 - self._spread)
                    amount = diff_value/asset_price
                    self._log(f" => Sell {amount:.2f}x {name} for ${asset_price:.2f} each (total: ${amount * asset_price:.2f})")
                    _, gain = asset.sell(amount, asset_price)
                    self._tax_model.add_gain(name, gain)

                else:
                    self._log(f" => Reallocate ${diff_value:.2f} from {name} away")
                    self._values[name] -= diff_value

            elif diff_value < 0:
                if self._values[name] is None:
                    asset_price = prices[name] * (1 + self._spread)
                    amount = -diff_value/asset_price
                    self._log(f" => Buy {amount:.2f}x {name} for ${asset_price:.2f} each (total: ${amount * asset_price:.2f})")
                    asset.buy(amount, asset_price)

                else:
                    self._log(f" => Reallocate ${-diff_value:.2f} to {name}")
                    self._values[name] -= diff_value

            value = asset.amount * prices[name] + self._get_value(name)
            percent = (value / sum_value) * 100
            diff = percent - self._setup[name]['dist']
            if self._detailed_output:
                self._log(f"  ==> {name}: ${value:.2f} (percent: {percent:.2f}%, diff: {diff:.2f}%)")


    def _log(self, msg):
        if self._detailed_output:
            print(msg)


    def _get_value(self, name):
        return self._values[name] if self._values[name] is not None else 0