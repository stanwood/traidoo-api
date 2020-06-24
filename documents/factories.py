import abc
import collections
import itertools
from typing import Dict, List

from django.contrib.auth import get_user_model
from loguru import logger

from common.models import Region
from delivery_options.models import DeliveryOption
from documents.models import Document
from jobs.models import Job
from orders.models import Order, OrderItem

User = get_user_model()


class DocumentFactory(abc.ABC):
    DOCUMENT_TYPE = None

    @staticmethod
    def as_dict(user: User) -> Dict:
        return {
            "company_name": user.company_name or "",
            "street": user.street,
            "city": user.city,
            "zip": user.zip,
            "phone": user.phone or "",
            "iban": user.iban or "",
            "email": user.email,
            "invoice_email": user.invoice_email,
            "vat_id": user.vat_id,
            "tax_id": user.tax_id,
            "company_registration_id": user.company_registration_id,
            "association_registration_id": user.association_registration_id,
            "is_certified_organic_producer": user.is_certified_organic_producer,
            "organic_control_body": user.organic_control_body,
            "user_id": user.id,
            "region_id": user.region.id,
        }

    @staticmethod
    def as_company(user: User) -> Dict:
        return {
            "user_id": user.id,
            "company_name": user.company_name,
            "street": user.street,
            "city": user.city,
            "zip": user.zip,
            "email": user.email,
            "invoice_email": user.invoice_email,
            "phone": user.phone,
            "region_id": user.region.id,
        }

    def __init__(self, order: Order, region: Region, seller: User = None):
        self._order = order
        self._region = region
        self._seller_user = seller
        self._settings = order.settings

    @property
    def _items(self) -> List[OrderItem]:
        items = self._order.items.order_by("product__id", "created_at")

        if self._filters:
            items = items.filter(**self._filters)

        items = items.all()

        unique_order_items = []
        for product, order_items in itertools.groupby(
            items, lambda order_item: order_item.product.id
        ):
            order_items = tuple(order_items)
            quantity = sum([item.quantity for item in order_items])
            order_items[0].quantity = quantity
            unique_order_items.append(order_items[0])

        return unique_order_items

    @property
    def product_lines(self) -> List:
        lines = [
            {
                "number": item.product_snapshot["id"],
                "name": item.product_name_expanded,
                "producer": item.product.seller.company_name,
                "amount": item.product_snapshot["amount"],
                "unit": item.product_snapshot["unit"],
                "price": item.product_snapshot["price"],
                "count": item.quantity,
                "vat_rate": item.vat_rate,
                "category": "Produkte",
                "organic_control_body": item.product.seller.organic_control_body,
                "seller_user_id": item.product_snapshot["seller"]["id"],
            }
            for item in self._items
        ]

        lines = sorted(lines, key=lambda l: l.get("name"))
        return lines

    @property
    @abc.abstractmethod
    def seller(self) -> Dict:
        pass

    @property
    @abc.abstractmethod
    def lines(self) -> List:
        pass

    @property
    @abc.abstractmethod
    def buyer(self) -> Dict:
        pass

    @property
    def container_deposit_lines(self) -> List[Dict]:
        return [
            {
                "number": container.id,
                "name": container.size_class,
                "producer": "",
                "amount": 1,
                "unit": "Stück",
                "price": container.deposit,
                "count": container.count,
                "vat_rate": float(container.vat),
                "category": "Pfand",
                "seller_user_id": container.seller_user_id,
            }
            for container in self._order.containers(self._filters)
        ]

    @property
    def delivery_address(self) -> Dict:
        try:
            item = self._items[0]
        except (IndexError, AttributeError):
            return {}

        if item.delivery_address:
            return {
                "company_name": item.delivery_address.company_name,
                "street": item.delivery_address.street,
                "zip": item.delivery_address.zip,
                "city": item.delivery_address.city,
            }
        else:
            return self.buyer

    @property
    def _filters(self):
        return {}

    @property
    def central_platform_user(self) -> User:
        return User.central_platform_user()

    def compose(self):
        document_type = self.DOCUMENT_TYPE.value[0]

        try:
            document = Document.objects.get(
                order_id=self._order.id,
                document_type=document_type,
                buyer=self.buyer,
                seller=self.seller,
            )
            logger.info(f"{document_type} already exist for order {self._order.id}")
            return document
        except Document.DoesNotExist:
            return Document(
                buyer=self.buyer,
                seller=self.seller,
                lines=self.lines,
                order=self._order,
                delivery_address=self.delivery_address,
                document_type=document_type,
            )


class PlatformInvoiceFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.platform_invoice

    @property
    def seller(self) -> Dict:
        return self.as_dict(self.central_platform_user)

    @property
    def buyer(self):
        return self.as_company(self._seller_user)

    @property
    def lines(self):
        platform_fees = self._order.seller_platform_fees
        return [
            {
                "number": "",
                "name": "Plattformgebühr",
                "producer": self.seller.get("company_name"),
                "price": platform_fees[self._seller_user.id],
                "unit": "",
                "count": 1,
                "vat_rate": float(self._settings.platform_fee_vat),
                "amount": 1.0,
                "category": "",
                "seller_user_id": self.seller["user_id"],
            }
        ]


class CreditNoteFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.credit_note

    @property
    def seller(self) -> Dict:
        return self.as_dict(self.central_platform_user)

    @property
    def buyer(self) -> Dict:
        return self.as_dict(self._settings.platform_user)

    @property
    def lines(self) -> List:
        return [
            {
                "number": "",
                "name": "Plattformgebühr",
                "producer": self.seller.get("company_name"),
                "price": self._order.local_platform_owner_platform_fee.netto,
                "unit": "",
                "count": 1,
                "vat_rate": float(
                    self._order.local_platform_owner_platform_fee.vat_rate
                ),
                "amount": 1.0,
                "category": "",
                "seller_user_id": self.seller["user_id"],
            }
        ]


class BuyerPlatformInvoiceFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.buyer_platform_invoice

    @property
    def seller(self) -> Dict:
        return self.as_dict(self.central_platform_user)

    @property
    def buyer(self):
        return self.as_company(self._order.buyer)

    @property
    def lines(self):
        return [
            {
                "number": "",
                "name": "Plattformgebühr",
                "producer": self.seller["company_name"],
                "price": self._order.buyer_platform_fee.netto,
                "unit": "",
                "count": 1,
                "vat_rate": float(self._settings.platform_fee_vat),
                "amount": 1.0,
                "category": "",
                "seller_user_id": self.seller["user_id"],
            }
        ]


class DeliveryOverviewBuyerFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.delivery_overview_buyer

    @property
    def seller(self) -> Dict:
        return self.as_dict(self._region.setting.logistics_company)

    @property
    def buyer(self):
        return self.as_company(self._order.buyer)

    @property
    def lines(self):
        def delivery_company(product, order_item):
            if order_item.is_seller_delivery:  # producer of a product
                company_name = product["seller"]["company_name"]

                if order_item.product.third_party_delivery:
                    logger.debug("Third party delivery.")

                    try:
                        job = Job.objects.get(order_item=order_item, user__isnull=False)
                    except Job.DoesNotExist:
                        pass
                    else:
                        logger.debug(f"Job claimed, ID: {job.id}.")
                        company_name = job.user.company_name

            elif order_item.is_self_collect_delivery:  # buyer of a product
                company_name = self.buyer["company_name"]
            else:  # else 0 and any other value mc swiss delivery
                company_name = (
                    order_item.product.region.setting.logistics_company.company_name
                )

            logger.debug(f"Delivery company name: {company_name}.")
            return company_name

        return [
            {
                "number": item.product_snapshot["id"],
                "name": item.product_name_expanded,
                "producer": self.seller["company_name"],
                "amount": float(item.product_snapshot["amount"]),
                "container_name": (
                    item.product_snapshot["container_type"]["size_class"]
                ),
                "unit": item.product_snapshot["unit"],
                "price": float(item.delivery_fee),
                "count": item.quantity,
                "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                "delivery_company": delivery_company(item.product_snapshot, item),
                "organic_control_body": item.product.seller.organic_control_body,
                "delivery_date": f"{item.delivery_date:%d.%m.%Y}",
                "pickup_address": item.product.seller.address_as_str,
                "delivery_address": item.delivery_address_as_str,
            }
            for item in self._items
        ]


