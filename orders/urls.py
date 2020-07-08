from django.urls import path
from rest_framework import routers

from .crons.third_party_delivery_orders import ThirdPartyDeliveryOrdersView
from .tasks.recalculate_delivery_fee import RecalculateDeliveryFeeView
from .views.purchases import PurchasesViewSet
from .views.sales import SalesViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"orders/purchases", PurchasesViewSet, basename="purchases")
router.register(r"orders/sales", SalesViewSet, basename="sales")


urlpatterns = [
    path(
        "orders/crons/third-party-delivery-orders",
        ThirdPartyDeliveryOrdersView.as_view(),
    ),
    path(
        "order-items/tasks/recalculate-delivery-fee",
        RecalculateDeliveryFeeView.as_view(),
    ),
] + router.urls
