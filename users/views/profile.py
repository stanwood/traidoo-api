from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.permissions.current_user import CurrentUser

from ..serializers import (
    UserCompanyProfile,
    UserDocumentsProfile,
    UserPersonalProfile,
    UserProfile,
)

User = get_user_model()


class UserProfileViewSet(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfile
    permission_classes = [CurrentUser]

    def get_object(self):
        if self.kwargs.get("pk", None) == "me":
            self.kwargs["pk"] = self.request.user.pk
        return super(UserProfileViewSet, self).get_object()


class UserPersonalProfileViewSet(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPersonalProfile
    permission_classes = [IsAuthenticated]

    def get_object(self):
        self.kwargs["pk"] = self.request.user.pk
        return super(UserPersonalProfileViewSet, self).get_object()


class UserCompanyProfileViewSet(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCompanyProfile
    permission_classes = [IsAuthenticated]

    def get_object(self):
        self.kwargs["pk"] = self.request.user.pk
        return super(UserCompanyProfileViewSet, self).get_object()


class UserDocumentsProfileViewSet(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserDocumentsProfile
    permission_classes = [IsAuthenticated]

    def get_object(self):
        self.kwargs["pk"] = self.request.user.pk
        return super(UserDocumentsProfileViewSet, self).get_object()
