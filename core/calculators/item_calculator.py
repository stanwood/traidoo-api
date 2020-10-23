import abc
import functools
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from core.calculators.value import Value
from core.payments.transport_insurance import calculate_transport_insurance_rate


class ItemCalculatorMixin:
    @property
    @abc.abstractmethod
    def product_price(self) -> Decimal:
        pass

    @property
    @abc.abstractmethod
    def amount(self) -> Decimal:
        pass

    @property
    @abc.abstractmethod
    def product_vat(self):
        pass

    @property
    @abc.abstractmethod
    def container_deposit_net(self) -> Decimal:
        pass

    @property
    @abc.abstractmethod
    def product_delivery_charge(self) -> Decimal:
        pass

    @property
    @abc.abstractmethod
    def settings(self):
        pass

    @property
    @abc.abstractmethod
    def total_price_central_delivery(self) -> Decimal:
        pass

    @property
    def price(self):
        return Value(self.quantity * self.product_price * self.amount, self.product_vat)

    @property
    def price_gross(self) -> float:
        return self.price.brutto

    @property
    def price_net(self) -> float:
        return self.price.netto

    @property
    def buyer_platform_fee(self) -> Value:
        value = (
            Decimal(str(self.price.netto))
            * self.buyer.buyer_platform_fee_rate
            / Decimal("100")
        )
        platform_fee = value.quantize(Decimal(".01"), "ROUND_HALF_UP")
        return Value(float(platform_fee), self.settings.platform_fee_vat)

    @property
    def is_central_logistic_delivery(self):
        return self.delivery_option.id == 0

    @property
    def is_seller_delivery(self):
        return self.delivery_option.id == 1

    @property
    def is_self_collect_delivery(self):
        return self.delivery_option.id == 2

    @property
    def is_third_party_delivery(self):
        if not settings.FEATURES["routes"]:
            return False

        if not self.product.third_party_delivery:
            return False

        return self.is_seller_delivery

    @property
    def transport_insurance(self) -> Decimal:
        """
        Calculates transport insurance
        """

        price_net = Decimal(str(self.price_net))
        insurance = price_net * calculate_transport_insurance_rate(
            self.total_price_central_delivery
        )
        return insurance.quantize(Decimal(".01"), "ROUND_HALF_UP")

    @property
    def central_logistic_delivery_fee(self) -> Value:
        value = self.transport_insurance

        return Value(
            value.quantize(Decimal(".01"), "ROUND_HALF_UP"),
            self.settings.mc_swiss_delivery_fee_vat,
        )

    @property
    def seller_delivery_fee(self) -> Value:
        return Value(
            self.product_delivery_charge,
            self.settings.mc_swiss_delivery_fee_vat,
        )

    def _delivery_fee(self) -> Value:
        if self.is_central_logistic_delivery:
            return self.central_logistic_delivery_fee
        elif self.is_seller_delivery:
            return self.seller_delivery_fee
        return Value(0)

    @property
    def container_deposit(self) -> Value:
        return Value(self.container_deposit_net, self.settings.deposit_vat)
