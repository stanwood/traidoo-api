from djoser.compat import get_user_email
from djoser import views
from djoser.email import PasswordResetEmail

from common.utils import get_region
from mails.utils import send_mail


class PasswordResetView(views.PasswordResetView):
    def send_password_reset_email(self, user):
        context = {"user": user}
        to = [get_user_email(user)]

        email = PasswordResetEmail(self.request, context)

        send_mail(
            region=get_region(self.request),
            subject="Password reset",
            recipient_list=to,
            template="mails/users/password_reset.html",
            context=email.get_context_data(),
        )
