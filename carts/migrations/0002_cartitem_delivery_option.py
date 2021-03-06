# Generated by Django 2.2.4 on 2020-01-13 07:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("delivery_options", "0001_initial"), ("carts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="cartitem",
            name="delivery_option",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="delivery_options.DeliveryOption",
            ),
        )
    ]
