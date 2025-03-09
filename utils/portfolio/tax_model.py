import abc

class TaxModel(abc.ABC):
    def add_gain(self, asset: str, gain: float):
        ...

    def pay_tax(self, asset: str, value: float):
        ...

    @property
    def open_tax(self) -> float:
        ...
