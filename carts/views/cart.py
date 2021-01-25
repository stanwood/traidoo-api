import datetime

from django.db.models import F, Sum, Window, OuterRef, Value, Subquery, Q
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.models import Cart, CartItem
from core.permissions.buyer_or_seller import IsBuyerOrSellerUser
from delivery_addresses.models import DeliveryAddress
from items.models import Item
from products.models import Product

from ..serializers import (
    CartDeliveryAddressPostSerializer,
    CartDeliveryDatePostSerializer,
    CartItemDeliveryOptionPostSerializer,
    CartPostSerializer,
)


class CartView(APIView):
    permission_classes = [IsBuyerOrSellerUser]

    def _add(self, cart: Cart, product: Product, quantity: int):
        for product_item in product.items.filter(
            quantity__gt=0, latest_delivery_date__gt=datetime.datetime.utcnow().date()
        ).order_by("latest_delivery_date"):
            item_quantity = (
                quantity if quantity <= product_item.quantity else product_item.quantity
            )

            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                latest_delivery_date=product_item.latest_delivery_date,
                defaults={
                    "quantity": item_quantity,
                    "delivery_option": product.first_available_delivery_option(),
                },
            )

            if not created:
                cart_item.quantity += item_quantity
                cart_item.save()

            product_item.quantity -= item_quantity

            if product_item.quantity == 0:
                product_item.delete()
            else:
                product_item.save()

            quantity -= item_quantity

            if quantity == 0:
                break

        # TODO: bulk save?

        return quantity

    def _remove(self, cart: Cart, product: Product, quantity: int):
        cart_items = CartItem.objects.filter(cart=cart, product=product).order_by(
            "-latest_delivery_date"
        )

        for cart_item in cart_items:
            quantity_to_release = (
                quantity if cart_item.quantity >= quantity else cart_item.quantity
            )

            product_item, created = Item.objects.get_or_create(
                product=product,
                latest_delivery_date=cart_item.latest_delivery_date,
                defaults={"quantity": quantity_to_release},
            )

            if not created:
                product_item.quantity += quantity_to_release
                product_item.save()

            quantity -= quantity_to_release
            cart_item.quantity -= quantity_to_release

            if cart_item.quantity == 0:
                cart_item.delete()
            else:
                cart_item.save()

            if quantity == 0:
                break

        return quantity

    def get(self, request: Request, format: str = None):
        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        utcnow = datetime.datetime.utcnow().date()

        subquery_items = (
            Item.objects.filter(product_id=OuterRef("product_id"))
            .order_by()
            .values("product")
        )
        subquery_quantity = subquery_items.annotate(
            total=Coalesce(
                Sum("quantity", filter=Q(latest_delivery_date__gt=utcnow)), Value(0)
            )
        ).values("total")

        items = (
            cart.items.annotate(
                total_quantity=Window(
                    partition_by=[F("product")],
                    expression=Sum("quantity"),
                )
            )
            .annotate(items_available=Subquery(subquery_quantity))
            .order_by("product", "created_at")
            .distinct("product")
        )

        response = {
            "products": [
                {
                    "id": item.product.id,
                    "name": item.product.name,
                    "price": item.product.price,
                    "unit": item.product.unit,
                    "amount": item.product.amount,
                    "quantity": item.total_quantity,
                    "max_quantity": item.items_available,
                }
                for item in items
            ],
        }

        return Response(response)

    def post(self, request: Request, format: str = None):
        serializer = CartPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = Product.objects.get(id=serializer.validated_data["product_id"])
        cart, _ = Cart.objects.get_or_create(
            user=self.request.user,
            defaults={
                "earliest_delivery_date": (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).date()
            },
        )
        cart_items_quantity = CartItem.objects.filter(
            cart=cart, product=product
        ).aggregate(sum=Coalesce(Sum("quantity"), 0))["sum"]

        if cart_items_quantity > serializer.validated_data["quantity"]:
            self._remove(
                cart,
                product,
                cart_items_quantity - serializer.validated_data["quantity"],
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        if cart_items_quantity < serializer.validated_data["quantity"]:
            return Response(
                {
                    "notAvailable": self._add(
                        cart,
                        product,
                        serializer.validated_data["quantity"] - cart_items_quantity,
                    )
                }
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, pk: int = None, format: str = None):
        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if pk:
            product = Product.objects.get(id=pk)
            cart_items = CartItem.objects.filter(cart=cart, product=product)
        else:
            cart_items = CartItem.objects.filter(cart=cart)

        for cart_item in cart_items:
            product_item, created = Item.objects.get_or_create(
                product=cart_item.product,
                latest_delivery_date=cart_item.latest_delivery_date,
                defaults={"quantity": cart_item.quantity},
            )

            if not created:
                product_item.quantity += cart_item.quantity
                product_item.save()

        cart_items.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartDevelieryView(APIView):
    permission_classes = [IsBuyerOrSellerUser]

    def post(self, request: Request, format: str = None):
        serializer = CartDeliveryDatePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        cart.earliest_delivery_date = serializer.validated_data["date"]
        cart.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartDevelieryAddressView(APIView):
    permission_classes = [IsBuyerOrSellerUser]

    def post(self, request: Request, format: str = None):
        serializer = CartDeliveryAddressPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: return a different code when the user does not exist and the address does not exist

        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            delivery_address = DeliveryAddress.objects.get(
                id=serializer.validated_data["delivery_address"]
            )
        except DeliveryAddress.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        cart.delivery_address = delivery_address
        cart.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemDevelieryOptionView(APIView):
    permission_classes = [IsBuyerOrSellerUser]

    def post(self, request: Request, pk: int, format: str = None):
        serializer = CartItemDeliveryOptionPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            product = Product.objects.get(id=pk)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        CartItem.objects.filter(cart=cart, product=product).update(
            delivery_option_id=serializer.validated_data["delivery_option"]
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
