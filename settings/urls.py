from django.urls import path
from rest_framework import routers

from settings.views import GlobalSettingView, SettingViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"settings", SettingViewSet)

urlpatterns = [path(r"global_settings", GlobalSettingView.as_view()),] + router.urls
