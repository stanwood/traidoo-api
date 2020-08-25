# Generated by Django 2.2.10 on 2020-08-06 07:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0003_auto_20200520_1539'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryIcon',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('icon_url', models.CharField(max_length=255, verbose_name='Icon URL')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]