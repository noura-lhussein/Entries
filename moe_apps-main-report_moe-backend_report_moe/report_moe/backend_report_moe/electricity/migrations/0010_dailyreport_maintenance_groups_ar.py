from __future__ import annotations

from django.db import migrations, models
from django.db.models import Q


def migrate_maintenance_units_to_text(apps, schema_editor):
    DailyReport = apps.get_model('electricity', 'DailyReport')
    GenerationUnitReading = apps.get_model('electricity', 'GenerationUnitReading')

    for report in DailyReport.objects.all():
        maintenance_rows = GenerationUnitReading.objects.filter(
            report=report,
        ).filter(
            Q(status='maintenance') | Q(plant_code='maintenance'),
        )
        lines = [
            (row.unit_code or row.plant_code or '').strip()
            for row in maintenance_rows
            if (row.unit_code or row.plant_code or '').strip()
        ]
        if lines and not report.maintenance_groups_ar:
            report.maintenance_groups_ar = '\n'.join(lines)
            report.save(update_fields=['maintenance_groups_ar'])
        maintenance_rows.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0009_executive_dashboard_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyreport',
            name='maintenance_groups_ar',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(migrate_maintenance_units_to_text, migrations.RunPython.noop),
    ]
