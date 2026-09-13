from django.db import migrations


def clear_storage_location(apps, schema_editor):
    Facility = apps.get_model('oil_gas', 'Facility')
    Facility.objects.filter(facility_type='storage_depot').exclude(location='').update(location='')


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('oil_gas', '0009_rbac_flags_and_drop_pipeline_incident'),
    ]

    operations = [
        migrations.RunPython(clear_storage_location, noop_reverse),
    ]
