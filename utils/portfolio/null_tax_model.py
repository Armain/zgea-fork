from utils.portfolio.tax_model import TaxModel


class NullTaxModel(TaxModel):
    def add_gain(self, asset: str, gain: float):
        pass

    def pay_tax(self, asset: str, value: float):
        pass

    @property
    def open_tax(self) -> float:
        return 0.0
