from django.urls import reverse
from model_bakery import baker

from documents.factories import DocumentFactory
from documents.models import DocumentSendLog


def test_send_documents_for_the_order(
    client_task, mailoutbox,
):
    region = baker.make_recipe("common.region")
    buyer = baker.make_recipe("users.user", region=region)
    order = baker.make_recipe("orders.order", region=region, buyer=buyer)
    platform_user = baker.make_recipe("users.user", region=region)
    baker.make_recipe(
        "documents.order_confirmation",
        buyer=DocumentFactory.as_dict(order.buyer),
        seller=DocumentFactory.as_dict(platform_user),
        order=order,
    )
    DocumentSendLog.objects.create(
        order_id=order.id, email=order.buyer.email, sent=False
    )
    response = client_task.post(
        reverse(
            "mail-documents", kwargs={"order_id": order.id, "email": order.buyer.email}
        ),
    )

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to[0] == order.buyer.email
    assert response.status_code == 200


def test_track_sending_emails(mailoutbox, client_task):
    region = baker.make_recipe("common.region")
    buyer = baker.make_recipe("users.user", region=region)
    order = baker.make_recipe("orders.order", region=region, buyer=buyer)
    platform_user = baker.make_recipe("users.user", region=region)
    baker.make_recipe(
        "documents.order_confirmation",
        buyer=DocumentFactory.as_dict(order.buyer),
        seller=DocumentFactory.as_dict(platform_user),
        order=order,
    )

    DocumentSendLog.objects.create(
        order_id=order.id, email=order.buyer.email, sent=False
    )

    client_task.post(
        reverse(
            "mail-documents", kwargs={"order_id": order.id, "email": order.buyer.email}
        ),
    )

    assert DocumentSendLog.objects.filter(
        email=order.buyer.email, order_id=order.id, sent=True
    ).exists()


def test_do_not_resend_documents_at_rerun(mailoutbox, client_task):
    region = baker.make_recipe("common.region")
    buyer = baker.make_recipe("users.user", region=region)
    order = baker.make_recipe("orders.order", region=region, buyer=buyer)
    platform_user = baker.make_recipe("users.user", region=region)
    baker.make_recipe(
        "documents.order_confirmation",
        buyer=DocumentFactory.as_dict(order.buyer),
        seller=DocumentFactory.as_dict(platform_user),
        order=order,
    )

    DocumentSendLog.objects.create(email=buyer.email, order=order, sent=True)
    client_task.post(
        reverse(
            "mail-documents", kwargs={"order_id": order.id, "email": order.buyer.email}
        ),
    )
    assert not mailoutbox
