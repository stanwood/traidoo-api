from decimal import Decimal
from typing import Dict

import requests
from loguru import logger
from requests import Session

from payments.client.exceptions import MangopayError, MangopayTransferError
from payments.utils import euro_to_cents, lookup_legal_person_type


class MangopayClient:
    def __init__(self, url, client_id, password):
        self._url = "{}/{}".format(url, client_id)
        self._client_id = client_id
        self._password = password

    def _make_request(self, url, method, payload=None, params=None):
        headers = {"Content-Type": "application/json"}

        logger.debug("{} {}".format(method, url))
        logger.debug(payload)

        request = requests.Request(
            url=url,
            headers=headers,
            method=method,
            json=payload,
            params=params,
            auth=(self._client_id, self._password),
        ).prepare()
        session = Session()
        response = session.send(request)

        logger.debug(request.url)

        logger.debug(response.text)
        if response.status_code > 399:
            logger.debug("{}\n{}".format(response.status_code, response.text))
            raise MangopayError(response.content)

        try:
            return response.json()
        except ValueError as value_error:
            logger.warning("Non json response: `{}`".format(response.text))
            return response.text

    def get(self, endpoint, params=None):
        if params is None:
            params = {}

        # TODO: fetch all available pages
        params["per_page"] = 100

        url = "{}{}".format(self._url, endpoint)

        return self._make_request(url, "GET", params=params)

    def post(self, endpoint, payload=None):
        if payload is None:
            payload = {}

        url = "{}{}".format(self._url, endpoint)

        return self._make_request(url, "post", payload=payload)

    def put(self, endpoint, payload=None):
        if payload is None:
            payload = {}

        url = "{}{}".format(self._url, endpoint)

        return self._make_request(url, "put", payload=payload)

    def delete(self, endpoint, params=None):
        if params is None:
            params = {}

        url = "{}{}".format(self._url, endpoint)

        return self._make_request(url, "DELETE", params=params)

    def wallet_transactions(self, wallet_id: str):
        page = 1
        while True:
            transactions = self.get(
                f"/wallets/{wallet_id}/transactions", {"page": page}
            )
            if not transactions:
                break
            page += 1

            for transaction in transactions:
                yield transaction

    def create_bank_account(
        self,
        user_id: str,
        street: str,
        city: str,
        zip: str,
        owner: str,
        iban: str,
        country: str = "DE",
    ):
        return self.post(
            f"/users/{user_id}/bankaccounts/iban",
            {
                "Tag": "Default",
                "OwnerAddress": {
                    "AddressLine1": street,
                    "City": city,
                    "PostalCode": zip,
                    "Country": country,
                },
                "OwnerName": owner,
                "IBAN": iban,
            },
        )

    def create_bank_payin(
        self,
        user_id: str,
        user_wallet_id: str,
        items_gross_price: float,
        platform_gross_fee: float,
        tag: str = "",
        currency_code: str = "EUR",
    ):
        return self.post(
            "/payins/bankwire/direct",
            {
                "Tag": tag,
                "AuthorId": user_id,
                "WalletId": user_wallet_id,
                "CreditedWalletId": user_wallet_id,
                "DeclaredDebitedFunds": {
                    "Currency": currency_code,
                    "Amount": euro_to_cents(items_gross_price),
                },
                "DeclaredFees": {
                    "Currency": currency_code,
                    "Amount": euro_to_cents(platform_gross_fee),
                },
            },
        )

    def transfer(
        self,
        user_id: str,
        source_wallet_id: str,
        destination_wallet_id: str,
        amount: float,
        fees: int = 0,
        tag: str = None,
        currency_code: str = "EUR",
    ):
        """
        Transfers money between mangopay wallets.
        :param user_id:
        :param source_wallet_id:
        :param destination_wallet_id:
        :param amount:
        :param fees:
        :param tag:
        :param currency_code:
        :raises MangopayTrasnferError
        :return: Response from `/transfers` mangopay api
        """
        transfer = self.post(
            "/transfers",
            {
                "AuthorId": user_id,
                "DebitedFunds": {
                    "Amount": euro_to_cents(amount),
                    "Currency": currency_code,
                },
                "Fees": {"Amount": euro_to_cents(fees), "Currency": currency_code},
                "DebitedWalletId": source_wallet_id,
                "CreditedWalletId": destination_wallet_id,
                "Tag": tag,
            },
        )

        if transfer["Status"] != "SUCCEEDED":
            logger.error(transfer)
            raise MangopayTransferError(transfer["ResultMessage"])

        return transfer

    def create_wallet(
        self, user_id: int, description: str = "Default", currency: str = "EUR"
    ) -> Dict:
        """
        Call Mangopay API to create a wallet for the user
        """
        return self.post(
            "/wallets",
            {"Owners": [user_id], "Description": description, "Currency": currency},
        )

    def get_wallet(self, wallet_id: str):
        return self.get(f"/wallets/{wallet_id}")

    def get_user_wallets(self, user_id: str):
        return self.get(f"/users/{user_id}/wallets")

    def create_banking_alias_iban(
        self, wallet_id: str, user_id: str, name: str, country: str = "FR"
    ):
        """
        Create banking alias IBAN for a wallet

        The only supported country code are FR and LU as of writing this
        docstring (2020-03-08).
        """
        return self.post(
            f"/wallets/{wallet_id}/bankingaliases/iban",
            {"CreditedUserId": user_id, "OwnerName": name, "Country": country},
        )

    def get_wallet_banking_alias(self, wallet_id: str):
        """
        The Mangopay API will return a list of banking aliases for given wallet
        but there will be only one alias maximum.
        """
        return self.get(f"/wallets/{wallet_id}/bankingaliases/")

    def get_banking_alias(self, baking_alias_id: str):
        return self.get(f"/bankingaliases/{baking_alias_id}")

    def get_bank_accounts(self, mangopay_user_id: str, active: bool = True):
        return self.get(
            f"/users/{mangopay_user_id}/bankaccounts", params={"Active": active}
        )

    def create_mangopay_natural_user(
        self,
        first_name: str,
        last_name: str,
        birthday: str,
        residence_country_code: str,
        nationality_country_code: str,
        email: str,
        street: str,
        city: str,
        zip: str,
    ):
        return self.post(
            "/users/natural",
            {
                "FirstName": first_name,
                "LastName": last_name,
                "Address": {
                    "AddressLine1": street,
                    "City": city,
                    "PostalCode": zip,
                    "Country": residence_country_code,
                },
                "Birthday": birthday,
                "Nationality": nationality_country_code,
                "CountryOfResidence": residence_country_code,
                "Email": email,
            },
        )

    def create_mangopay_legal_user(
        self,
        first_name: str,
        last_name: str,
        birthday: str,
        residence_country_code: str,
        nationality_country_code: str,
        email: str,
        company_name: str,
        company_type: str,
        street: str,
        city: str,
        zip: str,
        company_registration_id: str = None,
        currency_code: str = "DE",
    ):
        return self.post(
            "/users/legal",
            {
                "LegalPersonType": lookup_legal_person_type(company_type),
                "Name": company_name,
                "LegalRepresentativeBirthday": birthday,
                "LegalRepresentativeCountryOfResidence": residence_country_code,
                "LegalRepresentativeNationality": nationality_country_code,
                "Email": email,
                "LegalRepresentativeFirstName": first_name,
                "LegalRepresentativeLastName": last_name,
                "CompanyNumber": company_registration_id.replace(" ", "")
                if company_registration_id
                else company_registration_id,
                "HeadquartersAddress": {
                    "AddressLine1": street,
                    "City": city,
                    "PostalCode": zip,
                    "Country": currency_code,
                },
            },
        )

    def get_kyc_document(self, document_id: str):
        return self.get(f"/kyc/documents/{document_id}")

    def get_user(self, mangopay_user_id: str):
        return self.get(f"/users/{mangopay_user_id}")

    def get_user_kyc_documents(self, mangopay_user_id: str):
        return self.get(f"/users/{mangopay_user_id}/kyc/documents")

    def get_pay_in(self, pay_in_id: str):
        return self.get(f"/payins/{pay_in_id}")

    def get_pay_out(self, pay_out_id: str):
        return self.get(f"/payouts/{pay_out_id}")

    def create_pay_out(
        self,
        author_id: str,
        amount: int,
        bank_account_id: str,
        wallet_id: str,
        fees_amount: int = 0,
        fees_currency: str = "EUR",
        wire_reference: str = None,
    ):
        payload = {
            "AuthorId": author_id,
            "DebitedFunds": {"Amount": amount, "Currency": "EUR"},
            "Fees": {"Amount": fees_amount, "Currency": fees_currency},
            "BankAccountId": bank_account_id,
            "DebitedWalletId": wallet_id,
        }

        if wire_reference:
            payload["BankWireRef"] = wire_reference

        return self.post("/payouts/bankwire", payload)

    def create_kyc_document(self, user_mangopay_id: str, document_type: str):
        return self.post(
            f"/users/{user_mangopay_id}/kyc/documents/", {"Type": document_type},
        )

    def create_kyc_page(self, user_mangopay_id: str, kyc_doc_id: str, file: str):
        return self.post(
            f"/users/{user_mangopay_id}/kyc/documents/{kyc_doc_id}/pages/",
            {"File": file},
        )

    def submit_kyc_document(self, user_mangopay_id: str, kyc_doc_id: str):
        return self.put(
            f"/users/{user_mangopay_id}/kyc/documents/{kyc_doc_id}/",
            {"Status": "VALIDATION_ASKED"},
        )

    def update_legal_user(self, user_mangopay_id: str, payload: Dict):
        return self.put(f"/users/legal/{user_mangopay_id}", payload)

    def update_natural_user(self, user_mangopay_id: str, payload: Dict):
        return self.put(f"/users/natural/{user_mangopay_id}", payload)

    def create_pay_in(
        self,
        user_id: str,
        user_wallet: Dict,
        items_gross_price: float,
        platform_gross_fee: float,
        tag: str,
    ):
        return self.post(
            "/payins/bankwire/direct",
            {
                "Tag": tag,
                "AuthorId": user_id,
                "WalletId": user_wallet["Id"],
                "CreditedWalletId": user_wallet["Id"],
                "DeclaredDebitedFunds": {
                    "Currency": "EUR",
                    "Amount": euro_to_cents(items_gross_price),
                },
                "DeclaredFees": {
                    "Currency": "EUR",
                    "Amount": euro_to_cents(platform_gross_fee),
                },
            },
        )
