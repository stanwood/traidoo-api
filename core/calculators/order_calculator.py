import abc
import collections
import itertools
from decimal import Decimal

from core.calculators.utils import round_float
from core.calculators.value import Value


class OrderCalculatorMixin:
    class Item:
        def __init__(self, price, count, vat, amount=1, seller=None):
            self.price = price
            self.count = count
            self.amount = amount
            self.vat = vat
            self.seller = seller

        @property
        def value(self):
            return Value(
                Decimal(self.price)
                * Decimal(self.count)
                * Decimal(self.amount),  # endPrice - front
                Decimal(self.vat),
            )

    @property
    @abc.abstractmethod
    def calc_items(self):
        """This property should return list of items for further calculation in the mixin"""
        pass

    @staticmethod
    def calculate_gross_value_of_items(calc_items):
        items_values = [item.value for item in calc_items]
        items_values = sorted(items_values, key=lambda item: item.vat)
        gross = Decimal("0")
        for vat_rate, lines_by_vat_rate in itertools.groupby(
            items_values, lambda item_value: item_value.vat_rate
        ):
            sum_net_value = sum(value.netto for value in lines_by_vat_rate)
            total_value = Value(sum_net_value, vat_rate)
            gross += Decimal(str(total_value.brutto))
        return gross

    @property
    def price(self):
        total = sum(item.value.netto for item in self.calc_items)
        return round_float(total)

    @property
    def price_gross(self) -> float:
        gross = Decimal("0")
        items = sorted(self.calc_items, key=lambda item: item.seller)
        for seller_id, items in itertools.groupby(items, lambda item: item.seller):
            gross_per_seller = self.calculate_gross_value_of_items(items)
            gross += gross_per_seller

        return round_float(gross)

    @property
    def price_gross_cents(self):
        return int(round(self.price_gross * 100, 0))
