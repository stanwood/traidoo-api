from documents import factories


def test_logistics_invoice(
    order,
    order_items,
    products,
    platform_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    logistics_user,
    buyer,
    seller,
):
    order.recalculate_items_delivery_fee()

    factory = factories.LogisticsInvoiceFactory(order, region=traidoo_region)
    document = factory.compose()
    document.save()

    assert document.seller == factories.LogisticsInvoiceFactory.as_dict(logistics_user)
    assert document.buyer == factories.LogisticsInvoiceFactory.as_company(buyer)
    assert document.order_id == order.id
    assert len(document.lines) == 1
    assert document.lines[0] == {
        "amount": 1.0,
        "count": 1,
        "name": f"Lieferung von {products[0].name}",
        "number": products[0].id,
        "price": 14.31,
        "producer": "Traidoo",
        "seller_user_id": logistics_user.id,
        "unit": "",
        "vat_rate": 19.0,
        "category": "",
    }


def test_logistics_invoice_for_other_region_logistics_company(
    order_with_neighbour_product,
    neighbour_region,
    delivery_address,
    buyer,
    other_region_product,
):
    order_with_neighbour_product.recalculate_items_delivery_fee()

    assert len(order_with_neighbour_product.sellers_regions) == 2

    factory = factories.LogisticsInvoiceFactory(
        order_with_neighbour_product, region=neighbour_region
    )
    document = factory.compose()
    document.save()

    assert document.seller == factories.LogisticsInvoiceFactory.as_dict(
        neighbour_region.setting.logistics_company
    )

    assert document.buyer == factories.LogisticsInvoiceFactory.as_company(buyer)
    assert document.order_id == order_with_neighbour_product.id
    assert len(document.lines) == 1
    assert document.lines[0] == {
        "amount": 1.0,
        "count": 1,
        "name": f"Lieferung von {other_region_product.name}",
        "number": other_region_product.id,
        "price": 63,
        "producer": neighbour_region.setting.logistics_company.company_name,
        "seller_user_id": neighbour_region.setting.logistics_company.id,
        "unit": "",
        "vat_rate": 19.0,
        "category": "",
    }
