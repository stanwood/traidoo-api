from documents import factories


def test_create_platform_invoice_not_cooperative_member(
    order,
    order_items,
    central_platform_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    seller,
):
    seller.is_cooperative_member = False
    seller.save()
    order.recalculate_items_delivery_fee()
    document = factories.PlatformInvoiceFactory(
        order, region=traidoo_region, seller=seller
    ).compose()
    document.save()

    assert document.seller == factories.PlatformInvoiceFactory.as_dict(
        central_platform_user
    )

    assert document.buyer == factories.PlatformInvoiceFactory.as_company(seller)
    assert document.order_id == order.id
    assert len(document.lines) == 1
    assert document.lines[0] == {
        "amount": 1.0,
        "category": "",
        "count": 1.0,
        "name": "Plattformgebühr",
        "number": "",
        "price": 16.32,
        "producer": "Traidoo",
        "seller_user_id": central_platform_user.id,
        "unit": "",
        "vat_rate": 19.0,
    }


def test_create_platform_invoice_cooperative_member(
    order,
    order_items,
    central_platform_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    seller,
):
    assert seller.is_cooperative_member

    document = factories.PlatformInvoiceFactory(
        order, region=traidoo_region, seller=seller
    ).compose()

    document.save()

    assert document.seller == factories.PlatformInvoiceFactory.as_dict(
        central_platform_user
    )

    assert document.buyer == factories.PlatformInvoiceFactory.as_company(seller)
    assert document.order_id == order.id
    assert len(document.lines) == 1
    assert document.lines[0] == {
        "amount": 1.0,
        "category": "",
        "count": 1.0,
        "name": "Plattformgebühr",
        "number": "",
        "price": 13.6,
        "producer": "Traidoo",
        "seller_user_id": central_platform_user.id,
        "unit": "",
        "vat_rate": 19.0,
    }


def test_include_paid_notice_in_seller_platform_invoice(
    order, traidoo_region, seller, order_items
):
    document = (
        factories.PlatformInvoiceFactory(order, region=traidoo_region, seller=seller)
        .compose()
        .render_html()
    )

    assert "Diese Rechnung ist bereits bezahlt" in document
