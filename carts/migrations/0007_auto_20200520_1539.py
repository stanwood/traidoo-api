# Generated by Django 2.2.10 on 2020-05-20 15:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("carts", "0006_cart_delivery_address"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="cart",
            options={"verbose_name": "Cart", "verbose_name_plural": "Carts"},
        ),
        migrations.AlterModelOptions(
            name="cartitem",
            options={"ordering": ["created_at"], "verbose_name": "Cart item"},
        ),
        migrations.AlterField(
            model_name="cart",
            name="delivery_address",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="delivery_addresses.DeliveryAddress",
                verbose_name="Delivery address",
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="earliest_delivery_date",
            field=models.DateField(
                blank=True, null=True, verbose_name="Earliest delivery date"
            ),
        ),
        migrations.AlterField(
            model_name="cart",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="cart",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="items",
                to="carts.Cart",
                verbose_name="Cart",
            ),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="delivery_option",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="delivery_options.DeliveryOption",
                verbose_name="Delivery option",
            ),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="latest_delivery_date",
            field=models.DateField(verbose_name="Latest delivery date"),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="products.Product",
                verbose_name="Product",
            ),
        ),
        migrations.AlterField(
            model_name="cartitem",
            name="quantity",
            field=models.IntegerField(default=0, verbose_name="Quantity"),
        ),
    ]
