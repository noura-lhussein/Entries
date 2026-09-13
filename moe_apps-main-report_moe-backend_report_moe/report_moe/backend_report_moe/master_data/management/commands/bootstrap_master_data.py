"""
Bootstrap master catalog tables for all sectors (water, oil & gas, electricity, projects).

This command seeds report_moe's writable copy of the master/catalog tables in schema `moeds`.
It must be run separately from moeds' bootstrap_data, which focuses on operational tables.

Usage:
  python manage.py bootstrap_master_data
"""

from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Bootstrap all master/catalog tables in schema moeds.'

    def handle(self, *args, **options):
        commands = [
            ('seed_minister_ops', 'Oil & gas fields, refineries, pipelines, fuel stations', {}),
            ('seed_electricity_daily_catalogs', 'Electricity fuel tanks, hydro dams, load governorates', {}),
            ('seed_project_catalogs', 'Project governorates and organizations', {}),
            ('import_drinking_stations_master', 'Drinking water stations', {'apply': True}),
            ('import_pos2_fuel_stations', 'POS2 fuel stations', {'apply': True}),
        ]

        for cmd, label, kwargs in commands:
            self.stdout.write(f'Seeding {label}...')
            try:
                call_command(cmd, **kwargs)
                self.stdout.write(self.style.SUCCESS(f'  ✓ {label}'))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'  ✗ {label}: {exc}'))

        self.stdout.write(
            self.style.SUCCESS(
                '\nMaster data bootstrap complete. '
                'Run moeds bootstrap_data separately for operational tables.'
            )
        )
