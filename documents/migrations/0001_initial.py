# Generated by Django 2.2b1 on 2019-03-19 07:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_type', models.CharField(choices=[('Platform Invoice', 'documents/invoice_platform.html'), ('Logistics Invoice', 'documents/invoice_logistics.html'), ('Producer Invoice', 'documents/invoice_producer.html'), ('Order Confirmation Buyer', 'documents/order_confirmation_buyer.html'), ('Delivery Overview Buyer', 'documents/delivery_overview_buyer.html'), ('Delivery Overview Seller', 'documents/producer_delivery_note.html'), ('Receipt Buyer', 'documents/buyer_payment_receipt.html')], max_length=64)),
                ('buyer', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('seller', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('delivery_address', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('lines', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('blob_name', models.CharField(blank=True, max_length=128, null=True)),
                ('payment_reference', models.CharField(blank=True, max_length=64, null=True)),
                ('mangopay_payin_id', models.CharField(blank=True, max_length=64, null=True)),
                ('bank_account_owner', models.CharField(blank=True, default='MANGOPAY SA', max_length=128, null=True)),
                ('paid', models.BooleanField(default=False)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.Order')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
