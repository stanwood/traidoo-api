from decimal import Decimal


class Value(object):
    def __init__(self, netto, vat=0):

        self.netto = float(
            Decimal(str(netto)).quantize(Decimal(".01"), "ROUND_HALF_UP")
        )

        self.vat_rate = vat
        self.vat = Decimal(str(netto)) * Decimal(str(vat)) / Decimal("100")
        self.vat = self.vat.quantize(Decimal(".01"), "ROUND_HALF_UP")
        self.vat = float(self.vat)

    def __add__(self, other):
        if self.vat_rate != other.vat_rate:
            raise ValueError(
                "Cannot add values of different VAT rates. {} != {}".format(
                    self.vat_rate, other.vat_rate
                )
            )

        value = Decimal(str(self.netto)) + Decimal(str(other.netto))
        value = float(value)
        value = Value(value, self.vat_rate)

        # we do not want to include rounding errors which were lost when each
        # of Values vat was calculated
        value.vat = float(Decimal(str(self.vat)) + Decimal(str(other.vat)))

        return value

    def __iadd__(self, other):

        self.netto = float(Decimal(str(self.netto)) + Decimal(str(other.netto)))
        self.vat = float(Decimal(str(self.vat)) + Decimal(str(other.vat)))

        return self

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    @property
    def brutto(self):
        return float(Decimal(str(self.netto)) + Decimal(str(self.vat)))
