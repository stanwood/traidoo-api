import csv
import datetime
from collections import defaultdict
from decimal import Decimal

from django.core.files.storage import default_storage
from django.db.models import Sum
from django.utils.text import slugify

from products.models import Product
from common.commands import ExportCommand


def product_tags(product):
    tags = set()
    if product["is_vegan"]:
        tags.add("vegan")
    if product["is_organic"]:
        tags.add("organic")
    if product["is_gluten_free"]:
        tags.add("gluten-free")
    if product["is_grazing_animal"]:
        tags.add("grazing-animal")

    tags.add(f"mwst_{int(product['vat'])}")

    return tags


def product_weight_in_grams(product):
    if product["unit"] == "g":
        return product["amount"]

    if product["unit"] == "kg":
        return product["amount"] * 1000

    return 0


def product_weight_unit(product):
    if product["unit"] in ("g", "kg"):
        return product["unit"]

    return ""


def product_price(product):
    price = Decimal(str(product["price"]))
    if product["seller__is_cooperetive_member"]:
        price = price * 0.9
    else:
        price = price * 0.88
    price = price.quantize(Decimal(".01"), "ROUND_HALF_UP")
    return price


def product_description_with_unit_and_amount(product):
    units_translation = {
        "Bottle": "Flasche",
        "Bundle": "Bündel",
        "g": "g",
        "Glass": "Glas",
        "kg": "kg",
        "l": "l",
        "Net": "Netz",
        "Piece": "Stück",
    }

    unit_translated = units_translation.get(product["unit"], product["unit"])

    return f"{product['description']} {product['amount']} {unit_translated}"


def image_url(product):
    try:
        if product["image"]:
            image = default_storage.open(product["image"])
            return image.blob.public_url
    except LookupError:
        pass
    return product.get("image_url", "")


class Command(ExportCommand):
    help = "Saves products in csv format for shopify import"

    def get_header(self):
        return [
            "Handle",
            "Title",
            "Body (HTML)",
            "Vendor",
            "Type",
            "Tags",
            "Published",
            "Option1 Name",
            "Option1 Value",
            "Option2 Name",
            "Option2 Value",
            "Option3 Name",
            "Option3 Value",
            "Variant SKU",
            "Variant Grams",
            "Variant Inventory Tracker",
            "Variant Inventory Qty",
            "Variant Inventory Policy",
            "Variant Fulfillment Service",
            "Variant Price",
            "Variant Compare At Price",
            "Variant Requires Shipping",
            "Variant Taxable",
            "Variant Barcode",
            "Image Src",
            "Image Position",
            "Image Alt Text",
            "Gift Card",
            "SEO Title",
            "SEO Description",
            "Google Shopping / Google Product Category",
            "Google Shopping / Gender",
            "Google Shopping / Age Group",
            "Google Shopping / MPN",
            "Google Shopping / AdWords Grouping",
            "Google Shopping / AdWords Labels",
            "Google Shopping / Condition",
            "Google Shopping / Custom Product",
            "Google Shopping / Custom Label 0",
            "Google Shopping / Custom Label 1",
            "Google Shopping / Custom Label 2",
            "Google Shopping / Custom Label 3",
            "Google Shopping / Custom Label 4",
            "Variant Image",
            "Variant Weight Unit",
            "Variant Tax Code",
            "Cost per item",
            "Status",
            "Collection",
        ]

    def get_output_file_name(self):
        return f"products_{datetime.datetime.now().strftime('%Y-%m-%d')}.csv"

    def get_writer(self, output_file):
        return csv.DictWriter(output_file, self.get_header())

    def write_header(self, writer):
        writer.writeheader()

    def get_queryset(self):
        queryset = (
            Product.objects.select_related("seller", "category")
            .annotate(items_count=Sum("items__quantity"))
            .values(
                "id",
                "name",
                "description",
                "unit",
                "amount",
                "seller__company_name",
                "category__name",
                "price",
                "is_vegan",
                "is_organic",
                "is_gluten_free",
                "is_gmo_free",
                "is_grazing_animal",
                "image",
                "image_url",
                "items_count",
                "seller__is_cooperative_member",
                "vat",
            )
            .all()
        )
        return queryset

    def write_row(self, obj, writer):
        row = defaultdict(lambda: "")

        row["Handle"] = slugify(obj["name"])
        row["Title"] = obj["name"]
        row["Body (HTML)"] = product_description_with_unit_and_amount(obj)
        row["Vendor"] = obj["seller__company_name"]
        row["Type"] = obj["category__name"]
        row["Tags"] = ", ".join(product_tags(obj))
        row["Published"] = "TRUE"
        row["Option1 Name"] = "Title"
        row["Option1 Value"] = obj["name"]
        row["Variant SKU"] = obj["id"]
        row["Variant Grams"] = product_weight_in_grams(obj)
        row["Variant Inventory Tracker"] = "shopify"
        row["Variant Inventory Qty"] = obj["items_count"] or 0
        row["Variant Inventory Policy"] = "deny"
        row["Variant Fulfillment Service"] = "manual"
        row["Variant Price"] = obj["price"]
        row["Variant Requires Shipping"] = "TRUE"
        row["Image Src"] = image_url(obj)
        row["Image Position"] = ""
        row["Variant Weight Unit"] = product_weight_unit(obj)
        row["Status"] = "active"
        row["Collection"] = obj["category__name"]

        writer.writerow(row)
