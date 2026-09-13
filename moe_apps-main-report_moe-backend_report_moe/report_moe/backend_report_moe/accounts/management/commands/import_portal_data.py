from __future__ import annotations

import subprocess
from pathlib import Path

from config.data_transfer import import_portal_data, table_row_counts
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Import a MOE portal data bundle created by export_portal_data. '
        'Restores all tables (including PostGIS layers) via pg_restore.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'bundle_dir',
            type=str,
            help='Path to the export bundle directory (contains manifest.json and database.dump).',
        )
        parser.add_argument(
            '--data-only',
            action='store_true',
            help='Restore data only (schema must already exist from migrate).',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete all existing data first, then restore from the bundle (recommended).',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Drop existing database objects before restore (full restore only; use --replace instead).',
        )
        parser.add_argument(
            '--skip-media',
            action='store_true',
            help='Do not extract media.tar.gz even if present in the bundle.',
        )
        parser.add_argument(
            '--jobs',
            type=int,
            default=4,
            help='Parallel pg_restore workers (default: 4).',
        )

    def handle(self, *args, **options):
        bundle_dir = Path(options['bundle_dir']).resolve()
        if not bundle_dir.is_dir():
            raise CommandError(f'Bundle directory not found: {bundle_dir}')

        try:
            if options['replace']:
                self.stdout.write('Replace mode: existing data will be deleted before restore.')

            manifest = import_portal_data(
                bundle_dir,
                data_only=options['data_only'],
                clean=options['clean'],
                replace=options['replace'],
                include_media=not options['skip_media'],
                jobs=options['jobs'],
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        except subprocess.CalledProcessError as exc:
            raise CommandError(f'pg_restore failed (exit {exc.returncode}).') from exc

        counts = table_row_counts()
        total_rows = sum(counts.values())
        self.stdout.write(self.style.SUCCESS(f'Import complete from {bundle_dir}'))
        self.stdout.write(f'  Source DB: {manifest.database} @ {manifest.host}')
        self.stdout.write(f'  Exported:  {manifest.created_at}')
        self.stdout.write(f'  Tables:    {len(counts)}')
        self.stdout.write(f'  Rows:      {total_rows:,}')
        if manifest.include_media and not options['skip_media']:
            self.stdout.write('  Media:     restored')
