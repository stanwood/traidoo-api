# Generated by Django 2.2.10 on 2020-06-22 13:45

import core.storage.utils
import django.core.files.storage
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_auto_20200520_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kycdocument',
            name='file',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(), upload_to=core.storage.utils.private_image_upload_to, verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='user',
            name='business_license',
            field=models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(), upload_to=core.storage.utils.private_image_upload_to, verbose_name='Business license'),
        ),
        migrations.AlterField(
            model_name='user',
            name='id_photo',
            field=models.ImageField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(), upload_to=core.storage.utils.private_image_upload_to, verbose_name='ID photo'),
        ),
    ]