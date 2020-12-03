from .views.checkout import CheckoutView
from .views.delivery import CheckoutDeliveryView
from django.urls import path

urlpatterns = [
    path("checkout", CheckoutView.as_view()),
    path("checkout/delivery", CheckoutDeliveryView.as_view()),
]
