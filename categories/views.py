import datetime

from django.db.models import Q
from django.db.models.deletion import ProtectedError
from loguru import logger
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from categories.models import Category
from categories.serializers import CategorySerializer
from core.errors.exceptions import ProtectedEntityException
from core.permissions.admin import IsAdminUser
from core.permissions.get_permissions import GetPermissionsMixin


class CategoryViewSet(GetPermissionsMixin, viewsets.ModelViewSet):

    permission_classes_by_action = {
        'create': [IsAdminUser],
        'update': [IsAdminUser],
        'partial_update': [IsAdminUser],
        'destroy': [IsAdminUser],
        'default': [AllowAny],
    }

    serializer_class = CategorySerializer
    pagination_class = None

    filterset_fields = search_fields = (
        'id',
        'created_at',
        'updated_at',
        'icon',
        'name',
        'default_vat',
    )

    ordering_fields = search_fields + ('ordering',)

    def get_queryset(self):
        if self.request.query_params.get('has_products', None) is None:
            queryset = Category.objects.all()
        else:
            queryset = (
                Category.objects.select_related()
                .filter(
                    (
                        Q(product__items__quantity__gte=1)
                        & Q(
                            product__items__latest_delivery_date__gt=datetime.datetime.utcnow().date()
                        )
                    )
                    | (
                        Q(subcategories__product__items__quantity__gte=1)
                        & Q(
                            subcategories__product__items__latest_delivery_date__gt=datetime.datetime.utcnow().date()
                        )
                    )
                    | (
                        Q(subcategories__subcategories__product__items__quantity__gte=1)
                        & Q(
                            subcategories__subcategories__product__items__latest_delivery_date__gt=datetime.datetime.utcnow().date()
                        )
                    )
                    | (
                        Q(
                            subcategories__subcategories__subcategories__product__items__quantity__gte=1
                        )
                        & Q(
                            subcategories__subcategories__subcategories__product__items__latest_delivery_date__gt=datetime.datetime.utcnow().date()
                        )
                    )
                )
                .distinct()
            )

        return queryset

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            raise ProtectedEntityException()
