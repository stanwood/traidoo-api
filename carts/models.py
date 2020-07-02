import functools
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F

from common.models import Region
from core.calculators.item_calculator import ItemCalculatorMixin
from core.calculators.order_calculator import OrderCalculatorMixin
from core.calculators.value import Value
from core.db.base import BaseAbstractModel
from core.payments.transport_insurance import calculate_transport_insurance_rate
from delivery_addresses.models import DeliveryAddress
from delivery_options.models import DeliveryOption
from items.models import Item
from products.models import Product
from django.utils.translation import gettext_lazy as _


class Cart(OrderCalculatorMixin, BaseAbstractModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User")
    )
    earliest_delivery_date = models.DateField(
        null=True, blank=True, verbose_name=_("Earliest delivery date")
    )
    delivery_address = models.ForeignKey(
        DeliveryAddress,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name=_("Delivery address"),
    )

    @property
    def calc_items(self):
        return [
            OrderCalculatorMixin.Item(
                price=float(cart_item.product.price),
                count=cart_item.quantity,
                vat=float(cart_item.product.vat),
                amount=float(cart_item.product.amount),
                seller=cart_item.product.seller.id,
            )
            for cart_item in self.items.all()
        ]

    @property
    def total(self):
        return self.price

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")


class CartItem(ItemCalculatorMixin, BaseAbstractModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name=_("Product")
    )
    cart = models.ForeignKey(
        Cart, related_name="items", on_delete=models.CASCADE, verbose_name=_("Cart")
    )
    latest_delivery_date = models.DateField(verbose_name=_("Latest delivery date"))
    quantity = models.IntegerField(default=0, verbose_name=_("Quantity"))
    delivery_option = models.ForeignKey(
        DeliveryOption,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Delivery option"),
    )

    class Meta:
        unique_together = (("cart", "product", "latest_delivery_date"),)
        ordering = ["created_at"]
        verbose_name = _("Cart item")

    def release_product_item(
        self, product_id=None, quantity=None, latest_delivery_date=None
    ):
        product_item = Item.objects.filter(
            product_id=product_id or self.product.id,
            latest_delivery_date=latest_delivery_date or self.latest_delivery_date,
        ).update(quantity=F("quantity") + (quantity or self.quantity))

        if product_item < 1:
            Item.objects.create(
                product_id=product_id or self.product.id,
                latest_delivery_date=latest_delivery_date or self.latest_delivery_date,
                quantity=quantity or self.quantity,
            )

    @property
    def settings(self):
        return self.cart.user.region.settings.first()

    @property
    def buyer(self):
        return self.cart.user

    @property
    def product_price(self) -> Decimal:
        return self.product.price

    @property
    def amount(self) -> Decimal:
        return Decimal(self.product.amount)

    @property
    def product_vat(self):
        return self.product.vat

    @property
    def container_delivery_fee(self) -> Decimal:
        return self.product.container_type.delivery_fee

    @property
    def product_delivery_charge(self) -> Decimal:
        return self.product.delivery_charge

    @property
    def delivery_fee_net(self):
        return self._delivery_fee().netto

    @property
    def delivery_fee_gross(self):
        return self._delivery_fee().brutto

    @property
    def delivery_fee_vat(self):
        return self._delivery_fee().vat

    @property
    def delivery_fee_vat_rate(self):
        return self._delivery_fee().vat_rate

    @property
    def platform_fee_net(self):
        return self.buyer_platform_fee.netto

    @property
    def platform_fee_gross(self):
        return self.buyer_platform_fee.brutto

    @property
    def platform_fee_vat(self):
        return self.buyer_platform_fee.vat

    @property
    def platform_fee_vat_rate(self):
        return self.buyer_platform_fee.vat_rate

    @property
    def container_deposit_net(self) -> Decimal:
        return self.product.container_type.deposit

    @property
    def seller_delivery(self) -> Value:
        seller_region_settings = self.product.region.setting
        return Value(
            self.product_delivery_charge,
            seller_region_settings.mc_swiss_delivery_fee_vat,
        )

    def central_logistic_delivery(self, region: Region) -> Value:
        region_settings = region.settings.first()
        logistics_net = self.transport_insurance

        container_delivery_fee = self.product.container_type.delivery_fee
        if container_delivery_fee:
            logistics_net += container_delivery_fee * Decimal(self.quantity)

        return Value(
            logistics_net.quantize(Decimal(".01"), "ROUND_HALF_UP"),
            region_settings.mc_swiss_delivery_fee_vat,
        )
