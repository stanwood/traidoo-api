from model_mommy import mommy

from delivery_options.models import DeliveryOption
from documents import factories


def test_create_delivery_overview_producer(
    order,
    order_items,
    products,
    logistics_user,
    traidoo_region,
    delivery_address,
    delivery_options,
    buyer,
    seller,
):
    order.recalculate_items_delivery_fee()
    factory = factories.DeliveryOverviewSellerFactory(
        order, seller=seller, region=traidoo_region
    )
    document = factory.compose()
    document.save()

    assert document.seller == factories.DeliveryOverviewSellerFactory.as_dict(
        logistics_user
    )
    assert document.buyer == factories.DeliveryOverviewSellerFactory.as_company(seller)
    assert document.order_id == order.id
    assert len(document.lines) == 2
    assert document.lines[0] == {
        "amount": 3,
        "container_name": "Isolierbox",
        "count": 3.0,
        "delivery_company": "Traidoo",
        "delivery_date": order_items[0].delivery_date.strftime("%d.%m.%Y"),
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": seller.organic_control_body,
        "price": 18.81,
        "producer": "Traidoo",
        "unit": products[0].unit,
        "vat_rate": products[0].vat,
        "delivery_address": order_items[0].delivery_address_as_str,
        "pickup_address": seller.address_as_str,
    }
    assert document.lines[1] == {
        "amount": 1,
        "container_name": "Isolierbox",
        "count": 2.0,
        "delivery_company": seller.company_name,
        "delivery_date": order_items[1].delivery_date.strftime("%d.%m.%Y"),
        "name": products[1].name,
        "number": products[1].id,
        "organic_control_body": seller.organic_control_body,
        "price": 14.28,
        "producer": "Traidoo",
        "unit": products[1].unit,
        "vat_rate": products[1].vat,
        "delivery_address": order_items[1].delivery_address_as_str,
        "pickup_address": seller.address_as_str,
    }


def test_create_delivery_overview_producer_3rd_party_delivery(
    order,
    delivery_options,
    logistics_user,
    traidoo_region,
    delivery_address,
    products,
    order_items,
    seller,
    send_task,
    settings,
):
    settings.FEATURES["routes"] = True

    products[0].third_party_delivery = True
    products[0].save()
    order_items[0].delivery_option_id = DeliveryOption.SELLER
    order_items[0].save()
    order.recalculate_items_delivery_fee()

    supplier = mommy.make_recipe(
        "users.user", email="supplier@example.com", region=traidoo_region
    )
    mommy.make("jobs.Job", order_item=order_items[0], user=supplier)

    factory = factories.DeliveryOverviewSellerFactory(
        order, seller=seller, region=traidoo_region
    )
    document = factory.compose()
    document.save()

    assert document.seller == factories.DeliveryOverviewSellerFactory.as_dict(
        logistics_user
    )

    assert document.buyer == factories.DeliveryOverviewSellerFactory.as_company(seller)

    assert document.order_id == order.id
    assert len(document.lines) == 2
    assert document.lines[0] == {
        "amount": 3.0,
        "container_name": "Isolierbox",
        "count": 3.0,
        "delivery_company": supplier.company_name,
        "delivery_date": order_items[0].delivery_date.strftime("%d.%m.%Y"),
        "name": products[0].name,
        "number": products[0].id,
        "organic_control_body": seller.organic_control_body,
        "price": 0.12,
        "producer": "Traidoo",
        "unit": products[0].unit,
        "vat_rate": 19.0,
        "delivery_address": order_items[0].delivery_address_as_str,
        "pickup_address": seller.address_as_str,
    }
    assert document.lines[1] == {
        "amount": 1,
        "container_name": "Isolierbox",
        "count": 2.0,
        "delivery_company": seller.company_name,
        "delivery_date": order_items[1].delivery_date.strftime("%d.%m.%Y"),
        "name": products[1].name,
        "number": products[1].id,
        "organic_control_body": seller.organic_control_body,
        "price": 14.28,
        "producer": "Traidoo",
        "unit": products[1].unit,
        "vat_rate": products[1].vat,
        "delivery_address": order_items[1].delivery_address_as_str,
        "pickup_address": seller.address_as_str,
    }


def test_delivery_overview_seller_from_neighbour_region(
    order_with_neighbour_product, other_region_product, neighbour_region
):

    document = factories.DeliveryOverviewSellerFactory(
        order_with_neighbour_product,
        seller=other_region_product.seller,
        region=neighbour_region,
    ).compose()

    assert document.seller == factories.DeliveryOverviewSellerFactory.as_dict(
        neighbour_region.setting.logistics_company
    )
    assert document.buyer == factories.DeliveryOverviewSellerFactory.as_company(
        other_region_product.seller
    )
    assert (
        document.lines[0]["delivery_company"]
        == neighbour_region.setting.logistics_company.company_name
    )
