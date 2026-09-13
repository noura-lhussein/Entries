"""
Remove duplicate Info rows sharing (attribute, row_key), keeping the earliest.

A duplicate group here = same (attribute_id, row_key) — the pair a planned
UniqueConstraint(attribute, row_key) will enforce going forward. This is a
different notion of "duplicate" from `dedupe_infos` (which groups by identical
value/confirmed/user/sub_main and ignores row_key entirely): this command
targets rows from the same logical submission that got inserted twice, most
likely by re-running a migrate/import command that didn't check for an
existing row first.

Refuses to touch any group whose members disagree on `value` or `confirmed`
— that would mean the "duplicate" rows actually carry different information,
which is not a safe automatic delete and needs a human decision instead.

Safe by default: prints what would be deleted. Pass --apply to delete.

Usage:
  python manage.py dedupe_infos_by_row_key
  python manage.py dedupe_infos_by_row_key --apply
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Min

from dynamic_forms.models import Info


class Command(BaseCommand):
    help = (
        'Delete duplicate Info rows sharing (attribute, row_key), keeping the '
        'earliest per group. Skips any group where value/confirmed disagree.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually delete duplicates (default is a dry run).',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        groups = (
            Info.objects.filter(row_key__isnull=False)
            .values('attribute_id', 'row_key')
            .annotate(n=Count('id'), keep_id=Min('id'))
            .filter(n__gt=1)
        )

        group_count = groups.count()
        ids_to_delete: list[int] = []
        skipped_groups: list[tuple[int, str]] = []

        for g in groups:
            rows = list(
                Info.objects.filter(
                    attribute_id=g['attribute_id'], row_key=g['row_key'],
                ).values('id', 'value', 'confirmed')
            )
            distinct_values = {r['value'] for r in rows}
            distinct_confirmed = {r['confirmed'] for r in rows}
            if len(distinct_values) > 1 or len(distinct_confirmed) > 1:
                skipped_groups.append((g['attribute_id'], str(g['row_key'])))
                continue
            ids_to_delete.extend(
                r['id'] for r in rows if r['id'] != g['keep_id']
            )

        total = Info.objects.count()
        self.stdout.write(f'Total Info rows: {total}')
        self.stdout.write(f'Duplicate (attribute, row_key) groups: {group_count}')
        self.stdout.write(f'Rows to remove (keeping earliest): {len(ids_to_delete)}')
        if skipped_groups:
            self.stdout.write(
                self.style.WARNING(
                    f'Skipped {len(skipped_groups)} group(s) with disagreeing '
                    f'value/confirmed — needs a human decision, not auto-deleted:'
                )
            )
            for attr_id, row_key in skipped_groups[:20]:
                self.stdout.write(f'  attribute_id={attr_id} row_key={row_key}')
            if len(skipped_groups) > 20:
                self.stdout.write(f'  ... and {len(skipped_groups) - 20} more')

        if not ids_to_delete:
            self.stdout.write('Nothing to clean.')
            return

        if not apply_changes:
            self.stdout.write('Dry run only. Re-run with --apply to delete the rows above.')
            return

        with transaction.atomic():
            deleted, _ = Info.objects.filter(id__in=ids_to_delete).delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted} duplicate rows.'))
