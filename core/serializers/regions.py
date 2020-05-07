import six
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from common.models import Region
from common.serializers import RegionSerializer


class CustomRegionsSerializerField(serializers.ListField):
    """
    FIXME: This is a workaround. I couldn't implement the regions field
    to be able to send an empty list to remove all regions.
    This workaround allows sending empty string.
    """

    def get_value(self, dictionary):
        if self.context["request"].data.get("regions") == "":
            return []
        return super().get_value(dictionary)

    def to_internal_value(self, value):
        try:
            value = [int(region_id) for region_id in value]
        except ValueError:
            raise ValidationError("Regions ids must be integers")

        new_values = []
        for region_id in value:
            if not isinstance(region_id, six.integer_types):
                raise ValidationError("Only integers are allowed")

            try:
                region = Region.objects.get(id=region_id)
            except Region.DoesNotExist:
                raise ValidationError(f"Region with ID {region_id} does not exist")
            else:
                new_values.append(region.id)

        return new_values

    def to_representation(self, value):
        if type(value) is not list:
            return RegionSerializer(value, many=True).data
        return value