class DeliveryOverviewSellerFactory(DocumentFactory):

    DOCUMENT_TYPE = Document.TYPES.delivery_overview_seller

    @property
    def seller(self):
        return self.as_dict(self._region.setting.logistics_company)

    @property
    def buyer(self):
        """
        Could be confusing but for delivery confirmation we put seller into
        buyer place as document is sent by platform.
        """
        return self.as_company(self._seller_user)

    @property
    def _filters(self):
        return {"product__seller__id": self._seller_user.id}

    @property
    def lines(self):
        return [
            {
                "number": item.product_snapshot["id"],
                "name": item.product_name_expanded,
                "producer": self.seller["company_name"],
                "amount": float(item.product_snapshot["amount"]),
                "container_name": (
                    item.product_snapshot["container_type"]["size_class"]
                ),
                "unit": item.product_snapshot["unit"],
                "price": float(item.delivery_fee),
                "count": float(item.quantity),
                "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                "delivery_company": item.delivery_company.company_name,
                "organic_control_body": item.product.seller.organic_control_body,
                "delivery_date": f"{item.delivery_date:%d.%m.%Y}",
                "pickup_address": item.product.seller.address_as_str,
                "delivery_address": item.delivery_address_as_str,
            }
            for item in self._items
        ]


class OrderConfirmationBuyerFactory(DocumentFactory):

    DOCUMENT_TYPE = Document.TYPES.order_confirmation_buyer

    @property
    def seller(self) -> Dict:
        try:
            return self.as_dict(self._region.setting.platform_user)
        except AttributeError:
            return self.as_dict(self.central_platform_user)

    @property
    def buyer(self):
        return self.as_company(self._order.buyer)

    @property
    def delivery_fee_lines(self):
        lines = []

        for item in self._items:
            if item.is_seller_delivery and item.delivery_fee > 0:
                user_delivering_product = item.delivery_company
                lines.append(
                    {
                        "number": item.product_snapshot["id"],
                        "name": f"Lieferung von {item.product_name_expanded}",
                        "producer": user_delivering_product.company_name,
                        "amount": 1.0,
                        "unit": "",
                        "price": float(item.delivery_fee),
                        "count": 1,
                        "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                        "category": "Logistik",
                        "seller_user_id": user_delivering_product.id,
                    }
                )

        return lines

    @property
    def lines(self):
        lines = self.product_lines
        lines += self.container_deposit_lines

        # add mc-swiss logistics
        lines += [
            {
                "number": item.product_snapshot["id"],
                "name": f"Lieferung von {item.product_name_expanded}",
                "producer": item.product.region.setting.logistics_company.company_name,
                "amount": 1.0,
                "unit": "",
                "price": float(item.delivery_fee),
                "count": 1,
                "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                "category": "Logistik",
                "seller_user_id": self._region.setting.logistics_company.id,
            }
            for item in self._items
            if item.is_central_logistic_delivery and item.delivery_fee > 0
        ]

        # add producer logistics
        lines += self.delivery_fee_lines

        if not self._order.buyer.is_cooperative_member:
            # add a line for platform fee only if buyer is not cooperative member
            central_platform_user = User.central_platform_user()
            lines.append(
                {
                    "number": "",
                    "name": "Plattformgebühr",
                    "producer": central_platform_user.company_name,
                    "price": self._order.buyer_platform_fee.netto,
                    "unit": "",
                    "count": 1,
                    "vat_rate": float(self._settings.platform_fee_vat),
                    "category": "Plattform",
                    "amount": 1.0,
                    "seller_user_id": central_platform_user.id,
                }
            )

        return lines


class ThirdPartyLogisticsInvoiceFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.logistics_invoice

    @property
    def seller(self) -> Dict:
        return self.as_dict(self._region.setting.logistics_company)

    @property
    def buyer(self) -> Dict:
        return self.as_company(self._order.buyer)

    @property
    def _filters(self):
        return {
            "delivery_fee__gt": 0,
            "product__third_party_delivery": True,
            "delivery_option__id": 1,
            "job__user__isnull": False,
            "product__region__id": self._region.id,
        }

    def supplier(self, user: User) -> Dict:
        return self.as_dict(user)

    @property
    def lines(self):
        lines_dict = collections.defaultdict(lambda: collections.defaultdict(list))

        for item in self._items:
            logger.debug("Third party delivery.")

            job = Job.objects.get(order_item=item)
            logger.debug(f"Job claimed, ID: {job.id}.")
            producer = job.user.company_name
            seller_user_id = job.user.id

            logger.debug(
                f"Adding a new line. Producer: {producer}, seller user "
                f"ID: {seller_user_id}."
            )

            line = {
                "number": item.product_snapshot["id"],
                "name": f"Lieferung von {item.product_name_expanded}",
                "producer": producer,
                "amount": 1.0,
                "unit": "",
                "price": float(item.delivery_fee),
                "count": 1,
                "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                "category": "",
                "seller_user_id": seller_user_id,
            }

            lines_dict[seller_user_id]["seller_data"] = self.supplier(job.user)
            lines_dict[seller_user_id]["lines"].append(line)

        return lines_dict

    def compose(self):
        return (
            Document(
                buyer=self.buyer,
                seller=lines["seller_data"],
                lines=lines["lines"],
                order=self._order,
                delivery_address=self.delivery_address,
                document_type=self.DOCUMENT_TYPE.value[0],
            )
            for lines in self.lines.values()
        )


class LogisticsInvoiceFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.logistics_invoice

    @property
    def seller(self) -> Dict:
        return self.as_dict(self._region.setting.logistics_company)

    @property
    def buyer(self) -> Dict:
        return self.as_company(self._order.buyer)

    @property
    def _filters(self):
        return {
            "delivery_fee__gt": 0,
            "product__region__id": self._region.id,
            "delivery_option__id": DeliveryOption.CENTRAL_LOGISTICS,
        }

    @property
    def lines(self):
        return [
            {
                "number": item.product_snapshot["id"],
                "name": f"Lieferung von {item.product_name_expanded}",
                "producer": self.seller["company_name"],
                "amount": 1.0,
                "unit": "",
                "price": float(item.delivery_fee),
                "count": 1,
                "vat_rate": float(self._region.setting.mc_swiss_delivery_fee_vat),
                "category": "",
                "seller_user_id": self.seller["user_id"],
            }
            for item in self._items
        ]


class ProducerInvoiceFactory(DocumentFactory):
    DOCUMENT_TYPE = Document.TYPES.producer_invoice

    @property
    def seller(self) -> Dict:
        return self.as_dict(self._seller_user)

    @property
    def buyer(self) -> Dict:
        return self.as_company(self._order.buyer)

    @property
    def _filters(self):
        return {"product__seller__id": self._seller_user.id}

    @property
    def delivery_fee_lines(self):
        lines = []

        for item in self._items:
            if item.is_seller_delivery and item.delivery_fee > 0:
                producer = self.seller["company_name"]
                seller_user_id = self.seller["user_id"]

                if item.product.third_party_delivery:
                    logger.debug("Third party delivery.")

                    try:
                        job = Job.objects.get(order_item=item)
                    except Job.DoesNotExist:
                        pass
                    else:
                        if job.user:
                            continue

                lines.append(
                    {
                        "number": item.product_snapshot["id"],
                        "name": f"Lieferung von {item.product_name_expanded}",
                        "producer": producer,
                        "amount": 1.0,
                        "unit": "",
                        "price": float(item.delivery_fee),
                        "count": 1,
                        "vat_rate": float(self._settings.mc_swiss_delivery_fee_vat),
                        "category": "Logistik",
                        "seller_user_id": seller_user_id,
                    }
                )

        return lines

    @property
    def lines(self):
        lines = self.product_lines
        lines += self.container_deposit_lines
        lines += self.delivery_fee_lines

        return lines
