import csv
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand

from payments.client.client import MangopayClient

User = get_user_model()


class Command(BaseCommand):
    help = "Create banking aliases"

    @property
    def mangopay_client(self):
        return MangopayClient(
            settings.MANGOPAY_URL,
            settings.MANGOPAY_CLIENT_ID,
            settings.MANGOPAY_PASSWORD,
        )

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            if not user.mangopay_user_id:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Cannot proceed with user with ID: {user.id} because "
                        f"it does not have mangopay user ID"
                    )
                )
                continue

            # Get a wallet
            wallets = self.mangopay_client.get_user_wallets(
                user_id=user.mangopay_user_id
            )

            default_wallets = [
                wallet
                for wallet in wallets
                if (wallet["Currency"] == "EUR" and wallet["Description"] == "Default")
            ]

            if not default_wallets:
                self.stdout.write(
                    self.style.NOTICE(
                        f"No wallet with currency EUR for user with mangopay "
                        f"ID: {user.mangopay_user_id}"
                    )
                )
                continue

            wallet = default_wallets[0]

            # Get a banking alias
            wallet_id = wallet.get("Id")

            # List that contains only one item maximum
            banking_alias = self.mangopay_client.get_wallet_banking_alias(
                wallet_id=wallet_id
            )

            if banking_alias:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Baking alias IBAN already exists for user "
                        f"{user.mangopay_user_id} and wallet {wallet_id}"
                    )
                )
                continue

            # If alias does not exist then create one for the wallet
            self.mangopay_client.create_banking_alias_iban(
                wallet_id=wallet_id, user_id=user.mangopay_user_id
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Baking alias IBAN created for user "
                    f"{user.mangopay_user_id} and wallet {wallet_id}"
                )
            )
