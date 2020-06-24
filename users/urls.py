from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from users.views.auth.password_reset import PasswordResetView
from users.views.auth.password_set import PasswordSetView
from users.views.auth.password_update import PasswordUpdateView
from users.views.auth.resend_email_verification import ResendEmailVerificationView
from users.views.auth.token import CustomTokenObtainPairView
from users.views.auth.verify_email import VerifyEmailView

urlpatterns = [
    path("verify-email", VerifyEmailView.as_view(), name="user-verify-email",),
    path(
        "verify-email/resend",
        ResendEmailVerificationView.as_view(),
        name="user-resend-verification-email",
    ),
    path("password-set", PasswordSetView.as_view(), name="user-password-set",),
    path("password-reset", PasswordResetView.as_view(), name="user-password-reset",),
    path("password", PasswordUpdateView.as_view(), name="user-password",),
    path("token", CustomTokenObtainPairView.as_view(), name="user-token",),
    path("token/refresh", TokenRefreshView.as_view(), name="user-token-refresh"),
]
