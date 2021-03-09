import datetime

from django.contrib.auth.models import Group
from django.db.models import Q, Sum, Count

from common.commands import ExportCommand
from orders.models import Order
from users.models import User


class Command(ExportCommand):
    help = "Saves buyers in csv format for shopify import"

    def get_queryset(self):
        paid_orders = Q(order__status=Order.STATUSES.get_value("paid"))
        seller_group_id = (
            Group.objects.filter(name="buyer").values_list("id", flat=True).first()
        )

        return User.objects.filter(groups=seller_group_id).annotate(
            total_spend=Sum("order__total_price", filter=paid_orders),
            orders_count=Count("order", filter=paid_orders),
        )

    def write_header(self, writer):
        writer.writerow(
            [
                "First Name",
                "Last Name",
                "Email",
                "Company",
                "Address1",
                "Address2",
                "City",
                "Province",
                "Province Code",
                "Country",
                "Country Code",
                "Zip",
                "Phone",
                "Accepts Marketing",
                "Total Spent",
                "Total Orders",
                "Tags",
                "Note",
                "Tax Exempt",
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
                obj.street,
                "",
                obj.city,
                "",
                "",
                obj.residence_country_code,
                obj.residence_country_code,
                obj.zip,
                obj.phone,
                "no",
                obj.total_spend,
                obj.orders_count,
                tags,
                "",
                "",
            ]
        )

    def get_output_file_name(self):
        return f"buyers_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"
