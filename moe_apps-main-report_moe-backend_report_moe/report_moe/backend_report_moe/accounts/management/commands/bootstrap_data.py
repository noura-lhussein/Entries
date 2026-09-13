from __future__ import annotations

from config.bootstrap_data import run_bootstrap
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Bootstrap local MOE portal data from bundled files and demo seeds. '
        'Single entry point for auth, GIS, water, projects, oil & gas, and electricity.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-gis',
            action='store_true',
            help='Skip GIS layer imports (admin boundaries, water, geology, electricity shapefiles).',
        )
        parser.add_argument(
            '--with-external-water',
            action='store_true',
            help='Also import rainfall/dam/euphrates data from external DAM_DATA_DIR / RAINFALL_DATA_DIR paths.',
        )
        parser.add_argument(
            '--only',
            type=str,
            default='',
            help='Comma-separated subset: auth, gis, water, projects, oil-gas, electricity.',
        )
        parser.add_argument(
            '--fail-on-missing',
            action='store_true',
            help='Abort when required bundled data files are missing (default: skip optional steps).',
        )

    def handle(self, *args, **options):
        only = [part.strip() for part in options['only'].split(',') if part.strip()]
        counts = run_bootstrap(
            self.stdout,
            include_gis=not options['no_gis'],
            include_external_water=options['with_external_water'],
            only=only or None,
            skip_missing=not options['fail_on_missing'],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrap finished: {counts['ran']} ran, "
                f"{counts['skipped']} skipped, {counts['errors']} errors."
            )
        )
