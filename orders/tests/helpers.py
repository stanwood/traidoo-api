from model_bakery import baker

from documents.models import Document


def create_documents(buyer_group, seller_group, region):
    buyer = baker.make("users.user", groups=[buyer_group])
    seller = baker.make("users.user", groups=[seller_group])
    product = baker.make("products.product", seller=seller, region=region)
    baker.make("items.item", product=product)
    order = baker.make("orders.order", buyer=buyer, total_price=10)
    baker.make_recipe("orders.orderitem", product=product, order=order)

    documents = {}

    for document_type in Document.TYPES:
        documents[document_type.value[0]] = baker.make(
            "documents.document",
            document_type=document_type.value[0],
            order=order,
            buyer={
                "user_id": buyer.id
                if document_type != Document.TYPES.delivery_overview_seller
                else buyer.id + 1
            },
            seller={
                "user_id": seller.id
                if document_type != Document.TYPES.delivery_overview_buyer
                else seller.id + 1
            },
            lines=[
                {
                    "price": 1,
                    "count": 3,
                    "vat_rate": 0.7,
                    "amount": 5,
                    "seller_user_id": seller.id,
                },
                {
                    "price": 2,
                    "count": 2,
                    "vat_rate": 0.7,
                    "amount": 5,
                    "seller_user_id": seller.id,
                },
                {
                    "price": 3,
                    "count": 1,
                    "vat_rate": 0.7,
                    "amount": 5,
                    "seller_user_id": seller.id,
                },
            ],
        )

    return buyer, seller, order, documents
