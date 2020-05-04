from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class FeaturesView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        return Response(settings.FEATURES)
