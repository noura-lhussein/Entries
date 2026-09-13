from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from oil_gas.models import DailyReport
from oil_gas.services import upsert_metric

EXECUTIVE_REPORT_2026_06_01 = {
    'total_oil_production_bbl': 123_126,
    'total_crude_transferred_bbl': 124_686,
    'local_clean_gas_mm3': 6.663,
    'clean_gas_import_azerbaijan_mm3': 5.318,
    'clean_gas_import_jordan_mm3': 0.991,
    'total_clean_gas_mm3': 12.972,
    'clean_gas_distributed_mm3': 12.614,
    'electricity_clean_gas_consumption_mm3': 11.369,
    'mazut_sold_thu_fri_m3': 8_856,
    'gasoline_90_95_sold_thu_fri_m3': 8_916,
    'domestic_lpg_sold_m3': 2_101,
    'fuel_oil_sold_m3': 6_306,
}


class Command(BaseCommand):
    help = 'Seed executive oil & gas daily report (لوحة النفط والغاز — نظرة تنفيذية).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            default='2026-06-01',
            help='Report date (YYYY-MM-DD).',
        )

    def handle(self, *args, **options):
        report_date = date.fromisoformat(options['date'])
        report, created = DailyReport.objects.update_or_create(
            report_date=report_date,
            defaults={
                'status': DailyReport.Status.PUBLISHED,
                'notes_ar': 'التقرير اليومي لقطاع البترول ومشتقاته — 1/6/2026',
                'notes_en': 'Daily petroleum sector report — 1 Jun 2026',
            },
        )
        report.metrics.filter(metric_key__in=EXECUTIVE_REPORT_2026_06_01).delete()
        for key, value in EXECUTIVE_REPORT_2026_06_01.items():
            upsert_metric(report, key, value)

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            self.style.SUCCESS(f'{action} executive report {report_date} ({len(EXECUTIVE_REPORT_2026_06_01)} metrics).'),
        )
