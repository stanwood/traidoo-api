from documents import factories
from payments.views import sufficient_wallet_balance_for_order


def test_calculation_without_buyer_platform_invoice(
    order, order_items, producer_invoice, logistics_invoice, platform_invoice, order_confirmation
):
    assert sufficient_wallet_balance_for_order(order.id, order.buyer.id, {"Balance": {"Amount": order_confirmation.price_gross_cents}}) is True


def test_calculation_with_buyer_platform_invoice(
    order, order_items, producer_invoice, logistics_invoice, platform_invoice, traidoo_region, buyer
):
    buyer.is_cooperative_member = False
    buyer.save()
    order_confirmation = factories.OrderConfirmationBuyerFactory(order, traidoo_region).compose()
    order_confirmation.save()
    buyer_platform_invoice = factories.BuyerPlatformInvoiceFactory(order, traidoo_region).compose()
    buyer_platform_invoice.save()
    assert sufficient_wallet_balance_for_order(
        order.id,
        buyer.id,
        {
            "Balance": {"Amount": 18088}  # this is value of unpaid invoices excluding buyer platform invoice
        }
    ) is False

    assert sufficient_wallet_balance_for_order(
        order.id,
        buyer.id,
        {
            "Balance": {"Amount": order_confirmation.price_gross_cents}
        }
    )
