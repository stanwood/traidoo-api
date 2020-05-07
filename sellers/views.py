from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny

from sellers.serializers import SellerPublicSerializer

User = get_user_model()


class SellerViewSet(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = SellerPublicSerializer
    permission_classes = [AllowAny]
