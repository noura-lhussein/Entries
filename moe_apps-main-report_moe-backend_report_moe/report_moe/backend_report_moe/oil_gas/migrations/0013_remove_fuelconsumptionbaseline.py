from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0012_remove_facility_design_capacity_mw'),
    ]

    operations = [
        migrations.DeleteModel(
            name='FuelConsumptionBaseline',
        ),
    ]
