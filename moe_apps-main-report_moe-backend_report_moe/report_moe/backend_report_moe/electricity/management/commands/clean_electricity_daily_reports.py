from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from electricity.models import (
    DailyMetric,
    DailyReport,
    FuelTankReading,
    GenerationIncident,
    GenerationUnitReading,
    GovernorateLoad,
    GridLineIncident,
    HydroDamReading,
)

RELATED_COUNTS: tuple[tuple[str, type], ...] = (
    ('DailyMetric', DailyMetric),
    ('GovernorateLoad', GovernorateLoad),
    ('HydroDamReading', HydroDamReading),
    ('GenerationIncident', GenerationIncident),
    ('GridLineIncident', GridLineIncident),
    ('FuelTankReading', FuelTankReading),
    ('GenerationUnitReading', GenerationUnitReading),
)


class Command(BaseCommand):
    help = 'Remove all electricity daily coordination reports and related child rows.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show row counts that would be deleted (default when --confirm is omitted).',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually delete all DailyReport rows (CASCADE to child tables).',
        )

    def handle(self, *args, **options):
        confirm = options['confirm']
        dry_run = options['dry_run'] or not confirm

        counts = self._collect_counts()
        self._print_counts(counts, dry_run=dry_run)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Dry run only — no rows deleted. Re-run with --confirm to apply.',
                ),
            )
            return

        if counts['DailyReport'] == 0:
            self.stdout.write(self.style.SUCCESS('Nothing to delete.'))
            return

        with transaction.atomic():
            deleted_total, deleted_by_model = DailyReport.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {deleted_total} row(s) across {len(deleted_by_model)} table(s).',
            ),
        )
        for label, _model in RELATED_COUNTS:
            remaining = _model.objects.count()
            if remaining:
                raise CommandError(
                    f'Expected 0 {label} rows after cleanup, found {remaining}.')

        if DailyReport.objects.exists():
            raise CommandError('DailyReport rows still exist after cleanup.')

        self.stdout.write(self.style.SUCCESS(
            'Cleanup complete. All daily report tables are empty.'))
        self.stdout.write(
            self.style.WARNING(
                'Executive electricity dashboard APIs will be empty until reports are re-imported.',
            ),
        )

    def _collect_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {'DailyReport': DailyReport.objects.count()}
        for label, model in RELATED_COUNTS:
            counts[label] = model.objects.count()
        return counts

    def _print_counts(self, counts: dict[str, int], *, dry_run: bool) -> None:
        mode = 'Would delete' if dry_run else 'Deleting'
        self.stdout.write(f'{mode}:')
        for label, count in counts.items():
            self.stdout.write(f'  {label}: {count}')
