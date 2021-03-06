# Generated by Django 2.2.1 on 2019-11-12 16:45

import core.storage.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_auto_20190905_0712'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=core.storage.utils.public_image_upload_to),
        ),
        migrations.AlterField(
            model_name='product',
            name='image_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
