import pandas as pd
from typing import Dict, Optional
from typeguard import typechecked
from dateutil.relativedelta import relativedelta

from utils.portfolio.asset import Asset
from utils.portfolio.tax_model import TaxModel

from .null_tax_model import NullTaxModel


class Portfolio():
    @typechecked()
    def __init__(
            self,
            distribution: Dict[str, float],
            start_value: float = 10000,
            rebalancing: Optional[relativedelta] = None,
            rebalancing_offset: Optional[relativedelta] = None,
            detailed_output: bool = False,
            tax_model: TaxModel = NullTaxModel(),
    ):
        assert len(distribution.keys()) >= 1, "You must specify at least one ETF."
        assert len(distribution.keys()) == len(set(distribution.keys())), "Every ETF must be unique in your portfilio."
        assert sum([d for d in distribution.values()]) <= 100, f"Your Portfolio has an allocation of {sum([d for d in distribution.values()])}%"

        self._distribution = distribution
        self._start_value = start_value
        self._rebalancing = rebalancing
        self._rebalancing_offset = rebalancing_offset
        self._detailed_output = detailed_output
        self._tax_model = tax_model


    def backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        asset_names = list(self._distribution.keys())
        assets = {}
        print(f"Backtest of portfolio with assts: {asset_names}")

        start_date = data.iloc[0].name
        end_date = self._calc_end_date(start_date, data, self._rebalancing_offset)

        for name, distribution in self._distribution.items():
            assert name in data.columns, f"Asset with the name {name} does not exist in data ({data.columns})."
            value_to_buy = (self._start_value * distribution)/100
            asset_price = data.loc[start_date, name]
            assets[name] = Asset(name, detailed_output = self._detailed_output)
            assets[name].buy(value_to_buy/asset_price, asset_price)


        portfolio_values = pd.DataFrame(columns=asset_names+['sum'], index=data.index)

        while True:
            for name in asset_names:
                portfolio_values.loc[start_date:end_date, name] = data.loc[start_date:end_date, name] * assets[name].amount

            if end_date >= data.iloc[-1].name:
                break

            else:
                self._do_rebalancing(assets, data.loc[end_date, :])
                start_date = end_date
                end_date = self._calc_end_date(start_date, data)


        portfolio_values['sum']= portfolio_values.apply(lambda r: r.sum(), axis=1)

        return portfolio_values


    def _calc_end_date(self, start_date, data, rebalancing_offset = None):
        if self._rebalancing is not None:
            next_rebalancing_date = start_date + self._rebalancing
            if rebalancing_offset is not None:
                next_rebalancing_date += rebalancing_offset
            return min(data.iloc[-1].name, next_rebalancing_date)

        else:
            return data.iloc[-1].name


    def _do_rebalancing(self, assets, prices):
        if self._detailed_output:
            print(f"Rebalancing: {prices.name}")
        sum_value = sum([prices[name] * asset.amount for name, asset in assets.items()])
        for name, asset in assets.items():
            value = asset.amount * prices[name]
            percent = (value / sum_value) * 100
            diff = percent - self._distribution[name]
            if self._detailed_output:
                print(f" * {name}: ${value:.2f} (percent: {percent:.2f}%, diff: {diff:.2f}%)")

            target_value = (self._distribution[name] * sum_value)/100
            diff_value = value - target_value
            if diff_value > 0:
                _, gain = asset.sell(diff_value/prices[name], prices[name])
                self._tax_model.add_gain(asset=name, gain=gain)

            elif diff_value < 0:
                asset.buy(-diff_value/prices[name], prices[name])

            value = asset.amount * prices[name]
            percent = (value / sum_value) * 100
            diff = percent - self._distribution[name]
            if self._detailed_output:
                print(f"   => {name}: ${value:.2f} (percent: {percent:.2f}%, diff: {diff:.2f}%)")


        while self._tax_model.open_tax > 1.0:
            self._sell(assets, prices, self._tax_model.open_tax)


    def _sell(self, assets, prices, target: float):
        self._log(f" * Sell assets to get ${target:.2f} for tax.")
        sum_value = sum([(prices[name] * asset.amount) for name, asset in assets.items()])
        for name, asset in assets.items():
            value = asset.amount * prices[name]
            percent = (value / sum_value) * 100
            asset_target = (target * percent) / 100
            if asset_target < 0.1:
                self._log(f"Ignore selling [{name}] since amount ${asset_target:.2f} is too small.")
                continue

            amount = asset_target/prices[name]
            self._log(f"Sell {amount} (from {assets[name].amount}) of [{name}] to pay ${asset_target:.2f} of tax.")
            _, gain = asset.sell(amount, prices[name])
            self._tax_model.pay_tax(name, asset_target)
            self._tax_model.add_gain(name, gain)


    def _log(self, msg):
        if self._detailed_output:
            print(msg)
