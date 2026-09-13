"""
Import fuel stations into `oil_gas_facility` (schema `moeds`).

Ported from moeds `oil_gas/management/commands/import_pos2_fuel_stations.py`. report_moe
is the single writer for oil_gas_facility, so the importer lives here; moeds can only
read it.

The source is a CSV export from the POS2 system. Rows with missing coordinates or outside
Syria's geographic bounds are skipped.

Existing fuel stations are replaced entirely — this is not an upsert, but a full reload.

Usage:
  python manage.py import_pos2_fuel_stations --path facility_*.csv
  python manage.py import_pos2_fuel_stations --path facility_*.csv --apply
"""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from master_data.management.commands.pos2_fuel_stations import (
    DEFAULT_POS2_FACILITY_CSV,
    iter_pos2_fuel_stations,
    pos2_row_to_facility,
)
from master_data.models import OilFacility as Facility


class Command(BaseCommand):
    help = 'Upsert oil-gas fuel stations from a POS2 facility export.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default=str(DEFAULT_POS2_FACILITY_CSV),
            help='Path to facility_*.csv export from POS2.',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Bulk insert batch size.',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write to the database. Without it the command only reports what it would do.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['path'])
        batch_size = max(1, int(options['batch_size']))
        apply = bool(options['apply'])

        try:
            rows = iter_pos2_fuel_stations(csv_path)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        with_coords = sum(1 for row in rows if row.latitude is not None and row.longitude is not None)
        active = sum(1 for row in rows if row.status == Facility.Status.ACTIVE)

        self.stdout.write(
            f'Parsed {len(rows)} fuel stations from {csv_path.name} '
            f'({active} active, {with_coords} with Syria coordinates).'
        )

        if not apply:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY-RUN: would replace {Facility.objects.count()} '
                    f'existing fuel stations with {len(rows)} new ones. Re-run with --apply.'
                )
            )
            return

        with transaction.atomic():
            deleted, _details = Facility.objects.filter(
                facility_type=Facility.FacilityType.FUEL_STATION,
            ).delete()
            self.stdout.write(f'Removed {deleted} existing fuel station record(s).')

            created = 0
            batch: list[Facility] = []
            for row in rows:
                batch.append(pos2_row_to_facility(row))
                if len(batch) >= batch_size:
                    Facility.objects.bulk_create(batch, batch_size=batch_size)
                    created += len(batch)
                    batch.clear()

            if batch:
                Facility.objects.bulk_create(batch, batch_size=batch_size)
                created += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f'APPLIED: imported {created} fuel stations (fuel-stations map layer).')
        )
