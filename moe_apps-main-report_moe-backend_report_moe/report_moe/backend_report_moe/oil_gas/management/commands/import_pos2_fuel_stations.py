from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from oil_gas.operational_models import Facility
from oil_gas.pos2_fuel_stations import (
    DEFAULT_POS2_FACILITY_CSV,
    iter_pos2_fuel_stations,
    pos2_row_to_facility,
)


class Command(BaseCommand):
    help = 'Replace oil-gas fuel stations with POS2 facility export (محطات الوقود map layer).'

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
            '--dry-run',
            action='store_true',
            help='Parse and report counts without writing to the database.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['path'])
        batch_size = max(1, int(options['batch_size']))
        dry_run = bool(options['dry_run'])

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

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run — no database changes made.'))
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

        self.stdout.write(self.style.SUCCESS(f'Imported {created} fuel stations for oil-fuel-stations map layer.'))
