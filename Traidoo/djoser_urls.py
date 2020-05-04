from django.conf.urls import include, url
from django.contrib.auth import get_user_model
from djoser import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as rfs_views

from users.views.auth.password_reset_confirm import PasswordResetConfirmView
from users.views.email import UserEmailView
from users.views.login import CustomTokenObtainPairView
from users.views.resend_activation_email import ResendActivationView
from users.views.auth.password_reset import PasswordResetView

router = DefaultRouter(trailing_slash=False)

router.register("users", views.UserViewSet)

User = get_user_model()

urlpatterns_djoser = [
    url(r"^me/?$", views.UserView.as_view(), name="user"),
    url(r"^delete/?$", views.UserDeleteView.as_view(), name="user-delete"),
    url(r"^verify_email/?$", views.ActivationView.as_view(), name="user-activate"),
    url(
        r"^resend_email_verify/?$",
        ResendActivationView.as_view(),
        name="resend-activation",
    ),
    url(r"^password/?$", views.SetPasswordView.as_view(), name="set_password"),
    url(r"^password_reset/?$", PasswordResetView.as_view(), name="password_reset"),
    url(
        r"^set_password/?$",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    url(r"^email", UserEmailView.as_view()),
    url(r"^$", views.RootView.as_view(), name="root"),
    url(r"^", include(router.urls)),
]

urlpatterns_jwt = [
    url(r"^login/?", CustomTokenObtainPairView.as_view(), name="jwt-create"),
    url(r"^jwt/refresh/?", rfs_views.TokenRefreshView.as_view(), name="jwt-refresh"),
]
