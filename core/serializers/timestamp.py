from datetime import datetime

import pytz
from django.conf import settings
from django.utils import timezone
from rest_framework import serializers


class TimestampField(serializers.DateTimeField):
    """
    Convert a django datetime to/from timestamp.
    """

    def to_internal_value(self, value):
        """
        deserialize a UTC timestamp to a DateTime value
        :param value: the timestamp value
        :return: a django DateTime value
        """

        converted = timezone.localtime(
            timezone.make_aware(datetime.utcfromtimestamp(int(value) / 1000.0)),
            timezone=pytz.timezone(settings.USER_DEFAULT_TIME_ZONE),
        )
        return super(TimestampField, self).to_representation(converted)


class TimestampDateField(serializers.DateField):
    """
    Convert a django datetime to/from timestamp.
    """

    def to_internal_value(self, value):
        """
        deserialize a timestamp to a DateTime value
        :param value: the timestamp value
        :return: a django DateTime value
        """
        converted = datetime.utcfromtimestamp(int(value) / 1000.0).date()
        return super(TimestampDateField, self).to_representation(converted)
