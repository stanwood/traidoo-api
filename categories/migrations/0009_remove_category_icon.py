# Generated by Django 2.2.10 on 2020-08-06 11:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0008_auto_20200806_1107'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='icon',
        ),
    ]