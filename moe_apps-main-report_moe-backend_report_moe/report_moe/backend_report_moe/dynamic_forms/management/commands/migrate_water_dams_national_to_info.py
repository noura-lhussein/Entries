"""
Aggregate DamStorageReading into national water Info dam KPIs.

Prereqs:
  python manage.py seed_water_sector_info_forms

Usage:
  python manage.py migrate_water_dams_national_to_info --sub-main-id 20
  python manage.py migrate_water_dams_national_to_info --sub-main-id 20 --apply --year 2024
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[water-dams-national-migration]'
TITLE_NATIONAL = 'مؤشرات قطاع المياه'


def _attrs() -> dict[str, Attribute]:
    title = Title.objects.filter(name=TITLE_NATIONAL).first()
    if title is None:
        raise CommandError('Missing title. Run seed_water_sector_info_forms.')
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return {**by_key, **by_label}


def _create_info(attribute: Attribute, sub: SubMainSection, row_key: uuid.UUID, value: str) -> bool:
    if Info.objects.filter(attribute=attribute, sub_main=sub, row_key=row_key).exists():
        return False
    Info.objects.create(
        attribute=attribute,
        sub_main=sub,
        row_key=row_key,
        value=value,
        confirmed=Info.ConfirmStatus.ACCEPT,
        commit_note=NOTE_TAG,
    )
    return True


class Command(BaseCommand):
    help = 'Migrate dam storage aggregates into national water Info KPIs (dry-run default).'

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

        sql = """
            SELECT reading_date::date AS d,
                   COUNT(DISTINCT dam_id) AS dams,
                   COALESCE(AVG(storage_mcm), 0) AS avg_mcm,
                   COALESCE(SUM(storage_mcm), 0) AS total_mcm
            FROM water_damstoragereading
            WHERE storage_mcm IS NOT NULL
        """
        params: list[Any] = []
        if year > 0:
            sql += ' AND EXTRACT(YEAR FROM reading_date) = %s'
            params.append(year)
        sql += ' GROUP BY reading_date::date ORDER BY d DESC'

        with connections['default'].cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        dams_attr = attrs.get('dams_with_readings')
        avg_attr = attrs.get('dam_storage_avg_mcm')
        total_attr = attrs.get('dam_storage_total_mcm')
        if not date_attr or not dams_attr or not avg_attr:
            raise CommandError('National dam attributes missing. Re-run seed_water_sector_info_forms.')

        created = skipped = 0
        for d, dams, avg_mcm, total_mcm in rows:
            day: date = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
            date_s = day.isoformat()
            # Share row_key namespace with rainfall national so same-day cells can coexist
            # under distinct attribute sets; use dams-specific key to avoid collisions.
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'water-dams-national-{date_s}')
            pairs = [
                (date_attr, date_s),
                (dams_attr, str(int(dams))),
                (avg_attr, str(avg_mcm)),
            ]
            if total_attr is not None:
                pairs.append((total_attr, str(total_mcm)))
            if not apply:
                created += len(pairs)
                continue
            with transaction.atomic():
                for attr, value in pairs:
                    if _create_info(attr, sub, row_key, value):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(f'{mode}: days={len(rows)} created≈{created} skipped≈{skipped}')
        )
