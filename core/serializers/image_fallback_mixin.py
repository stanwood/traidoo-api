class ImageFallbackMixin(object):
    def to_representation(self, instance):
        representation = super(ImageFallbackMixin, self).to_representation(instance)

        try:
            replacement_fields = self.Meta.image_fallback_fields
        except AttributeError:
            replacement_fields = [("image", "image_url")]

        for destination, source in replacement_fields:
            if representation.get(destination) is None:
                representation[destination] = getattr(instance, source)

        return representation
