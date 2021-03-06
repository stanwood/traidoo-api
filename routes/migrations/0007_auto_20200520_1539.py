# Generated by Django 2.2.10 on 2020-05-20 15:39

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import routes.models


class Migration(migrations.Migration):

    dependencies = [
        ("routes", "0006_auto_20200507_0742"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="route",
            options={"verbose_name": "Route", "verbose_name_plural": "Routes"},
        ),
        migrations.AlterField(
            model_name="route",
            name="destination",
            field=models.CharField(max_length=255, verbose_name="Destination"),
        ),
        migrations.AlterField(
            model_name="route",
            name="frequency",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.PositiveIntegerField(
                    choices=[
                        (1, routes.models.Days(1)),
                        (2, routes.models.Days(2)),
                        (3, routes.models.Days(3)),
                        (4, routes.models.Days(4)),
                        (5, routes.models.Days(5)),
                        (6, routes.models.Days(6)),
                        (7, routes.models.Days(7)),
                    ]
                ),
                size=7,
                verbose_name="Frequency",
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="length",
            field=models.PositiveIntegerField(default=0, verbose_name="Length"),
        ),
        migrations.AlterField(
            model_name="route",
            name="origin",
            field=models.CharField(max_length=255, verbose_name="Origin"),
        ),
        migrations.AlterField(
            model_name="route",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="routes",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="route",
            name="waypoints",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=255),
                blank=True,
                default=list,
                size=None,
                verbose_name="Way points",
            ),
        ),
    ]
