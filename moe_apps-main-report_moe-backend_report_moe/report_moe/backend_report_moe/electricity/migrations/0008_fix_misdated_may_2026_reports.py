from __future__ import annotations

from datetime import date

from django.db import migrations

DATE_FIXES = (
    (date(2025, 5, 20), date(2026, 5, 20)),
    (date(2025, 5, 21), date(2026, 5, 21)),
)


def fix_report_dates(apps, schema_editor):
    DailyReport = apps.get_model('electricity', 'DailyReport')
    for old_date, new_date in DATE_FIXES:
        report = DailyReport.objects.filter(report_date=old_date).first()
        if not report:
            continue
        if DailyReport.objects.filter(report_date=new_date).exists():
            report.delete()
            continue
        report.report_date = new_date
        report.save(update_fields=['report_date'])


def revert_report_dates(apps, schema_editor):
    DailyReport = apps.get_model('electricity', 'DailyReport')
    for old_date, new_date in DATE_FIXES:
        report = DailyReport.objects.filter(report_date=new_date).first()
        if not report:
            continue
        if DailyReport.objects.filter(report_date=old_date).exists():
            continue
        report.report_date = old_date
        report.save(update_fields=['report_date'])


class Migration(migrations.Migration):
    dependencies = [
        ('electricity', '0007_fuel_tanks_generation_units'),
    ]

    operations = [
        migrations.RunPython(fix_report_dates, revert_report_dates),
    ]
