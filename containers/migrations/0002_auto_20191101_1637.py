# Generated by Django 2.2.1 on 2019-11-01 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('containers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to='public/'),
        ),
        migrations.AlterField(
            model_name='container',
            name='image_url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
