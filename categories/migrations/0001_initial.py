# Generated by Django 2.2b1 on 2019-03-19 07:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('icon', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('ordering', models.IntegerField(blank=True, null=True)),
                ('default_vat', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='categories.Category')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
