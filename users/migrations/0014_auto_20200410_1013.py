# Generated by Django 2.2.10 on 2020-04-10 10:13

from django.db import migrations, models

import core.storage.utils


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0013_auto_20200409_0918"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="iban",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
