from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from oil_gas.models import DailyReport
from oil_gas.services import upsert_metric


def _apply_day_metrics(report: DailyReport, day_index: int) -> None:
    """Seed metrics; day_index 0 = anchor report (2026-03-25)."""
    drift = Decimal(str(day_index))
    scale = Decimal('1') + (drift * Decimal('0.02'))

    kpis = {
        'crude_cumulative_bbl': 472000 + day_index * 8500,
        'crude_transfer_daily_bbl': 10469 + day_index * 120,
        'crude_transfer_mtd_bbl': 232626 + day_index * 4200,
        'catalytic_load_homs_t': 2085 + day_index * 35,
        'catalytic_load_banias_t': 12093 + day_index * 180,
        'domestic_gas_index': 48,
        'gas_import_azerbaijan_k_m3d': 3383 - day_index * 12,
        'reserve_days_network': 182 - day_index,
        'units_operating': 0 if day_index < 2 else min(day_index, 3),
        'units_under_repair': 110 - day_index * 2,
        'gas_production_k_m3': 4200 + day_index * 45,
    }
    for key, value in kpis.items():
        upsert_metric(report, key, value)

    homs_products = {
        'product_gasoline_t': 0,
        'product_mazut_t': 0,
        'product_fuel_oil_t': 1322,
        'product_vgo_t': 305,
        'product_residue_t': 69995,
        'product_crude_adequacy_t': 841,
    }
    banias_products = {
        'product_gasoline_t': 2166,
        'product_mazut_t': 4565,
        'product_fuel_oil_t': 4884,
        'product_vgo_t': 152,
        'product_residue_t': 74801,
        'product_crude_adequacy_t': 0,
    }
    for key, value in homs_products.items():
        upsert_metric(report, key, int(Decimal(value) * scale), 'homs')
    for key, value in banias_products.items():
        upsert_metric(report, key, int(Decimal(value) * scale), 'banias')

    distribution = {
        'jinder': (3160, 5),
        'tartous': (2374, 10),
        'aleppo': (227910, 12),
        'banias': (5928, 216),
        'homs': (28234, 29),
        'damascus': (69768, 11028),
    }
    for region, (tonnes, days) in distribution.items():
        upsert_metric(report, 'dist_tonnes', tonnes + day_index * 40, region)
        upsert_metric(report, 'dist_reserve_days', max(days - day_index, 1), region)


class Command(BaseCommand):
    help = 'Seed daily oil & gas production reports for dashboard and trends.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--anchor-date',
            type=str,
            default='2026-03-25',
            help='Anchor report date (YYYY-MM-DD).',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=14,
            help='Number of consecutive daily reports to seed.',
        )

    def handle(self, *args, **options):
        anchor = date.fromisoformat(options['anchor_date'])
        days = options['days']

        for offset in range(days - 1, -1, -1):
            report_date = anchor - timedelta(days=offset)
            day_index = days - 1 - offset
            report, created = DailyReport.objects.update_or_create(
                report_date=report_date,
                defaults={
                    'status': DailyReport.Status.PUBLISHED,
                    'notes_ar': (
                        'تقرير إنتاج يومي — بيانات توضيحية من تقرير 25/3/2026'
                        if day_index == days - 1
                        else ''
                    ),
                    'notes_en': (
                        'Daily production report — seeded from 25 Mar 2026 ministry report'
                        if day_index == days - 1
                        else ''
                    ),
                },
            )
            report.metrics.all().delete()
            _apply_day_metrics(report, day_index)
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} report {report_date}'))

        self.stdout.write(self.style.SUCCESS(f'Seeded {days} daily reports ending {anchor}.'))
