"""
Migrate EuphratesCascadeReading rows into accepted Info «مؤشرات سلسلة الفرات».

Prereqs:
  python manage.py seed_euphrates_cascade_info_forms
  python manage.py seed_water_sector_info_forms

Usage:
  python manage.py migrate_euphrates_to_info --sub-main-id 20
  python manage.py migrate_euphrates_to_info --sub-main-id 20 --apply [--year 2024]
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[euphrates-cascade-migration]'
TITLE_NAME = 'مؤشرات سلسلة الفرات'
METRIC_KEYS = (
    'inflow_jarabulus',
    'tishreen_level_m',
    'tishreen_storage_mcm',
    'tishreen_outflow',
    'tishreen_generation_mwh',
    'furat_level_m',
    'furat_storage_mcm',
    'furat_outflow',
    'furat_generation_mwh',
    'kadiran_outflow',
    'kadiran_generation_mwh',
    'al_jalab_discharge',
    'total_generation_mwh',
)


def _attrs() -> dict[str, Attribute]:
    title = Title.objects.filter(name=TITLE_NAME).first()
    if title is None:
        raise CommandError('Missing title. Run seed_euphrates_cascade_info_forms.')
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return {**by_key, **by_label}


def _create(attr: Attribute, sub: SubMainSection, row_key: uuid.UUID, value: str) -> bool:
    if Info.objects.filter(attribute=attr, sub_main=sub, row_key=row_key).exists():
        return False
    Info.objects.create(
        attribute=attr,
        sub_main=sub,
        row_key=row_key,
        value=value,
        confirmed=Info.ConfirmStatus.ACCEPT,
        commit_note=NOTE_TAG,
    )
    return True


class Command(BaseCommand):
    help = 'Migrate Euphrates cascade readings into Info (dry-run default).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--year', type=int, default=0)

    def handle(self, *args, **options):
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')
        apply = bool(options['apply'])
        year = int(options['year'] or 0)
        attrs = _attrs()
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        if date_attr is None:
            raise CommandError('Date attribute missing on Euphrates title.')

        cols = ', '.join(METRIC_KEYS)
        sql = f"""
            SELECT reading_date::date, report_label, {cols}
            FROM water_euphratescascadereading
            WHERE 1=1
        """
        params: list[Any] = []
        if year > 0:
            sql += ' AND EXTRACT(YEAR FROM reading_date) = %s'
            params.append(year)
        sql += ' ORDER BY reading_date DESC'

        with connections['default'].cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        label_attr = attrs.get('report_label')
        created = skipped = 0
        for row in rows:
            day = row[0] if isinstance(row[0], date) else date.fromisoformat(str(row[0])[:10])
            date_s = day.isoformat()
            report_label = str(row[1] or '')
            values = row[2:]
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'euphrates-cascade-{date_s}')
            pairs: list[tuple[Attribute, str]] = [(date_attr, date_s)]
            if label_attr is not None and report_label:
                pairs.append((label_attr, report_label))
            for key, raw in zip(METRIC_KEYS, values, strict=True):
                attr = attrs.get(key)
                if attr is None or raw is None:
                    continue
                pairs.append((attr, str(raw)))
            if not apply:
                created += len(pairs)
                continue
            with transaction.atomic():
                for attr, value in pairs:
                    if _create(attr, sub, row_key, value):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(f'{mode}: days={len(rows)} created≈{created} skipped≈{skipped}')
        )
