# Generated by Django 2.2.4 on 2020-04-06 16:40

import django.db.models.deletion
import storages.backends.gcloud
from django.conf import settings
from django.db import migrations, models

import core.storage.utils
import users.models.kyc


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_user_region"),
    ]

    operations = [
        migrations.RemoveField(model_name="user", name="drivers_license_photo",),
        migrations.RemoveField(model_name="user", name="drivers_license_photo_url",),
        migrations.RemoveField(model_name="user", name="invoice_city",),
        migrations.RemoveField(model_name="user", name="invoice_street",),
        migrations.RemoveField(model_name="user", name="invoice_zip",),
        migrations.CreateModel(
            name="KycDocument",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(
                        choices=[
                            (
                                users.models.kyc.KycDocument.Name("IDENTITY_PROOF"),
                                "IDENTITY_PROOF",
                            ),
                            (
                                users.models.kyc.KycDocument.Name(
                                    "ARTICLES_OF_ASSOCIATION"
                                ),
                                "ARTICLES_OF_ASSOCIATION",
                            ),
                            (
                                users.models.kyc.KycDocument.Name("REGISTRATION_PROOF"),
                                "REGISTRATION_PROOF",
                            ),
                            (
                                users.models.kyc.KycDocument.Name("ADDRESS_PROOF"),
                                "ADDRESS_PROOF",
                            ),
                            (
                                users.models.kyc.KycDocument.Name(
                                    "SHAREHOLDER_DECLARATION"
                                ),
                                "SHAREHOLDER_DECLARATION",
                            ),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        storage=storages.backends.gcloud.GoogleCloudStorage(
                            default_acl="projectPrivate"
                        ),
                        upload_to=core.storage.utils.private_image_upload_to,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"unique_together": {("user", "name")},},
        ),
    ]
