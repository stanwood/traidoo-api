from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import Enum

import dateutil
import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from loguru import logger

from common.models import Region
from core.calculators.item_calculator import ItemCalculatorMixin
from core.calculators.order_calculator import OrderCalculatorMixin
from core.calculators.utils import round_float
from core.calculators.value import Value
from core.db.base import BaseAbstractModel
from delivery_addresses.models import DeliveryAddress
from delivery_options.models import DeliveryOption
from products.models import Product

User = get_user_model()


class Order(OrderCalculatorMixin, BaseAbstractModel):
    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    class STATUSES(Enum):
        cart = (0, _("Cart"))
        paid = (1, _("Paid"))
        ordered = (2, _("Ordered"))

        @classmethod
        def get_value(cls, member):
            return getattr(cls, member).value[0]

    @dataclass
    class Container:
        id: int
        size_class: str
        deposit: float
        vat: float
        count: int
        seller_user_id: int

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Buyer"),
    )
    status = models.IntegerField(
        default=0, choices=[s.value for s in STATUSES], verbose_name=_("Status")
    )
    total_price = models.FloatField(
        blank=True, null=True, verbose_name=_("Total price")
    )
    earliest_delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Earliest delivery date")
    )  # TODO: why it's a datetime? why not date?
    processed = models.BooleanField(default=False, verbose_name=_("Processed"))
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="orders",
        blank=False,
        help_text=_("Region in which order took place"),
        verbose_name=_("Region"),
    )

    @cached_property
    def setting(self):
        return self.region.settings.all()[0]

    @cached_property
    def order_items(self):
        return list(self.items.all())

    def recalculate_items_delivery_fee(self):
        for item in self.items.all():
            item.delivery_fee = Decimal(str(item._delivery_fee().netto))
            item.save()

    @property
    def total_price_central_delivery(self):
        prices = []
        for item in self.items.all():
            if item.is_central_logistic_delivery:
                prices.append(item.price.netto)

        return round_float(sum(prices))

    @property
    def total_price_traidoo_delivery_or_third_party_delivery(self):
        prices = []

        for item in self.items.all():
            if (
                item.is_seller_delivery
                and item.product.third_party_delivery
                and item.is_third_party_delivery
            ):
                prices.append(item.price.netto)

        prices.append(self.total_price_central_delivery)

        return round_float(sum(prices))

    @property
    def calc_items(self):
        product_items = [
            OrderCalculatorMixin.Item(
                price=item.product_price,
                count=item.quantity,
                vat=item.product_vat,
                amount=item.amount,
                seller=item.product_snapshot["seller"]["id"],
            )
            for item in self.order_items
        ]

        container_deposits = [
            OrderCalculatorMixin.Item(
                price=container.deposit,
                count=container.count,
                vat=float(container.vat),
                amount=1,
                seller=container.seller_user_id,
            )
            for container in self.containers()
        ]

        logistics_fees = [
            OrderCalculatorMixin.Item(
                price=float(item.delivery_fee),
                count=1,
                vat=float(self.setting.mc_swiss_delivery_fee_vat),
                amount=1,
                seller=item.delivery_company_user_id,
            )
            for item in self.order_items
            if (item.is_central_logistic_delivery or item.is_seller_delivery)
            and item.delivery_fee > 0
        ]

        if not self.buyer.is_cooperative_member:
            platform_fees = [
                OrderCalculatorMixin.Item(
                    price=self.sum_of_seller_platform_fees.netto
                    + self.buyer_platform_fee.netto,
                    count=1,
                    vat=float(self.setting.platform_fee_vat),
                    amount=1,
                    seller=User.central_platform_user().id,
                )
            ]
        else:
            platform_fees = []
        return product_items + container_deposits + logistics_fees + platform_fees

    @property
    def buyer_platform_fee(self) -> Value:
        return sum(item.buyer_platform_fee for item in self.items.all())

    @property
    def seller_platform_fees(self) -> dict:
        """

        :return: dict of platform fees for each seller
        """
        platform_fees = {}
        values = {}

        for order_item in self.items.all():
            seller = order_item.product.seller
            if seller in values:
                values[seller] += order_item.price.netto
            else:
                values[seller] = order_item.price.netto

        for seller, total_seller_price in values.items():
            total_price = Decimal(str(total_seller_price)).quantize(
                Decimal(".01"), "ROUND_HALF_UP"
            )
            platform_fee = (
                total_price * seller.seller_platform_fee_rate / Decimal("100")
            ).quantize(Decimal(".01"), "ROUND_HALF_UP")
            platform_fees[seller.id] = float(platform_fee)

        return platform_fees

    @property
    def sum_of_seller_platform_fees(self) -> Value:
        sum_of_seller_fees = sum(
            seller_fee for seller_fee in self.seller_platform_fees.values()
        )
        return Value(sum_of_seller_fees, self.setting.platform_fee_vat)

    @property
    def total_platform_fees(self) -> Value:
        return self.sum_of_seller_platform_fees + self.buyer_platform_fee

    @property
    def local_platform_owner_platform_fee(self) -> Value:
        total_platform_fees = Decimal(str(self.total_platform_fees.netto))
        local_platform_fee_share = total_platform_fees * (
            Decimal("1") - self.setting.central_share / Decimal("100")
        )
        local_platform_fee_share = local_platform_fee_share.quantize(
            Decimal(".01"), "ROUND_HALF_UP"
        )
        return Value(local_platform_fee_share, self.setting.platform_fee_vat)

    @property
    def has_central_logistics_deliveries(self):
        """ Backward compatibility to reuse documents generation tasks"""
        return any(
            item.delivery_option.id == DeliveryOption.CENTRAL_LOGISTICS
            for item in self.items.all()
        )

    @property
    def has_third_party_deliveries(self):
        return self.items.filter(job__user__isnull=False).exists()

    def set_paid(self):
        self.status = self.STATUSES.get_value("paid")

    @property
    def is_paid(self):
        return self.status == self.STATUSES.get_value("paid")

    def containers(self, filters=None):
        containers = {}
        deposit_vat = float(self.setting.deposit_vat)
        if filters:
            items_queryset = self.items.filter(**filters)
        else:
            items_queryset = self.items.all()

        for item in items_queryset:
            product = item.product_snapshot
            container = product["container_type"]

            try:
                containers[f"${container['id']}|${product['seller']['id']}"]
            except KeyError:
                containers[
                    f"${container['id']}|${product['seller']['id']}"
                ] = self.Container(
                    id=container["id"],
                    size_class=container["size_class"],
                    deposit=float(container["deposit"] or 0),
                    vat=deposit_vat,
                    count=item.quantity,
                    seller_user_id=product["seller"]["id"],
                )
            else:
                containers[
                    f"${container['id']}|${product['seller']['id']}"
                ].count += item.quantity

        containers = containers.values()
        containers = sorted(containers, key=lambda c: c.size_class)
        return containers

    @property
    def sellers_regions(self):
        return set([item.product.seller.region for item in self.items.all()])

    def __str__(self):
        try:
            company_name = self.buyer.company_name
        except AttributeError:
            company_name = None
        return f"{company_name} {self.total_price}"


