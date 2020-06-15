from django.conf.urls import url
from django.urls import path

from payments.crons.payouts import MangopayPayoutView
from payments.tasks.create_banking_alias_iban import CreateBankingAliasIbanView
from payments.tasks.create_wallet import CreateWalletView
from payments.views import MangopayWebhookHandler

tasks = [
    path(
        r"tasks/create-wallet",
        CreateWalletView.as_view(),
        name="mangopay-create-wallet",
    ),
    path(
        r"tasks/create-banking-alias-iban",
        CreateBankingAliasIbanView.as_view(),
        name="mangopay-create-banking-alias-iban",
    ),
]

urlpatterns = [
    url("webhook", MangopayWebhookHandler.as_view(), name="webhook"),
    url(
        "cron/payouts/(?P<mangopay_user_id>.+)",
        MangopayPayoutView.as_view(),
        name="payouts-user",
    ),
] + tasks
