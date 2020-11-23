from rest_framework import views
from rest_framework.response import Response
from carts.models import Cart
from core.permissions.buyer_or_seller import IsBuyerOrSellerUser


from ..serializers.delivery import CheckoutDeliverySerializer


class CheckoutDeliveryView(views.APIView):
    permission_classes = (IsBuyerOrSellerUser,)

    def get(self, request, pk: int = None, format=None):
        queryset = (
            Cart.objects.filter(user=self.request.user).order_by("-created_at").first()
        )
        serializer = CheckoutDeliverySerializer(queryset, context={"request": request})
        return Response(serializer.data)
