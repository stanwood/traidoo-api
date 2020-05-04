from django_filters import rest_framework as django_filters
from rest_framework import filters, viewsets

from core.permissions.seller import IsSellerOrAdminUser
from core.permissions.buyer import IsBuyerUser
from orders.models import OrderItem
from orders.serializers import OrderItemSerializer
from django.db.models import Sum, Q


class OrderItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderItemSerializer
    http_method_names = ['get']
    permission_classes = (IsSellerOrAdminUser | IsBuyerUser,)

    filter_backends = (
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )

    filterset_fields = {
        'order__status': ['exact', 'gt', 'gte', 'lt', 'lte', 'contains'],
        'latest_delivery_date': ['gt', 'gte', 'lt', 'lte', 'contains'],
    }

    ordering_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_queryset(self):

        queryset = OrderItem.objects.select_related('product')

        if self.kwargs.get('order_pk'):
            queryset = queryset.filter(order=self.kwargs['order_pk'])

        if not self.request.user.is_admin:
            queryset = queryset.filter(order__buyer=self.request.user)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # FIXME: this is wrong
        if self.kwargs.get('order_pk'):
            merged_proudcts_dict = {}

            for item in response.data['results']:
                if not merged_proudcts_dict.get(item['product']['id']):
                    merged_proudcts_dict[item['product']['id']] = item
                else:
                    merged_proudcts_dict[item['product']['id']]['quantity'] += item[
                        'quantity'
                    ]

            response.data['results'] = merged_proudcts_dict.values()
        return response
