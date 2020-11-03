from django.urls import path

from settings.views import GlobalSettingView, SettingView

urlpatterns = [
    path(r"global_settings", GlobalSettingView.as_view()),
    path(r"settings", SettingView.as_view()),
]
