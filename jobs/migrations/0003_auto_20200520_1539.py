# Generated by Django 2.2.10 on 2020-05-20 15:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0002_auto_20190611_1913"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="detour",
            options={"verbose_name": "Detour", "verbose_name_plural": "Detours"},
        ),
        migrations.AlterModelOptions(
            name="job", options={"verbose_name": "Job", "verbose_name_plural": "Jobs"},
        ),
        migrations.AlterField(
            model_name="detour",
            name="job",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="detours",
                to="jobs.Job",
                verbose_name="Job",
            ),
        ),
        migrations.AlterField(
            model_name="detour",
            name="length",
            field=models.PositiveIntegerField(default=0, verbose_name="Lenght"),
        ),
        migrations.AlterField(
            model_name="detour",
            name="route",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="routes.Route",
                verbose_name="Route",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="order_item",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="job",
                to="orders.OrderItem",
                verbose_name="Order item",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
    ]