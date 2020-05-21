from django.conf.urls import url

from .views import FeaturesView

urlpatterns = [url("features", FeaturesView.as_view())]
