from django.urls import path

from .views.cart import (
    CartDevelieryAddressView,
    CartDevelieryView,
    CartItemDevelieryOptionView,
    CartView,
)

urlpatterns = [
    path("cart", CartView.as_view()),
    path("cart/delivery", CartDevelieryView.as_view()),
    path("cart/deliveryAddress", CartDevelieryAddressView.as_view()),
    path("cart/<int:pk>/delivery_option", CartItemDevelieryOptionView.as_view()),
    path("cart/<int:pk>", CartView.as_view()),
]
