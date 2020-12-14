# Generated by Django 2.2.15 on 2020-12-14 09:44

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [
        ("orders", "0001_initial"),
        ("orders", "0002_auto_20190429_1605"),
        ("orders", "0003_order_processed"),
        ("orders", "0004_orderitem_delivery_fee"),
        ("orders", "0005_auto_20200116_2025"),
        ("orders", "0006_order_region"),
        ("orders", "0007_remove_order_payment_method"),
        ("orders", "0008_auto_20200520_1539"),
    ]

    initial = True

    dependencies = [
        ("delivery_options", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0001_initial"),
        ("delivery_addresses", "0001_initial"),
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(0, "Cart"), (1, "Paid"), (2, "Ordered")],
                        default=0,
                        verbose_name="Status",
                    ),
                ),
                (
                    "total_price",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Total price"
                    ),
                ),
                (
                    "earliest_delivery_date",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Earliest delivery date"
                    ),
                ),
                (
                    "buyer",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Buyer",
                    ),
                ),
                (
                    "processed",
                    models.BooleanField(default=False, verbose_name="Processed"),
                ),
                (
                    "region",
                    models.ForeignKey(
                        help_text="Region in which order took place",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="common.Region",
                        verbose_name="Region",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("latest_delivery_date", models.DateField()),
                ("quantity", models.IntegerField()),
                ("product_snapshot", django.contrib.postgres.fields.jsonb.JSONField()),
                (
                    "delivery_address",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="delivery_addresses.DeliveryAddress",
                    ),
                ),
                (
                    "delivery_option",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="delivery_options.DeliveryOption",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="items",
                        to="orders.Order",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="products.Product",
                    ),
                ),
                (
                    "delivery_fee",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
            ],
            options={
                "unique_together": {("order", "product", "latest_delivery_date")},
            },
        ),
    ]
