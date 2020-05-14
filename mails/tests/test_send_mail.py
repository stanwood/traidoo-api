import bs4
from django.conf import settings

from mails.utils import send_mail


def test_use_global_platform_mail_if_local_is_missing(
    traidoo_settings, mailoutbox, traidoo_region
):
    setting = traidoo_region.setting
    setting.platform_user = None
    setting.save()

    send_mail(traidoo_region, "Foo", ["foo@bar.com"], "mails/unsold_items.html", {})
    assert mailoutbox[-1].subject == "Foo"
    assert mailoutbox[-1].from_email == settings.DEFAULT_FROM_EMAIL


def test_use_regional_website_slogan_in_email(traidoo_region, mailoutbox):
    send_mail(traidoo_region, "Foo", ["foo@bar.com"], "mails/unsold_items.html", {})
    assert traidoo_region.website_slogan in mailoutbox[-1].body


def test_use_footer_from_region_model_in_email(traidoo_region, mailoutbox):
    send_mail(traidoo_region, "Foo", ["foo@bar.com"], "mails/unsold_items.html", {})
    assert traidoo_region.mail_footer in mailoutbox[-1].body


def test_use_logo_from_region_model_in_email(traidoo_region, mailoutbox, image_file):
    image_file._committed = True
    traidoo_region.mail_logo = image_file
    traidoo_region.save()
    send_mail(traidoo_region, "Foo", ["foo@bar.com"], "mails/unsold_items.html", {})
    soup = bs4.BeautifulSoup(mailoutbox[-1].body, features="html.parser")
    assert "png" in soup.find_all("img")[0].attrs["src"]


def test_add_regional_reply_to(traidoo_region, mailoutbox):
    send_mail(traidoo_region, "Foo", ["foo@bar.com"], "mails/unsold_items.html", {})
    assert f"intercom+{traidoo_region.name}@example.com" in mailoutbox[-1].reply_to
