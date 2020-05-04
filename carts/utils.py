import datetime
from typing import Union

import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers


def validate_earliest_delivery_date(
    date: Union[datetime.date, None],
) -> Union[datetime.date, serializers.ValidationError]:
    if not date:
        raise serializers.ValidationError(
            {"earliest_delivery_date": "Date is required."}
        )

    now = timezone.localtime(
        timezone.now(), pytz.timezone(settings.USER_DEFAULT_TIME_ZONE)
    )

    if date < now.date() + datetime.timedelta(
        days=settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[0]
    ):
        raise serializers.ValidationError(
            {"earliest_delivery_date": "Date must be in the future."}
        )

    if date > now.date() + datetime.timedelta(
        days=settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[1]
    ):
        raise serializers.ValidationError(
            {
                "earliest_delivery_date": f"Cannot exceed {settings.EARLIEST_DELIVERY_DATE_DAYS_RANGE[1]} days."
            }
        )

    return date
