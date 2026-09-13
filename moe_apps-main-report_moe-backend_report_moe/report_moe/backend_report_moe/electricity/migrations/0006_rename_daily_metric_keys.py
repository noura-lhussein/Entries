from __future__ import annotations

from django.db import migrations

METRIC_KEY_RENAMES = {
    'available_capacity_mw': 'available_fuel_quantity',
    'hydro_generation_mwh': 'available_generated_power',
}


def rename_metric_keys(apps, schema_editor):
    DailyMetric = apps.get_model('electricity', 'DailyMetric')
    OperationalTarget = apps.get_model('electricity', 'OperationalTarget')
    for old_key, new_key in METRIC_KEY_RENAMES.items():
        DailyMetric.objects.filter(metric_key=old_key).update(metric_key=new_key)
        OperationalTarget.objects.filter(metric_key=old_key).update(metric_key=new_key)


def revert_metric_keys(apps, schema_editor):
    DailyMetric = apps.get_model('electricity', 'DailyMetric')
    OperationalTarget = apps.get_model('electricity', 'OperationalTarget')
    for old_key, new_key in METRIC_KEY_RENAMES.items():
        DailyMetric.objects.filter(metric_key=new_key).update(metric_key=old_key)
        OperationalTarget.objects.filter(metric_key=new_key).update(metric_key=old_key)


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0005_transmissionline_map_geometry'),
    ]

    operations = [
        migrations.RunPython(rename_metric_keys, revert_metric_keys),
    ]
