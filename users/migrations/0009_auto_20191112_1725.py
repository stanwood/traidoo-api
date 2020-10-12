# Generated by Django 2.2.1 on 2019-11-12 17:25

import storages.backends.gcloud
from django.db import migrations, models

import core.storage.utils


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_user_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="business_license",
            field=models.FileField(
                blank=True,
                null=True,
                storage=storages.backends.gcloud.GoogleCloudStorage(),
                upload_to=core.storage.utils.private_image_upload_to,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="drivers_license_photo",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=storages.backends.gcloud.GoogleCloudStorage(),
                upload_to=core.storage.utils.private_image_upload_to,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="id_photo",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=storages.backends.gcloud.GoogleCloudStorage(),
                upload_to=core.storage.utils.private_image_upload_to,
            ),
        ),
    ]
