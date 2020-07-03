from model_bakery import baker

from documents.models import Document


def create_documents(buyer_group, seller_group, region, cooperative_member):
    buyer = baker.make(
        "users.user", groups=[buyer_group], is_cooperative_member=cooperative_member
    )
    seller = baker.make("users.user", groups=[seller_group])
    product = baker.make("products.product", seller=seller, region=region)
    baker.make("items.item", product=product)
    order = baker.make("orders.order", buyer=buyer, total_price=10)
    baker.make_recipe("orders.orderitem", product=product, order=order)

    documents = {}

    for document_type in Document.TYPES:
        documents[document_type.value[0]] = baker.make(
            "documents.document", document_type=document_type.value[0], order=order,
        )

    return buyer, seller, order, documents