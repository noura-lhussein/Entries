from __future__ import annotations

from config.data_transfer import clear_media, clear_portal_data, table_row_counts, tables_to_clear
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Delete all MOE portal application data while keeping the database schema.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-media',
            action='store_true',
            help='Also delete uploaded files from MEDIA_ROOT.',
        )
        parser.add_argument(
            '--include-migrations',
            action='store_true',
            help='Also truncate django_migrations (not recommended).',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help=(
                'Override the safety guards: allows running with DJANGO_DEBUG=False and '
                'when CASCADE would reach tables owned by report_moe.'
            ),
        )

    def handle(self, *args, **options):
        tables = tables_to_clear(keep_migrations=not options['include_migrations'])
        self.stdout.write(f'Clearing {len(tables)} tables…')
        try:
            clear_portal_data(
                keep_migrations=not options['include_migrations'],
                force=options['force'],
            )
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        if options['include_media']:
            clear_media()
            self.stdout.write('Media files deleted.')

        counts = table_row_counts()
        remaining = sum(counts.values())
        self.stdout.write(self.style.SUCCESS('All application data deleted.'))
        self.stdout.write(f'  Remaining rows: {remaining:,}')
