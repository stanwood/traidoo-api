from django.conf.urls import url

from payments.views import MangopayWebhookHandler
from payments.crons.payouts import MangopayPayoutView

urlpatterns = [
    url("webhook", MangopayWebhookHandler.as_view(), name="webhook"),
    url(
        "cron/payouts/(?P<mangopay_user_id>.+)",
        MangopayPayoutView.as_view(),
        name="payouts-user",
    ),
]
