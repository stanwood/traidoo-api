from .views import ItemView
from django.urls import path

urlpatterns = [
    path("items/<int:product_id>", ItemView.as_view()),
    path("items/<int:product_id>/<int:item_id>", ItemView.as_view()),
]
