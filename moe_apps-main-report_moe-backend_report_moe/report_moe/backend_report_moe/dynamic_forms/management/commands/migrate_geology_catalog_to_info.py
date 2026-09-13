"""
Snapshot geology_info.csv catalog counts into accepted Info KPIs.

Reads CSV from moeds repo path (or --csv). Does not replace GIS map layers.

Usage:
  python manage.py migrate_geology_catalog_to_info --sub-main-id 20
  python manage.py migrate_geology_catalog_to_info --sub-main-id 20 --apply
"""

from __future__ import annotations

import csv
import uuid
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[geology-catalog-migration]'
TITLE_NATIONAL = 'مؤشرات قطاع الجيولوجيا'
# .../report_moe/backend_report_moe/.../commands/file → parents[4]=report_moe → sibling moeds
DEFAULT_CSV = Path(__file__).resolve().parents[4].parent / 'moeds' / 'geology_info.csv'


class Command(BaseCommand):
    help = 'Migrate geology CSV catalog counts into Info (dry-run default).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--csv', type=str, default='')
        parser.add_argument('--date', type=str, default='')

    def handle(self, *args, **options):
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')

        csv_path = Path(options['csv']) if options['csv'] else DEFAULT_CSV
        if not csv_path.is_file():
            raise CommandError(f'CSV not found: {csv_path}')

        title = Title.objects.filter(name=TITLE_NATIONAL).first()
        if title is None:
            raise CommandError('Missing title. Run seed_geology_sector_info_forms.')
        attrs = {a.label: a for a in Attribute.objects.filter(title=title)}
        attrs.update({a.key: a for a in Attribute.objects.filter(title=title) if a.key})

        counts = {'volcanic': 0, 'sedimentary': 0, 'modern': 0, 'total': 0}
        with csv_path.open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                active = str(row.get('is_active') or '').strip().lower() in (
                    '1',
                    'true',
                    't',
                    'yes',
                )
                if not active:
                    continue
                cat = (row.get('category') or '').strip()
                counts['total'] += 1
                if cat in counts:
                    counts[cat] += 1

        date_s = (options['date'] or '').strip() or date.today().isoformat()
        row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'geology-catalog-{date_s}')
        apply = bool(options['apply'])
        pairs = [
            ('تاريخ التقرير', date_s),
            ('geology_catalog_records', str(counts['total'])),
            ('geology_category_volcanic', str(counts['volcanic'])),
            ('geology_category_sedimentary', str(counts['sedimentary'])),
            ('geology_category_modern', str(counts['modern'])),
        ]
        created = skipped = 0
        if not apply:
            self.stdout.write(f'DRY-RUN would write {len(pairs)} cells for {date_s}: {counts}')
            return

        with transaction.atomic():
            for label, value in pairs:
                attr = attrs.get(label)
                if attr is None:
                    continue
                if Info.objects.filter(
                    attribute=attr, sub_main=sub, row_key=row_key
                ).exists():
                    skipped += 1
                    continue
                Info.objects.create(
                    attribute=attr,
                    sub_main=sub,
                    row_key=row_key,
                    value=value,
                    confirmed=Info.ConfirmStatus.ACCEPT,
                    commit_note=NOTE_TAG,
                )
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f'APPLIED: created={created} skipped={skipped} counts={counts}')
        )
