import base64
from decimal import Decimal
from typing import Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from loguru import logger

from core import utils
from payments.client.client import MangopayClient
from payments.utils import lookup_legal_person_type, lookup_user_type

User = get_user_model()


class MangopayMixin:
    @property
    def mangopay(self):
        return MangopayClient(
            settings.MANGOPAY_URL,
            settings.MANGOPAY_CLIENT_ID,
            settings.MANGOPAY_PASSWORD,
        )

    def update_legal_user(self, mangopay_user_id: str, **kwargs):
        address = {
            "AddressLine1": kwargs.get("street"),
            "City": kwargs.get("city"),
            "PostalCode": kwargs.get("zip"),
        }
        address = {key: value for key, value in address.items() if value}
        if address:
            address["Country"] = "DE"

        try:
            company_number = kwargs.get("company_registration_id").replace(" ", "")
        except AttributeError:
            company_number = None

        try:
            birthday_timestamp = int(kwargs.get("birthday"))
            birthday_timestamp = int(birthday_timestamp / 1000)
        except TypeError:
            birthday_timestamp = None

        payload = {
            "Name": kwargs.get("company_name"),
            "LegalRepresentativeFirstName": kwargs.get("first_name"),
            "LegalRepresentativeLastName": kwargs.get("last_name"),
            "LegalRepresentativeBirthday": birthday_timestamp,
            "LegalRepresentativeCountryOfResidence": kwargs.get(
                "residence_country_code"
            ),
            "LegalRepresentativeNationality": kwargs.get("nationality_country_code"),
            "CompanyNumber": company_number,
            "LegalPersonType": lookup_legal_person_type(kwargs["company_type"])
            if kwargs.get("company_type")
            else None,
        }

        if address:
            payload["HeadquartersAddress"] = address

        payload = {key: value for key, value in payload.iteritems() if value}

        if payload:
            self.mangopay.update_legal_user(mangopay_user_id, payload)

    def update_natural_user(self, mangopay_user_id: str, **kwargs):
        address = {
            "AddressLine1": kwargs.get("street"),
            "City": kwargs.get("city"),
            "PostalCode": kwargs.get("zip"),
        }
        address = {key: value for key, value in address.iteritems() if value}

        if address:
            address["Country"] = "DE"

        try:
            birthday_timestamp = int(kwargs.get("birthday"))
            birthday_timestamp = int(birthday_timestamp / 1000)
        except TypeError:
            birthday_timestamp = None

        payload = {
            "FirstName": kwargs.get("first_name"),
            "LastName": kwargs.get("last_name"),
            "Birthday": birthday_timestamp,
            "Nationality": kwargs.get("nationality_country_code"),
            "CountryOfResidence": kwargs.get("residence_country_code"),
        }

        if address:
            payload["Address"] = address

        payload = {key: value for key, value in payload.items() if value}

        if payload:
            self.mangopay.update_natural_user(mangopay_user_id, payload)

    def get_user_wallet(self, user_id: str, currency_code: str = "EUR"):
        wallets = self.mangopay.get_user_wallets(user_id)

        default_wallets = [
            wallet
            for wallet in wallets
            if (
                wallet["Currency"] == currency_code
                and wallet["Description"] == "Default"
            )
        ]

        if default_wallets:
            return default_wallets[0]

        logger.info(f"User {user_id} has no {currency_code} wallet yet. Creating.")
        return self.mangopay.create_wallet(user_id)

    def get_user_bank_account(self, mangopay_user_id: str):
        active_accounts = self.mangopay.get_bank_accounts(mangopay_user_id)
        return active_accounts[0] if active_accounts else None

    @staticmethod
    def mangopay_fees(order_value):
        fees = 0.005 * order_value * 1.19
        fees = Decimal(str(fees))
        fees = fees.quantize(Decimal(".01"), "ROUND_HALF_UP")
        return float(fees)

    def create_mangopay_account_for_user(self, user: User) -> None:
        if lookup_user_type(user.company_type) == "natural":
            mangopay_user = self.mangopay.create_mangopay_natural_user(
                first_name=user.first_name,
                last_name=user.last_name,
                birthday=utils.to_timestamp(user.birthday) / 1000,
                residence_country_code=user.residence_country_code.code,
                nationality_country_code=user.nationality_country_code.code,
                email=user.email,
                street=user.street,
                city=user.city,
                zip=user.zip,
            )
            user.mangopay_user_type = "natural"
        else:
            mangopay_user = self.mangopay.create_mangopay_legal_user(
                first_name=user.first_name,
                last_name=user.last_name,
                birthday=utils.to_timestamp(user.birthday) / 1000,
                residence_country_code=user.residence_country_code.code,
                nationality_country_code=user.nationality_country_code.code,
                email=user.email,
                company_name=user.company_name,
                company_type=user.company_type,
                street=user.street,
                city=user.city,
                zip=user.zip,
                company_registration_id=user.company_registration_id,
            )
            user.mangopay_user_type = "legal"

        user.mangopay_user_id = mangopay_user["Id"]
        user.save()

    def get_wallet_banking_alias(self, wallet_id: str) -> Dict:
        # Will always return a list but with maximum one item on it
        response = self.mangopay.get_wallet_banking_alias(wallet_id=wallet_id)

        if not response:
            return {}

        return {
            "iban": response[0]["IBAN"],
            "bic": response[0]["BIC"],
            "id": response[0]["Id"],
            "owner_name": response[0]["OwnerName"],
        }

    def create_bank_pay_in(
        self,
        user_id: str,
        items_gross_price: int,
        platform_gross_fee: int,
        tag: str = "",
    ):
        user_wallet = self.get_user_wallet(user_id)
        return self.mangopay.create_pay_in(
            user_id, user_wallet, items_gross_price, platform_gross_fee, tag
        )

    def upload_kyc_document(
        self, mangopay_user_id: str, document_type: str, file_content
    ) -> None:
        response = self.mangopay.create_kyc_document(
            user_mangopay_id=mangopay_user_id, document_type=document_type,
        )

        kyc_doc_id = response["Id"]

        self.mangopay.create_kyc_page(
            user_mangopay_id=mangopay_user_id, kyc_doc_id=kyc_doc_id, file=file_content,
        )

        self.mangopay.submit_kyc_document(
            user_mangopay_id=mangopay_user_id, kyc_doc_id=kyc_doc_id
        )
