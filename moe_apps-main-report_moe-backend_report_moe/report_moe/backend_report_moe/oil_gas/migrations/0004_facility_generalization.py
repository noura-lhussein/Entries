from __future__ import annotations

import re

import django.db.models.deletion
from django.db import migrations, models


def _slug_code(name: str) -> str:
    code = re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')
    return (code or 'facility')[:50]


def _unique_code(Facility, base: str) -> str:
    code = base
    suffix = 1
    while Facility.objects.filter(code=code).exists():
        suffix += 1
        code = f'{base}-{suffix}'[:50]
    return code


def migrate_storage_to_facility(apps, schema_editor):
    Facility = apps.get_model('oil_gas', 'Facility')
    for row in Facility.objects.all():
        name = row.facility_name or f'Facility {row.pk}'
        if not row.name_en:
            row.name_en = name
        if not row.code:
            row.code = _unique_code(Facility, _slug_code(name))
        legacy = (row.facility_type or '').lower()
        if legacy in ('depot', 'storage', 'storage_depot', ''):
            row.facility_type = 'storage_depot'
        elif legacy in ('power_plant', 'power', 'plant'):
            row.facility_type = 'power_plant'
        elif legacy == 'substation':
            row.facility_type = 'substation'
        else:
            row.facility_type = 'storage_depot'
        if not row.sector:
            row.sector = 'oil-gas'
        if not row.status:
            row.status = 'active'
        row.save(update_fields=['code', 'name_en', 'facility_type', 'sector', 'status'])


def migrate_power_station_fk(apps, schema_editor):
    Facility = apps.get_model('oil_gas', 'Facility')
    PowerGasSupply = apps.get_model('oil_gas', 'PowerGasSupply')
    PowerGasRequirement = apps.get_model('oil_gas', 'PowerGasRequirement')

    def get_or_create_power_facility(name: str):
        clean = name.strip()
        existing = Facility.objects.filter(name_en__iexact=clean).first()
        if existing:
            return existing
        code = _unique_code(Facility, _slug_code(clean))
        return Facility.objects.create(
            code=code,
            name_en=clean,
            facility_type='power_plant',
            sector='electricity',
            status='active',
        )

    for row in PowerGasSupply.objects.exclude(power_station=''):
        facility = get_or_create_power_facility(row.power_station)
        row.facility_id = facility.id
        row.save(update_fields=['facility_id'])

    for row in PowerGasRequirement.objects.exclude(power_station=''):
        facility = get_or_create_power_facility(row.power_station)
        row.facility_id = facility.id
        row.save(update_fields=['facility_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('oil_gas', '0003_operationaltarget_audit_and_snapshot_targets'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='StorageFacility',
            new_name='Facility',
        ),
        migrations.AlterModelOptions(
            name='facility',
            options={'ordering': ['name_en'], 'verbose_name_plural': 'facilities'},
        ),
        migrations.AddField(
            model_name='facility',
            name='code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='facility',
            name='name_en',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='facility',
            name='name_ar',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='facility',
            name='governorate',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='facility',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='facility',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='facility',
            name='status',
            field=models.CharField(
                choices=[('active', 'Active'), ('inactive', 'Inactive'), ('maintenance', 'Maintenance')],
                default='active',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='facility',
            name='sector',
            field=models.CharField(
                choices=[('oil-gas', 'Oil & Gas'), ('electricity', 'Electricity')],
                default='oil-gas',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='facility',
            name='design_capacity_mw',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=18, null=True),
        ),
        migrations.RunPython(migrate_storage_to_facility, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='facility',
            name='facility_type',
            field=models.CharField(
                choices=[
                    ('storage_depot', 'Storage depot'),
                    ('power_plant', 'Power plant'),
                    ('substation', 'Substation'),
                ],
                default='storage_depot',
                max_length=50,
            ),
        ),
        migrations.RemoveField(
            model_name='facility',
            name='facility_name',
        ),
        migrations.AlterField(
            model_name='facility',
            name='code',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='facility',
            name='name_en',
            field=models.CharField(max_length=200),
        ),
        migrations.AddField(
            model_name='powergassupply',
            name='facility',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='power_gas_supplies',
                to='oil_gas.facility',
            ),
        ),
        migrations.AddField(
            model_name='powergasrequirement',
            name='facility',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='power_gas_requirements',
                to='oil_gas.facility',
            ),
        ),
        migrations.RunPython(migrate_power_station_fk, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='powergassupply',
            name='oil_gas_unique_power_gas_supply',
        ),
        migrations.RemoveConstraint(
            model_name='powergasrequirement',
            name='oil_gas_unique_power_gas_requirement',
        ),
        migrations.RemoveField(
            model_name='powergassupply',
            name='power_station',
        ),
        migrations.RemoveField(
            model_name='powergasrequirement',
            name='power_station',
        ),
        migrations.AlterField(
            model_name='powergassupply',
            name='facility',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='power_gas_supplies',
                to='oil_gas.facility',
            ),
        ),
        migrations.AlterField(
            model_name='powergasrequirement',
            name='facility',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='power_gas_requirements',
                to='oil_gas.facility',
            ),
        ),
        migrations.AddConstraint(
            model_name='powergassupply',
            constraint=models.UniqueConstraint(
                fields=('supply_date', 'facility'),
                name='oil_gas_unique_power_gas_supply',
            ),
        ),
        migrations.AddConstraint(
            model_name='powergasrequirement',
            constraint=models.UniqueConstraint(
                fields=('facility', 'requirement_date'),
                name='oil_gas_unique_power_gas_requirement',
            ),
        ),
    ]
