# Generated by Django 2.2rc1 on 2019-05-17 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='delivery_requirements',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
