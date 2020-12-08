from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(CustomTokenObtainPairSerializer, self).validate(attrs)
        request = self.context.get("request")

        if (
            request.region
            and self.user.region
            and request.region.id != self.user.region.id
        ):
            raise AuthenticationFailed()

        return data
