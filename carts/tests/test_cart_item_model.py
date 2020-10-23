import pytest

pytestmark = pytest.mark.django_db()


def test_item_price(cart, buyer, traidoo_settings):
    cart_item = cart.items.first()
    buyer.is_cooperative_member = False
    buyer.save()
    assert cart_item.price.netto == 180
    assert cart_item.platform_fee_net == 3.6
    assert cart_item.container_deposit.netto == 3.2
