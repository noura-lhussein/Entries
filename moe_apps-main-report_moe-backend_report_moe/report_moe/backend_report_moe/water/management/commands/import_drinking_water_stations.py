from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from water.drinking_water_import import import_drinking_water_workbook
from water.map_layers import sync_drinking_water_map_layer


class Command(BaseCommand):
    help = 'Import drinking water pumping stations from the مياه الشرب.xlsx workbook.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=str(Path(__file__).resolve().parents[2] / 'data' / 'drinking_water_stations.xlsx'),
            help='Path to the drinking water stations .xlsx file.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing drinking water stations before import.',
        )

    def handle(self, *args, **options):
        path = Path(options['path'])
        if not path.is_file():
            raise CommandError(f'Workbook not found: {path}')

        try:
            stats = import_drinking_water_workbook(path, clear=options['clear'])
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc

        sync_stats = sync_drinking_water_map_layer()

        self.stdout.write(
            self.style.SUCCESS(
                'Drinking water import complete: '
                f"{stats['created']} created, {stats['updated']} updated, {stats['skipped']} skipped. "
                f"Map layer synced: {sync_stats['imported']} features.",
            ),
        )
