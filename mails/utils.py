from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def get_admin_emails():
    UserModel = get_user_model()
    return UserModel.objects.filter(
        groups__name__contains=settings.ADMIN_GROUP_NAME
    ).values_list("email", flat=True)


def send_mail(
    region,
    subject,
    recipient_list,
    template,
    context=None,
    from_email=None,
    attachments=None,
):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        mailbox, domain = settings.INTERCOM_EMAIL.split("@")
        reply_to = [f"{mailbox}+{region.name}@{domain}"]
    except AttributeError:
        reply_to = []

    if context is None:
        context = {}

    try:
        context["website_slogan"] = region.website_slogan or ""
        context["mail_footer"] = region.mail_footer or ""
        if region.mail_logo:
            context["logo_url"] = region.mail_logo.url
    except AttributeError:
        pass

    html_message = render_to_string(template, context)

    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=from_email,
        bcc=get_admin_emails(),
        attachments=attachments,
        to=recipient_list,
        reply_to=reply_to,
    )

    email.content_subtype = "html"
    email.send()
