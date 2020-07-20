import json
from json import JSONDecodeError

import six
from rest_framework.exceptions import ValidationError
from taggit.models import Tag
from taggit_serializer.serializers import TagListSerializerField


class CustomTagListSerializerField(TagListSerializerField):

    # FIXME: https://github.com/glemmaPaul/django-taggit-serializer/issues/34

    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except JSONDecodeError:
                raise ValidationError("Value is not parsable")
        if not isinstance(value, list):
            raise ValidationError("Value is not a list")

        try:
            value = [int(tag_id) for tag_id in value]
        except ValueError:
            raise ValidationError("Tag ids must be integers")
        new_values = []
        for tag_id in value:
            if not isinstance(tag_id, six.integer_types):
                raise ValidationError("Only integers are allowed")

            try:
                tag = Tag.objects.get(id=tag_id)
            except Tag.DoesNotExist:
                raise ValidationError(f"Tag with ID {tag_id} does not exist")
            else:
                new_values.append(tag.name)

        return new_values

    def to_representation(self, value):
        if type(value) is not list:
            return [
                {"id": tag.id, "name": tag.name, "slug": tag.slug}
                for tag in value.all()
            ]
        return value
