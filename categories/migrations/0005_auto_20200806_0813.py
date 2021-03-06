# Generated by Django 2.2.10 on 2020-08-06 08:13

from django.conf import settings
from django.db import migrations


def create_icons(apps, schema_editor):
    CategoryIcon = apps.get_model("categories", "CategoryIcon")
    icons = list(map(lambda n: f"ico{n}.svg", range(1, 36)))
    category_icons = [
        CategoryIcon(
            id=index + 1,
            name=icon,
            icon_url=f"https://storage.googleapis.com/{settings.STATIC_BUCKET}/categories/{icon}",
        )
        for index, icon in enumerate(icons)
    ]
    CategoryIcon.objects.bulk_create(category_icons)


class Migration(migrations.Migration):

    dependencies = [
        ("categories", "0004_categoryicon"),
    ]

    operations = [
        migrations.RunPython(create_icons),
    ]
