from utils.portfolio import TaxModel

class GermanTaxModel(TaxModel):
    _SHARES = ['sp500', 'ndx100']
    _TAX = 26.38

    def __init__(self, detailed_output=False):
        self._bucket = 0.0
        self._detailed_output = detailed_output


    def add_gain(self, asset: str, gain: float):
        for s in self._SHARES:
            if s in asset:
                self._log(f"** Consider 'Teilfreistellung' for '{asset}'")
                gain = gain * 0.7
                break

        self._bucket += (gain * self._TAX)/100
        self._log(f"** Tax bucket is now: ${self._bucket:.2f}")


    def pay_tax(self, asset: str, value: float):
        self._bucket -= value
        self._log(f"** Payed Tax. Tax bucket is now: ${self._bucket:.2f}")


    @property
    def open_tax(self) -> float:
        return self._bucket


    def _log(self, msg):
        if self._detailed_output:
            print(msg)
