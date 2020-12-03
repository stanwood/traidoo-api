from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.request import Request

from items.models import Item
from items.serializers import ItemSerializer
from products.models import Product


class ItemView(views.APIView):
    def get(self, request: Request, product_id: int, format: str = None):
        queryset = Item.objects.filter(
            product__seller=self.request.user, product__id=product_id
        )
        return Response(ItemSerializer(queryset, many=True).data)

    def post(self, request: Request, product_id: int, format: str = None):
        try:
            Product.objects.filter(id=product_id, seller=request.user).exists()
        except Item.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        request.data.update({"product": product_id})

        serializer = ItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(
        self, request: Request, product_id: int, item_id: int, format: str = None
    ):
        try:
            item = Item.objects.get(
                id=item_id, product__id=product_id, product__seller=request.user
            )
        except Item.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ItemSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(
        self, request: Request, product_id: int, item_id: int, format: str = None
    ):
        try:
            item = Item.objects.get(
                id=item_id, product__id=product_id, product__seller=request.user
            )
        except Item.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            item.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
