from documents import factories


def test_order_confirmation_buyer(
    order,
    order_items,
    products,
    central_platform_user,
    logistics_user,
    container_types,
    traidoo_region,
    delivery_address,
    delivery_options,
    traidoo_settings,
    buyer,
):

    buyer.is_cooperative_member = False
    buyer.save()

    order.recalculate_items_delivery_fee()
    factory = factories.OrderConfirmationBuyerFactory(order, region=traidoo_region)
    document = factory.compose()
    document.save()

    assert document.seller == factories.OrderConfirmationBuyerFactory.as_dict(
        traidoo_region.setting.platform_user
    )

    assert document.buyer == factories.OrderConfirmationBuyerFactory.as_company(buyer)
    assert len(document.lines) == 6
    assert document.order_id == order.id
    assert document.lines[0] == {
        "amount": 3.0,
        "category": "Produkte",
        "count": 3,
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": products[0].seller.organic_control_body,
        "price": 10.6,
        "producer": products[0].seller.company_name,
        "seller_user_id": products[0].seller.id,
        "unit": products[0].unit,
        "vat_rate": 19.0,
    }
    assert document.lines[1] == {
        "amount": 1.0,
        "category": "Produkte",
        "count": 2,
        "name": products[1].name,
        "number": products[1].id,
        "organic_control_body": products[1].seller.organic_control_body,
        "price": 20.3,
        "producer": products[1].seller.company_name,
        "seller_user_id": products[1].seller.id,
        "unit": products[1].unit,
        "vat_rate": 19,
    }
    assert document.lines[2] == {
        "amount": 1.0,
        "category": "Pfand",
        "count": 5.0,
        "name": "Isolierbox",
        "number": container_types[0].id,
        "price": 3.2,
        "producer": "",
        "seller_user_id": products[0].seller.id,
        "unit": "Stück",
        "vat_rate": 19.0,
    }
    assert document.lines[3] == {
        "amount": 1.0,
        "category": "Logistik",
        "count": 1,
        "name": f"Lieferung von {products[0].name}",
        "number": products[0].id,
        "price": 14.31,
        "producer": logistics_user.company_name,
        "seller_user_id": logistics_user.id,
        "unit": "",
        "vat_rate": 19.0,
    }
    assert document.lines[4] == {
        "amount": 1.0,
        "category": "Logistik",
        "count": 1,
        "name": f"Lieferung von {products[1].name}",
        "number": products[1].id,
        "price": 12,
        "producer": products[1].seller.company_name,
        "seller_user_id": products[1].seller.id,
        "unit": "",
        "vat_rate": traidoo_settings.mc_swiss_delivery_fee_vat,
    }
    assert document.lines[5] == {
        "amount": 1.0,
        "category": "Plattform",
        "count": 1,
        "name": "Plattformgebühr",
        "number": "",
        "price": 2.72,
        "producer": central_platform_user.company_name,
        "seller_user_id": central_platform_user.id,
        "unit": "",
        "vat_rate": 19.0,
    }


def test_order_confirmation_with_products_delivered_by_neighbouring_region_logistics(
    order_with_neighbour_product, traidoo_region, other_region_product
):

    order_with_neighbour_product.recalculate_items_delivery_fee()
    factory = factories.OrderConfirmationBuyerFactory(
        order_with_neighbour_product, region=traidoo_region
    )
    document = factory.compose()
    document.save()
    assert document.lines[6]["category"] == "Logistik"
    assert document.lines[6]["name"] == f"Lieferung von {other_region_product.name}"
    assert (
        document.lines[6]["producer"]
        == other_region_product.region.setting.logistics_company.company_name
    )
