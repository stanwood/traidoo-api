from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.request import Request

from core.permissions.owner import IsOwner
from items.models import Item
from items.serializers import ItemSerializer


class ItemView(views.APIView):
    OWNER_FIELD = "product.seller"

    permission_classes = (IsOwner,)

    def get(self, request: Request, product_id: int, format: str = None):
        queryset = Item.objects.filter(
            product__seller=self.request.user, product__id=product_id
        )
        return Response(ItemSerializer(queryset, many=True).data)

    def post(self, request: Request, product_id: int, format: str = None):
        request.data.update({"product": product_id})

        serializer = ItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(
        self, request: Request, product_id: int, item_id: int, format: str = None
    ):
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
