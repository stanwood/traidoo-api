from model_bakery import baker

from documents import factories


def test_create_delivery_overview_buyer(
    order,
    buyer,
    order_items,
    logistics_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    traidoo_settings,
    products,
):
    order.recalculate_items_delivery_fee()
    factory = factories.DeliveryOverviewBuyerFactory(order, region=buyer.region)
    document = factory.compose()
    document.save()

    assert document.seller == factories.DeliveryOverviewBuyerFactory.as_dict(
        buyer.region.setting.logistics_company
    )
    assert document.buyer == factories.DeliveryOverviewBuyerFactory.as_company(buyer)

    assert document.order_id == order.id
    assert len(document.lines) == 2
    assert document.lines[0] == {
        "amount": 3.0,
        "container_name": "Isolierbox",
        "count": 3,
        "delivery_company": products[0].region.setting.logistics_company.company_name,
        "delivery_date": order_items[0].delivery_date.strftime("%d.%m.%Y"),
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": products[0].seller.organic_control_body,
        "price": 15.81,  # this needs to be net value
        "producer": buyer.region.setting.logistics_company.company_name,
        "unit": products[0].unit,
        "vat_rate": 19.0,
        "pickup_address": products[0].seller.address_as_str,
        "delivery_address": order_items[0].delivery_address.as_str(),
    }
    assert document.lines[1] == {
        "amount": 1.0,
        "container_name": "Isolierbox",
        "count": 2,
        "delivery_company": products[1].seller.company_name,
        "delivery_date": order_items[1].delivery_date.strftime("%d.%m.%Y"),
        "name": products[1].name,
        "number": products[1].id,
        "organic_control_body": products[1].seller.organic_control_body,
        "price": 12,  # this must be net value
        "producer": buyer.region.setting.logistics_company.company_name,
        "unit": products[1].unit,
        "vat_rate": 19.0,
        "delivery_address": order_items[0].delivery_address.as_str(),
        "pickup_address": products[1].seller.address_as_str,
    }


def test_create_delivery_overview_buyer_with_3rd_party_delivery(
    send_task,
    order,
    traidoo_region,
    order_items,
    delivery_address,
    delivery_options,
    logistics_user,
    buyer,
    products,
    settings,
):
    settings.FEATURES["routes"] = True

    products[1].third_party_delivery = True
    products[1].save()

    order.recalculate_items_delivery_fee()

    supplier = baker.make_recipe("users.user", email="supplier@example.com")
    baker.make("jobs.Job", order_item=order_items[1], user=supplier)

    factory = factories.DeliveryOverviewBuyerFactory(order, region=traidoo_region)
    document = factory.compose()
    document.save()

    assert document.seller["company_name"] == "Traidoo"

    assert document.seller == factories.DeliveryOverviewBuyerFactory.as_dict(
        logistics_user
    )

    assert document.buyer == factories.DeliveryOverviewBuyerFactory.as_company(buyer)

    order_items[0].refresh_from_db()
    order_items[1].refresh_from_db()

    assert document.order_id == order.id
    assert len(document.lines) == 2
    assert document.lines[0] == {
        "amount": 3.0,
        "container_name": "Isolierbox",
        "count": 3,
        "delivery_company": products[0].region.setting.logistics_company.company_name,
        "delivery_date": order_items[0].delivery_date.strftime("%d.%m.%Y"),
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": products[0].seller.organic_control_body,
        "price": 15.81,
        "producer": buyer.region.setting.logistics_company.company_name,
        "unit": products[0].unit,
        "vat_rate": 19.0,
        "pickup_address": products[0].seller.address_as_str,
        "delivery_address": order_items[0].delivery_address.as_str(),
    }
    assert document.lines[1] == {
        "amount": 1.0,
        "container_name": "Isolierbox",
        "count": 2,
        "delivery_company": supplier.company_name,
        "delivery_date": order_items[1].delivery_date.strftime("%d.%m.%Y"),
        "name": products[1].name,
        "number": products[1].id,
        "organic_control_body": products[1].seller.organic_control_body,
        "price": 12,
        "producer": buyer.region.setting.logistics_company.company_name,
        "unit": products[1].unit,
        "vat_rate": 19.0,
        "delivery_address": order_items[0].delivery_address.as_str(),
        "pickup_address": products[1].seller.address_as_str,
    }


def test_use_neighbour_delivery_company_in_delivery_document(
    order_with_neighbour_product, buyer, neighbour_region
):

    order_with_neighbour_product.recalculate_items_delivery_fee()

    factory = factories.DeliveryOverviewBuyerFactory(
        order_with_neighbour_product, region=buyer.region
    )
    document = factory.compose()
    document.save()

    assert (
        document.lines[2]["delivery_company"]
        == neighbour_region.setting.logistics_company.company_name
    )
