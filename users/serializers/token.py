from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from common.utils import get_region


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(CustomTokenObtainPairSerializer, self).validate(attrs)

        request = self.context.get("request")
        region = get_region(request)

        if region and self.user.region and region.id != self.user.region.id:
            raise AuthenticationFailed()

        return data
