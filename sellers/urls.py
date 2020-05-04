from django.urls import path

from sellers.views import SellerViewSet

urlpatterns = [path("<int:pk>", SellerViewSet.as_view(), name="seller")]
