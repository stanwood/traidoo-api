import collections

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from common.utils import get_region
from core.permissions.cron_or_task import IsCronOrTask
from core.tasks.mixin import TasksMixin
from items.models import Item
from mails.utils import send_mail

User = get_user_model()


class FindUnsoldItemsView(TasksMixin, views.APIView):

    permission_classes = (AllowAny, IsCronOrTask)

    def get(self, request, format=None):
        sellers = User.objects.filter(groups__name="seller")

        for seller in sellers:
            self.send_task(
                f"/orders/cron/find-unsold-items/{seller.id}",
                queue_name="unsold-items",
                http_method="POST",
                headers={"Region": seller.region.slug},
            )

        return Response()

    def post(self, request, seller_id, format=None):
        unsold_items_by_product = collections.defaultdict(dict)

        now = timezone.localtime(
            timezone.now(), pytz.timezone(settings.USER_DEFAULT_TIME_ZONE)
        )

        items = (
            Item.objects.select_related("product")
            .annotate(items_available=Coalesce(Sum("product__items__quantity"), 0))
            .filter(
                items_available__gt=0,
                product__seller_id=seller_id,
                latest_delivery_date__lt=now.date(),
            )
        )

        for item in items:
            try:
                count = unsold_items_by_product[item.product.id]["count"]
            except KeyError:
                count = 0

            unsold_items_by_product[item.product.id] = {
                "name": item.product.name,
                "count": count + 1,
            }

        items.delete()

        if unsold_items_by_product:
            send_mail(
                region=get_region(request),
                subject="Abgelaufene Produkte",
                recipient_list=[User.objects.get(id=seller_id).email],
                template="mails/unsold_items.html",
                context={
                    "items_by_product": dict(unsold_items_by_product),
                    "base_url": Site.objects.get_current().domain,
                },
            )

        return Response()
