# Generated by Django 2.2.10 on 2020-05-20 15:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("items", "0003_auto_20200520_1323"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="item",
            options={"verbose_name": "Item", "verbose_name_plural": "Items"},
        ),
        migrations.AlterField(
            model_name="item",
            name="latest_delivery_date",
            field=models.DateField(verbose_name="Latest delivery date"),
        ),
        migrations.AlterField(
            model_name="item",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="products.Product",
                verbose_name="Product",
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="quantity",
            field=models.PositiveIntegerField(verbose_name="Quantity"),
        ),
        migrations.AlterField(
            model_name="item",
            name="valid_from",
            field=models.DateField(
                blank=True, null=True, verbose_name="Date valid from"
            ),
        ),
    ]
