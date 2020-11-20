from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from carts.models import Cart, CartItem
from core.permissions.buyer_or_seller import IsBuyerOrSellerUser

from ..serializers import CartItemDeliveryOptionPostSerializer


class DevelieryOptionBulkUpdateView(APIView):
    permission_classes = [IsBuyerOrSellerUser]

    def post(self, request: Request, pk: int = None, format: str = None):
        serializer = CartItemDeliveryOptionPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cart = Cart.objects.get(user=self.request.user)
        except Cart.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        CartItem.objects.filter(
            cart=cart,
            product__delivery_options__in=[
                serializer.validated_data["delivery_option"]
            ],
        ).update(delivery_option_id=serializer.validated_data["delivery_option"])

        return Response(status=status.HTTP_204_NO_CONTENT)
