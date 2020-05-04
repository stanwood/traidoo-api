from django.conf import settings
from loguru import logger
from rest_framework import serializers, status, views
from rest_framework.response import Response

from carts.models import Cart
from carts.utils import validate_earliest_delivery_date
from common.utils import get_region
from core.permissions.buyer_or_seller import IsBuyerOrSellerUser
from core.tasks.mixin import TasksMixin
from delivery_addresses.models import DeliveryAddress
from delivery_options.models import DeliveryOption
from documents import factories
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer
from settings.models import Setting

from .serializers import CartSerializer


class CheckoutView(TasksMixin, views.APIView):
    permission_classes = (IsBuyerOrSellerUser,)

    def post(self, request, format=None):
        region = get_region(request)
        region_settings = region.settings.first()

        try:
            cart = (
                Cart.objects.filter(user=self.request.user)
                .order_by("-created_at")
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
                "Delivery address is required.", status=status.HTTP_400_BAD_REQUEST,
            )

        cart_total = cart.total
        min_purchase_value = region_settings.min_purchase_value

        if cart_total < min_purchase_value:
            # TODO: return validation error with a unique code
            return Response(
                f"Order must exceed {min_purchase_value} EUR. This cart net "
                f"value is {cart_total}",
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.create(
            earliest_delivery_date=cart.earliest_delivery_date,
            buyer=request.user,
            status=Order.STATUSES.get_value("ordered"),
            region=region,
        )

        third_party_delivery = False

        for cart_item in cart.items.all():
            order_item = OrderItem.objects.create(
                product=cart_item.product,
                order=order,
                latest_delivery_date=cart_item.latest_delivery_date,
                quantity=cart_item.quantity,
                delivery_address=cart.delivery_address,
                delivery_option_id=cart_item.delivery_option.id,
            )

            if settings.FEATURES["routes"] and order_item.product.third_party_delivery:
                third_party_delivery = True

                self.send_task(
                    f"/jobs/create/{order_item.id}",
                    queue_name="routes",
                    http_method="POST",
                    schedule_time=30,
                    headers={"Region": region.slug},
                )

        # WARNING: It's required.
        # The changes should be stored in the DB before we run
        # recalculate_items_delivery_fee method.
        # FIXME: It should not work like this.
        order.save()

        order.recalculate_items_delivery_fee()

        order.total_price = order.price_gross
        order.save()

        cart.delete()

        if not (settings.FEATURES["routes"] and third_party_delivery):
            self.send_task(
                f"/documents/queue/{order.id}/all",
                queue_name="documents",
                http_method="POST",
                schedule_time=60,
                headers={"Region": region.slug},
            )
        else:
            logger.debug(f"Third party delivery. Order ID: {order.id}")

        return Response(OrderSerializer(order, context={"request": request}).data)

    def get(self, request, pk: int = None, format=None):
        queryset = (
            Cart.objects.filter(user=self.request.user).order_by("-created_at").first()
        )
        serializer = CartSerializer(queryset, context={"request": request})
        return Response(serializer.data)
