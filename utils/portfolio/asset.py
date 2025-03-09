from typeguard import typechecked
from typing import Tuple
from dataclasses import dataclass

TOLERANCE = 0.001


@dataclass
class AssetEntry():
    amount: float
    price: float


class Asset():
    @typechecked()
    def __init__(self, name: str, detailed_output: bool = False):
        self._name = name
        self._amount = 0.0
        self._detailed_output = detailed_output
        self._buffer = []


    @typechecked()
    def buy(self, amount: float, price: float) -> float:
        total = amount*price
        if self._detailed_output:
            print(f"Buy {amount:.2f}x '{self._name}' for ${price:.2f} each (total: ${total:.2f}).")
        self._buffer.append(AssetEntry(amount = amount, price = price))
        return total


    @typechecked()
    def sell(self, amount: float, price: float) -> Tuple[float, float]:
        """
        Sells an amount of the asset.

        :param amount: The amount to sell.
        :param price: The price to sell for.
        :return: Returns a tuple, which contains the total money and the gain.
        """
        total = amount*price
        gain = 0

        if self._detailed_output:
            print(f"Sell {amount:.2f}x '{self._name}' for ${price:.2f} each (total: ${total:.2f}).")

        while True:
            assert len(self._buffer) > 0, "Cannot sell assets you don't have in your buffer."
            next_entry = self._buffer[0]
            sell_amount = min(next_entry.amount, amount)
            amount -= sell_amount
            next_entry.amount -= sell_amount
            gain += sell_amount * (price - next_entry.price)
            if abs(next_entry.amount) < TOLERANCE:
                self._buffer.pop(0)
            if abs(amount) < TOLERANCE:
                break

        return total, gain


    @property
    def amount(self) -> float:
        return sum([e.amount for e in self._buffer])
