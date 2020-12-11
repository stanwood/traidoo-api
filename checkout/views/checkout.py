from django.conf import settings
from loguru import logger
from rest_framework import status, views
from rest_framework.response import Response

from carts.models import Cart
from carts.utils import validate_earliest_delivery_date
from core.currencies import CURRENT_CURRENCY_CODE
from core.permissions.buyer_or_seller import IsBuyerOrSellerUser
from core.tasks.mixin import TasksMixin
from delivery_options.models import DeliveryOption
from orders.models import Order, OrderItem
from orders.serializers.order import OrderSerializer

from ..serializers.checkout import CartSerializer


class CheckoutView(TasksMixin, views.APIView):
    permission_classes = (IsBuyerOrSellerUser,)

    def post(self, request, format=None):
        region_settings = request.region.setting

        try:
            cart = (
                Cart.objects.filter(user=self.request.user)
                .order_by("-created_at")
                .select_related("user", "delivery_address")
                .prefetch_related(
                    "items__product",
                    "items__product__container_type",
                    "items__delivery_option",
                    "items__product__seller",
                    "items__product__region",
                    "items__product__regions",
                    "items__product__category",
                    "items__product__category__icon",
                    "user__region__settings",
                    "items__product__delivery_options",
                )
                .first()
            )
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        validate_earliest_delivery_date(cart.earliest_delivery_date)

        if (
            not cart.delivery_address
            and cart.items.exclude(delivery_option_id=DeliveryOption.BUYER).exists()
        ):
            # TODO: return validation error with a unique code
            return Response(
                "Delivery address is required.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_total = cart.total
        min_purchase_value = region_settings.min_purchase_value

        if cart_total < min_purchase_value:
            # TODO: return validation error with a unique code
            return Response(
                f"Order must exceed {min_purchase_value} {CURRENT_CURRENCY_CODE}. This cart net "
                f"value is {cart_total}",
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.create(
            earliest_delivery_date=cart.earliest_delivery_date,
            buyer=request.user,
            status=Order.STATUSES.get_value("ordered"),
            region=request.region,
        )

        third_party_delivery = False

        order_items = []
        for cart_item in cart.items.all():
            order_item = OrderItem(
                product=cart_item.product,
                order=order,
                latest_delivery_date=cart_item.latest_delivery_date,
                quantity=cart_item.quantity,
                delivery_address=cart.delivery_address,
                delivery_option_id=cart_item.delivery_option.id,
            )
            order_item.product_snapshot = order_item.product.create_snapshot()
            order_items.append(order_item)

        order_items = OrderItem.objects.bulk_create(order_items)

        if settings.FEATURES["routes"]:
            for order_item in order_items:
                if (
                    order_item.product.third_party_delivery
                    and order_item.delivery_option_id == DeliveryOption.SELLER
                ):
                    third_party_delivery = True

                    self.send_task(
                        f"/jobs/create/{order_item.id}",
                        queue_name="routes",
                        http_method="POST",
                        schedule_time=30,
                        headers={"Region": request.region.slug},
                    )

        # WARNING: It's required. The changes should be stored in the DB before we run recalculate_items_delivery_fee method.
        # FIXME: It should not work like this.
        order.save()

        order = Order.objects.prefetch_related(
            "items__delivery_option",
            "items__product__container_type",
            "items__product__region__settings__logistics_company",
            "items__product__category",
            "items__product__seller__region__settings",
            "items__delivery_option",
            "items__product__regions",
            "buyer__region__settings",
            "items__order__region__settings",
            "region__settings",
        ).get(id=order.id)

        order.recalculate_items_delivery_fee()
        order.total_price = order.price_gross
        order.save()

        cart.delete()

        if not third_party_delivery:
            self.send_task(
                f"/documents/queue/{order.id}/all",
                queue_name="documents",
                http_method="POST",
                schedule_time=60,
                headers={"Region": request.region.slug},
            )
        else:
            logger.debug(f"Third party delivery. Order ID: {order.id}")

        return Response(OrderSerializer(order, context={"request": request}).data)

    def get(self, request, pk: int = None, format=None):
        queryset = (
            Cart.objects.filter(user=self.request.user)
            .order_by("-created_at")
            .select_related("user", "delivery_address")
            .prefetch_related(
                "items",
                "items__delivery_option",
                "items__product",
                "items__product__delivery_options",
                "user__region__settings",
            )
            .first()
        )
        serializer = CartSerializer(queryset, context={"request": request})
        return Response(serializer.data)
