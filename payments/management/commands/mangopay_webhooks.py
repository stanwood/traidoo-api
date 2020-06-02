import json

from django.core.management import BaseCommand

from payments.mixins import MangopayMixin


class Command(MangopayMixin, BaseCommand):
    EVENT_TYPES = [
        "PAYIN_NORMAL_CREATED",
        "PAYIN_NORMAL_SUCCEEDED",
        "PAYIN_NORMAL_FAILED",
        "PAYOUT_NORMAL_SUCCEEDED",
        "PAYOUT_NORMAL_FAILED",
        "KYC_SUCCEEDED",
        "KYC_FAILED",
    ]

    help = "Sets mangopay webhooks handlers"

    def add_arguments(self, parser):
        parser.add_argument("handler_url", type=str)

    def handle(self, *args, **options):
        new_hook = options["handler_url"]
        hooks = self.mangopay.get("/hooks")
        if not hooks:
            for event_type in self.EVENT_TYPES:
                hook = self.mangopay.post(
                    "/hooks/", {"eventType": event_type, "url": new_hook}
                )
                self.stdout.write(json.dumps(hook))
        else:
            for hook in hooks:
                self.stdout.write(json.dumps(hook))
                result = self.mangopay.put(
                    "/hooks/{}".format(hook["Id"]), {"Url": new_hook},
                )
                self.stdout.write(json.dumps(result))
