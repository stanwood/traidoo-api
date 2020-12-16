# Generated by Django 2.2.15 on 2020-12-15 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_auto_20201102_1308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='unit',
            field=models.CharField(blank=True, choices=[('kg', 'kg'), ('g', 'g'), ('l', 'l'), ('ml', 'ml'), ('Piece', 'Piece'), ('Glass', 'Glass'), ('Net', 'Net'), ('Bundle', 'Bundle'), ('Bottle', 'Bottle')], max_length=10, null=True, verbose_name='Unit'),
        ),
    ]
