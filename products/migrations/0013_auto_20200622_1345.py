# Generated by Django 2.2.10 on 2020-06-22 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_auto_20200520_1539'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bigautofieldtaggeditem',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products_bigautofieldtaggeditem_tagged_items', to='contenttypes.ContentType', verbose_name='content type'),
        ),
    ]
