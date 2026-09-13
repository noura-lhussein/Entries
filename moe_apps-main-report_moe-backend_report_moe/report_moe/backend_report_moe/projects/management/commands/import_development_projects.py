from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from projects.csv_loader import DEFAULT_DEVELOPMENT_PROJECT_CSV, load_development_projects_csv


class Command(BaseCommand):
    help = 'Import development projects from development_project.csv into PostGIS/PostgreSQL.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default=str(DEFAULT_DEVELOPMENT_PROJECT_CSV),
            help='Path to development_project.csv',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing development projects before import.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        if not csv_path.is_file():
            raise CommandError(f'CSV file not found: {csv_path}')

        if options['clear']:
            from projects.models import DevelopmentProject

            deleted, _ = DevelopmentProject.objects.all().delete()
            self.stdout.write(f'Cleared {deleted} existing project row(s).')

        try:
            stats = load_development_projects_csv(csv_path)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                'Imported development projects: '
                f"{stats['created']} created, {stats['updated']} updated, "
                f"{stats['skipped']} skipped ({stats['total_rows']} CSV rows).",
            ),
        )