class OrderItem(BaseAbstractModel, ItemCalculatorMixin):
    # TODO: Do we need the product? We have the product snapshot.
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, related_name="items", on_delete=models.PROTECT)
    latest_delivery_date = models.DateField()
    delivery_address = models.ForeignKey(
        DeliveryAddress, on_delete=models.SET_NULL, null=True, blank=True
    )
    quantity = models.IntegerField()
    product_snapshot = JSONField()
    delivery_option = models.ForeignKey(DeliveryOption, on_delete=models.PROTECT)
    delivery_fee = models.DecimalField(decimal_places=2, max_digits=10, default=0)

    class Meta:
        unique_together = (("order", "product", "latest_delivery_date"),)

    def __str__(self):
        return f"{self.product_snapshot['name']} x {self.quantity}"

    @cached_property
    def setting(self):
        return self.order.region.settings.all()[0]

    @property
    def buyer(self):
        return self.order.buyer

    @property
    def delivery_address_as_str(self):
        if self.delivery_address and self.delivery_option.id != DeliveryOption.BUYER:
            return self.delivery_address.as_str()
        else:
            return self.order.buyer.address_as_str

    @property
    def product_price(self) -> Decimal:
        return Decimal(str(self.product_snapshot["price"]))

    @property
    def amount(self) -> Decimal:
        return Decimal(str(self.product_snapshot["amount"]))

    @property
    def total_price_central_delivery(self) -> Decimal:
        return self.order.total_price_central_delivery

    @property
    def product_vat(self) -> Decimal:
        return Decimal(str(self.product_snapshot["vat"]))

    @property
    def product_name_expanded(self):
        """ Takes product name from snapshot and adds Bio if necessary"""
        name = self.product_snapshot["name"]
        if self.product_snapshot.get("is_organic", False):
            name += " Bio"
        return name

    @property
    def container_deposit_net(self) -> Decimal:
        return Decimal(self.product_snapshot["container_type"]["deposit"])

    @property
    def product_delivery_charge(self) -> Decimal:
        return Decimal(self.product_snapshot["delivery_charge"])

    @property
    def vat_rate(self):
        return self.product_snapshot["vat"]

    @property
    def delivery_date(self):
        created_at_aware = timezone.localtime(
            self.order.created_at,
            timezone=pytz.timezone(settings.USER_DEFAULT_TIME_ZONE),
        )

        # weekend orders always delivered on Tuesday
        if created_at_aware.weekday() >= 5:
            delivery_date = created_at_aware + timedelta(
                days=7 - created_at_aware.weekday() + 1
            )
        else:
            if created_at_aware.hour < 12:
                delivery_date = created_at_aware + timedelta(days=1)
            else:
                delivery_date = created_at_aware + timedelta(days=2)

        # if delivery date before earliest delivery date then move it forward
        if self.order.earliest_delivery_date.date() > delivery_date.date():
            delivery_date = self.order.earliest_delivery_date

        # if delivery date is on weekend we need to move it to monday
        if delivery_date.weekday() >= 5:
            delivery_date += timedelta(days=7 - delivery_date.weekday())

        return delivery_date.date()

    @property
    def delivery_company(self):
        # TODO: Is it possible that there is no delivery company? What then?
        delivery_company = None

        if self.is_central_logistic_delivery:
            delivery_company = self.product.region.setting.logistics_company
        elif self.is_seller_delivery and self.product.third_party_delivery:
            try:
                delivery_company = self.job.user or User.objects.get(
                    id=self.product_snapshot["seller"]["id"]
                )
            except (AttributeError, TypeError):
                delivery_company = User.objects.get(
                    id=self.product_snapshot["seller"]["id"]
                )
        elif self.is_seller_delivery:
            delivery_company = User.objects.get(
                id=self.product_snapshot["seller"]["id"]
            )
        elif self.is_self_collect_delivery:
            delivery_company = self.order.buyer

        if not delivery_company:
            logger.exception(
                f"Could not determine user for delivery of order item {self.id}."
            )

        return delivery_company

    @property
    def delivery_company_user_id(self):
        try:
            return self.delivery_company.id
        except AttributeError:
            return None


def utc_to_cet(utc_time):
    utc = dateutil.tz.gettz("UTC")
    cet = dateutil.tz.gettz("CET")
    utc_time = utc_time.replace(tzinfo=utc)
    return utc_time.astimezone(cet)


@receiver(pre_save, sender=OrderItem)
def calculate_delivery_fee(sender, instance, **kwargs):
    if not instance.product_snapshot:
        instance.product_snapshot = instance.product.create_snapshot()
