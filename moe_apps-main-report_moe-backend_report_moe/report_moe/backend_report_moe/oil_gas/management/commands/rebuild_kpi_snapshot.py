from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from oil_gas.alert_engine import evaluate_alerts
from oil_gas.snapshot_builder import build_kpi_snapshot


class Command(BaseCommand):
    help = 'Rebuild KPI daily snapshot and evaluate alerts for a date.'

    def add_arguments(self, parser):
        parser.add_argument('--date', required=True, help='YYYY-MM-DD')

    def handle(self, *args, **options):
        snapshot_date = date.fromisoformat(options['date'])
        snapshot = build_kpi_snapshot(snapshot_date)
        evaluate_alerts(snapshot_date, snapshot)
        self.stdout.write(self.style.SUCCESS(f'Rebuilt snapshot for {snapshot_date}'))
