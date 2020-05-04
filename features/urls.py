from django.urls import path
from django.conf.urls import include, url

from .views import FeaturesView

urlpatterns = [url('features', FeaturesView.as_view())]
