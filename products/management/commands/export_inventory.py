import csv
import datetime
from collections import defaultdict

from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils.text import slugify

from common.commands import ExportCommand
from products.models import Product


class Command(ExportCommand):
    help = "Saves products inventory into csv compatible with Shopify inventory"

    def get_header(self):
        return [
            "Handle",
            "Title",
            "Option1 Name",
            "Option1 Value",
            "Option2 Name",
            "Option2 Value",
            "Option3 Name",
            "Option3 Value",
            "SKU",
            "HS Code",
            "COO",
            "Mittelhof",
        ]

    def get_output_file_name(self):
        return f"inventory_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"

    def get_writer(self, output_file):
        return csv.DictWriter(output_file, self.get_header())

    def write_header(self, writer):
        writer.writeheader()

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("seller", "category")
            .annotate(items_count=Coalesce(Sum("items__quantity"), 0))
            .values(
                "id",
                "name",
                "items_count",
            )
            .all()
        )
        return queryset

    def write_row(self, obj, writer):
        row = defaultdict(lambda: "")

        row["Handle"] = slugify(obj["name"])
        row["Title"] = obj["name"]
        row["Option1 Name"] = obj["name"]
        row["Option1 Value"] = obj["name"]
        row["SKU"] = obj["id"]
        row["Mittelhof"] = obj["items_count"]

        writer.writerow(row)
