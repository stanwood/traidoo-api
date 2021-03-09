import datetime

from django.contrib.auth.models import Group

from common.commands import ExportCommand
from users.models import User


class Command(ExportCommand):
    help = "Saves sellers in csv format for shopify import"

    def get_queryset(self):
        seller_group_id = (
            Group.objects.filter(name="seller").values_list("id", flat=True).first()
        )

        return User.objects.filter(groups=seller_group_id)

    def write_header(self, writer):
        writer.writerow(
            [
                "firstName",
                "lastName",
                "email",
                "brandName",
                "phoneNumber",
                "address",
                "city",
                "country",
                "postalCode",
                "tags",
            ]
        )

    def write_row(self, obj, writer):
        if obj.is_cooperative_member:
            tags = "genossen"
        else:
            tags = ""
        writer.writerow(
            [
                obj.first_name,
                obj.last_name,
                obj.email,
                obj.company_name,
                obj.phone,
                obj.street,
                obj.city,
                obj.residence_country_code,
                obj.zip,
                tags,
            ]
        )

    def get_output_file_name(self):
        return f"sellers_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
