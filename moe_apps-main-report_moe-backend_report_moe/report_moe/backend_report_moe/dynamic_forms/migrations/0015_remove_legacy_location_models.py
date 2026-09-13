from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("dynamic_forms", "0014_remove_legacy_submain_district"),
    ]

    operations = [
        migrations.DeleteModel(name="Facility"),
        migrations.DeleteModel(name="Community"),
        migrations.DeleteModel(name="SubDistrict"),
        migrations.DeleteModel(name="District"),
        migrations.DeleteModel(name="City"),
    ]
