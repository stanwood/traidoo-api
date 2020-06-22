from rest_framework import serializers

from overlays.models import Overlay


class OvertlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Overlay
        fields = [
            "overlay_type",
            "title",
            "subtitle",
            "body",
            "learn_more_url",
            "avatar",
            "image",
        ]
