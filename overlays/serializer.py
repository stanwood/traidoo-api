from rest_framework import serializers

from overlays.models import Overlay, OverlayButton


class OverlayButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverlayButton
        fields = ["title", "url", "order"]


class OverlaySerializer(serializers.ModelSerializer):
    buttons = serializers.ListSerializer(child=OverlayButtonSerializer())

    class Meta:
        model = Overlay
        fields = [
            "overlay_type",
            "title",
            "subtitle",
            "body",
            "avatar",
            "image",
            "buttons",
        ]
