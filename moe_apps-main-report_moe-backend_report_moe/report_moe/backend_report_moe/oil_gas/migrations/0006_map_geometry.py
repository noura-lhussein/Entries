from __future__ import annotations

from decimal import Decimal

from django.db import migrations, models


def seed_map_coordinates(apps, schema_editor):
    Refinery = apps.get_model('oil_gas', 'Refinery')
    Pipeline = apps.get_model('oil_gas', 'Pipeline')
    Facility = apps.get_model('oil_gas', 'Facility')

    refinery_coords = {
        'Homs Refinery': (Decimal('34.731900'), Decimal('36.709800')),
        'Banias Refinery': (Decimal('35.181400'), Decimal('35.948100')),
    }
    for name, (lat, lng) in refinery_coords.items():
        Refinery.objects.filter(refinery_name=name).update(latitude=lat, longitude=lng)

    Pipeline.objects.filter(name='Banias–Homs Crude Line').update(
        source_latitude=Decimal('35.181400'),
        source_longitude=Decimal('35.948100'),
        dest_latitude=Decimal('34.731900'),
        dest_longitude=Decimal('36.709800'),
    )

    Facility.objects.filter(code='homs-strategic-depot').update(
        latitude=Decimal('34.731900'),
        longitude=Decimal('36.709800'),
        governorate='Homs',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0005_rename_oil_gas_oper_scope_idx_oil_gas_ope_scope_t_757fe2_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='refinery',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='refinery',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='dest_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='dest_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='source_latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='pipeline',
            name='source_longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='facility',
            name='facility_type',
            field=models.CharField(
                choices=[
                    ('storage_depot', 'Storage depot'),
                    ('fuel_station', 'Fuel station'),
                    ('power_plant', 'Power plant'),
                    ('substation', 'Substation'),
                ],
                max_length=50,
            ),
        ),
        migrations.RunPython(seed_map_coordinates, migrations.RunPython.noop),
    ]
