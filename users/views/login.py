from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.six import text_type

from common.utils import get_region
from users.serializers import UserSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super(CustomTokenObtainPairSerializer, self).validate(attrs)

        request = self.context.get("request")
        region = get_region(request)

        if region and self.user.region and region.id != self.user.region.id:
            raise AuthenticationFailed()

        refresh = self.get_token(self.user)

        data.update({
            "refresh": text_type(refresh),
            "auth_token": text_type(refresh.access_token),
            "user": UserSerializer(self.user).data,
        })

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
