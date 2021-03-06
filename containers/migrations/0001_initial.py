# Generated by Django 2.2b1 on 2019-03-19 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Container',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('size_class', models.CharField(max_length=255, unique=True)),
                ('standard', models.BooleanField(blank=True, null=True)),
                ('volume', models.FloatField()),
                ('deposit', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('delivery_fee', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('image_url', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
