# Generated by Django 2.2.4 on 2020-02-05 06:44

from django.db import migrations, models
import django.db.models.deletion


def apply_region(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    RegionModel = apps.get_model("common", "Region")
    region, _ = RegionModel.objects.using(db_alias).get_or_create(name="mcswiss")

    UserModel = apps.get_model('users', 'User')
    UserModel.objects.using(db_alias).update(region=region)


def unapply_region(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('users', '0010_auto_20200114_0929'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='region',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='users', to='common.Region'),
        ),
        migrations.RunPython(apply_region, reverse_code=unapply_region)
    ]
