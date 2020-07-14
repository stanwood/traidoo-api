from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_auto_20200522_1329"),
    ]

    operations = [
        migrations.RunSQL(sql="DROP TABLE IF EXISTS reversion_revision CASCADE "),
        migrations.RunSQL(sql="DROP TABLE IF EXISTS reversion_version CASCADE"),
    ]
