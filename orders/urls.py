from .crons.third_party_delivery_orders import ThirdPartyDeliveryOrdersView
from .tasks.recalculate_delivery_fee import RecalculateDeliveryFeeView

from django.urls import path


urlpatterns = [
    path(
        r'orders/crons/third-party-delivery-orders',
        ThirdPartyDeliveryOrdersView.as_view(),
    ),
    path(
        r'order-items/tasks/recalculate-delivery-fee',
        RecalculateDeliveryFeeView.as_view(),
    ),
]
