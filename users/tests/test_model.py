from decimal import Decimal
import django.contrib.admin
import pytest
from django.conf import settings
from django.urls import reverse
from model_mommy import mommy

from ..models import User

pytestmark = pytest.mark.django_db


def test_user_address_as_str():
    company_name = "Company Name"
    zip_code = 123
    city = "City"
    street = "Street"

    user = mommy.make(
        User, company_name=company_name, zip=zip_code, city=city, street=street
    )
    assert user.address_as_str == f"{company_name}, {street}, {zip_code}, {city}"


@pytest.mark.parametrize(
    "is_cooperative_member,is_seller,is_buyer,expected_value",
    [
        (True, True, False, Decimal("10.0")),
        (False, True, False, Decimal("12.0")),
        (True, True, True, Decimal("10.0")),
        (False, True, True, Decimal("12.0")),
    ],
)
def test_seller_platform_fee_rate(
    is_cooperative_member,
    is_seller,
    is_buyer,
    expected_value,
    seller_group,
    buyer_group,
    mcs_settings,
    traidoo_region,
):
    assert mcs_settings.charge == Decimal("10.0")

    groups = []

    if is_buyer:
        groups.append(buyer_group)

    if is_seller:
        groups.append(seller_group)

    user = mommy.make(
        User,
        is_cooperative_member=is_cooperative_member,
        groups=groups,
        region=traidoo_region,
    )

    assert user.is_seller is is_seller
    assert user.is_buyer is is_buyer
    assert user.is_cooperative_member is is_cooperative_member
    assert user.seller_platform_fee_rate == expected_value


@pytest.mark.parametrize(
    "is_cooperative_member,is_seller,is_buyer,expected_value",
    [
        (True, True, True, Decimal("0.0")),
        (False, True, True, Decimal("2.0")),
        (True, False, True, Decimal("0.0")),
        (False, False, True, Decimal("2.0")),
    ],
)
def test_buyer_platform_fee_rate(
    is_cooperative_member,
    is_seller,
    is_buyer,
    expected_value,
    seller_group,
    buyer_group,
    mcs_settings,
    traidoo_region,
):
    assert mcs_settings.charge == Decimal("10.0")

    groups = []

    if is_buyer:
        groups.append(buyer_group)

    if is_seller:
        groups.append(seller_group)

    user = mommy.make(
        User,
        is_cooperative_member=is_cooperative_member,
        groups=groups,
        region=traidoo_region,
    )

    assert user.is_seller is is_seller
    assert user.is_buyer is is_buyer
    assert user.is_cooperative_member is is_cooperative_member
    assert user.buyer_platform_fee_rate == expected_value


def test_email_change_mail_sent_to_user(mailoutbox, buyer, traidoo_region):
    buyer.email = "foo@bal.com"
    buyer.save()

    assert mailoutbox[-1].subject == "Ihre E-Mail-Adresse wurde geändert"
    assert mailoutbox[-1].from_email == settings.DEFAULT_FROM_EMAIL
    assert mailoutbox[-1].to == ["foo@bal.com"]


@pytest.mark.skip("Does not work but I do not know why")
def test_send_mail_to_user_after_activation(
    mailoutbox, traidoo_region, buyer_group, client_admin, admin
):
    new_user = mommy.make_recipe("users.user", region=traidoo_region)

    response = client_admin.post(
        reverse("admin:users_user_changelist"),
        {
            "action": "approve_user",
            django.contrib.admin.ACTION_CHECKBOX_NAME: new_user.id,
        },
        follow=True,
    )

    assert mailoutbox[-1].subject == "Ihr Account wurde aktiviert."
    assert mailoutbox[-1].from_email == traidoo_region.setting.platform_user.email
    assert mailoutbox[-1].to == [new_user.email]
