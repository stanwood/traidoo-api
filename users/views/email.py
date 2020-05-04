from rest_framework import views, status
from rest_framework.permissions import AllowAny
from ..serializers import UserEmailSerializer
from ..models import User
from rest_framework.response import Response


class UserEmailView(views.APIView):
    permission_classes = (AllowAny, )

    def post(self, request, format=None):
        serializer = UserEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email_exists = User.objects.filter(email=serializer.data['email']).exists()

        user_exists = False
        if serializer.data.get('user_id'):
            user_exists = User.objects.filter(id=serializer.data['user_id']).exists()

        if email_exists and not user_exists:
            return Response({'exists': True})

        return Response({'exists': False})
