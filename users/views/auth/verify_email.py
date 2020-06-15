from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import get_region
from core.tasks.mixin import TasksMixin
from users.serializers import TokenUidSerializer


class VerifyEmailView(APIView, TasksMixin):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        region = get_region(request)

        serializer = TokenUidSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.user
        user.is_active = True
        user.is_email_verified = True
        user.save()

        self.send_task(
            f"/mangopay/tasks/create-wallet",
            payload={"user_id": user.id,},
            queue_name="mangopay-create-wallet",
            http_method="POST",
            schedule_time=5,
            headers={"Region": region.slug, "Content-Type": "application/json"},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)
