from rest_framework import serializers


class BlankableDecimalField(serializers.DecimalField):
    def to_internal_value(self, data):
        if data in ('', 'null'):
            return None

        return super(BlankableDecimalField, self).to_internal_value(data)
