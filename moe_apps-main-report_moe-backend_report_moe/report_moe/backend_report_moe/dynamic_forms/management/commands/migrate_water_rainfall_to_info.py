"""
Aggregate published water RainfallObservation rows into national water Info metrics.

Prereqs:
  python manage.py seed_water_sector_info_forms

Usage:
  python manage.py migrate_water_rainfall_to_info --sub-main-id 20
  python manage.py migrate_water_rainfall_to_info --sub-main-id 20 --apply --year 2024
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[water-rainfall-migration]'
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
    help = 'Migrate rainfall observations into national water Info KPIs (dry-run default).'

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
            SELECT observation_date::date AS d,
                   COUNT(DISTINCT station_id) AS stations,
                   COALESCE(SUM(precipitation_mm), 0) AS total_mm
            FROM water_rainfallobservation
            WHERE precipitation_mm IS NOT NULL
        """
        params: list[Any] = []
        if year > 0:
            sql += ' AND EXTRACT(YEAR FROM observation_date) = %s'
            params.append(year)
        sql += ' GROUP BY observation_date::date ORDER BY d DESC'

        with connections['default'].cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        created = skipped = 0
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        stations_attr = attrs.get('rainfall_stations_reporting')
        total_attr = attrs.get('rainfall_total_mm')
        if not date_attr or not stations_attr or not total_attr:
            raise CommandError('National water attributes missing.')

        for d, stations, total_mm in rows:
            day: date = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
            date_s = day.isoformat()
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'water-rain-national-{date_s}')
            if not apply:
                created += 3
                continue
            with transaction.atomic():
                for attr, value in (
                    (date_attr, date_s),
                    (stations_attr, str(stations)),
                    (total_attr, str(total_mm)),
                ):
                    if _create_info(attr, sub, row_key, value):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(f'{mode}: days={len(rows)} created≈{created} skipped≈{skipped}')
        )
