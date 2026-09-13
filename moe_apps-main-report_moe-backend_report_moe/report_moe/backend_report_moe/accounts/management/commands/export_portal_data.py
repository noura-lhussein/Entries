from __future__ import annotations

import subprocess
from pathlib import Path

from config.data_transfer import DEFAULT_EXPORT_DIR, export_portal_data, table_row_counts
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        'Export all MOE portal database tables (including PostGIS layers) to a portable bundle. '
        'Uses pg_dump; run import_portal_data on the target server to restore.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='',
            help=f'Export bundle directory (default: {DEFAULT_EXPORT_DIR}/moe_portal_<timestamp>).',
        )
        parser.add_argument(
            '--data-only',
            action='store_true',
            help='Export data rows only (use when the target DB schema already exists from migrate).',
        )
        parser.add_argument(
            '--include-ephemeral',
            action='store_true',
            help='Include sessions, JWT blacklist, and admin log tables.',
        )
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='Also archive uploaded files from MEDIA_ROOT.',
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir']).resolve() if options['output_dir'] else None
        try:
            bundle_dir = export_portal_data(
                output_dir,
                data_only=options['data_only'],
                exclude_ephemeral=not options['include_ephemeral'],
                include_media=options['include_media'],
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        except subprocess.CalledProcessError as exc:
            raise CommandError(f'pg_dump failed (exit {exc.returncode}).') from exc

        counts = table_row_counts()
        total_rows = sum(counts.values())
        self.stdout.write(self.style.SUCCESS(f'Export complete: {bundle_dir}'))
        self.stdout.write(f'  Tables: {len(counts)}')
        self.stdout.write(f'  Rows:   {total_rows:,}')
        self.stdout.write('')
        self.stdout.write('Copy the bundle to the target server, then run:')
        self.stdout.write(f'  python manage.py import_portal_data {bundle_dir}')
