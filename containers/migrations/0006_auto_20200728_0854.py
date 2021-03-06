# Generated by Django 2.2.10 on 2020-07-28 08:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("containers", "0005_auto_20200520_1539"),
    ]

    operations = [
        migrations.AlterField(
            model_name="container",
            name="deposit",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(
                        0, message="Container deposit cannot be negative"
                    )
                ],
                verbose_name="Deposit",
            ),
        ),
    ]
