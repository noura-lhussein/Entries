"""
Migrate RainfallObservation rows into entity Info title «تحديث رصد الهطول».

Prereqs:
  python manage.py seed_water_entity_pilot_forms
  python manage.py seed_water_sector_info_forms

Usage:
  python manage.py migrate_water_rainfall_entity_to_info --sub-main-id 20 --user 1 --year 2024
  python manage.py migrate_water_rainfall_entity_to_info --sub-main-id 20 --user 1 --year 2024 --apply
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.info_confirmation import ACCEPT
from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[water-rainfall-entity-migration]'
TITLE_NAME = 'تحديث رصد الهطول'
ENTITY_TYPE = 'rainfall_station'


class Command(BaseCommand):
    help = 'Migrate rainfall observations into entity Info (dry-run default).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--user', type=int, required=True)
        parser.add_argument('--year', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--limit', type=int, default=0, help='Max logical rows (0=all).')

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(pk=options['user']).first()
        if user is None:
            raise CommandError(f'User {options["user"]} not found.')
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')

        title = Title.objects.filter(name=TITLE_NAME).first()
        if title is None:
            raise CommandError(f'Missing title {TITLE_NAME}. Run seed_water_entity_pilot_forms.')

        by_type: dict[str, Attribute] = {}
        for attr in Attribute.objects.filter(title=title):
            by_type.setdefault(attr.type, attr)
        entity_attr = by_type.get('rainfall_station')
        date_attr = by_type.get('date')
        number_attr = by_type.get('number')
        if not entity_attr or not date_attr or not number_attr:
            raise CommandError('Rainfall entity attributes missing.')

        year = int(options['year'])
        limit = int(options['limit'] or 0)
        apply = bool(options['apply'])

        sql = """
            SELECT station_id, observation_date::date, precipitation_mm
            FROM water_rainfallobservation
            WHERE precipitation_mm IS NOT NULL
              AND EXTRACT(YEAR FROM observation_date) = %s
            ORDER BY observation_date DESC, station_id
        """
        params: list[Any] = [year]
        if limit > 0:
            sql += ' LIMIT %s'
            params.append(limit)

        with connections['default'].cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        # Existing (entity_id, date) from accepted date cells
        existing: set[tuple[int, str]] = set()
        for eid, val in (
            Info.objects.filter(
                attribute=date_attr,
                confirmed=ACCEPT,
                entity_type=ENTITY_TYPE,
                entity_id__isnull=False,
            )
            .exclude(value='')
            .values_list('entity_id', 'value')
            .iterator(chunk_size=2000)
        ):
            existing.add((int(eid), str(val).strip()[:10]))

        created = skipped = 0
        for station_id, obs_date, precip in rows:
            day: date = obs_date if isinstance(obs_date, date) else date.fromisoformat(str(obs_date)[:10])
            date_s = day.isoformat()
            key = (int(station_id), date_s)
            if key in existing:
                skipped += 1
                continue
            if not apply:
                created += 1
                existing.add(key)
                continue
            row_key = uuid.uuid5(
                uuid.NAMESPACE_URL,
                f'water-rain-entity-{station_id}-{date_s}',
            )
            with transaction.atomic():
                for attr, value in (
                    (entity_attr, str(station_id)),
                    (date_attr, date_s),
                    (number_attr, str(precip)),
                ):
                    if Info.objects.filter(
                        attribute=attr, sub_main=sub, row_key=row_key
                    ).exists():
                        continue
                    Info.objects.create(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        user=user,
                        value=value,
                        confirmed=ACCEPT,
                        entity_type=ENTITY_TYPE,
                        entity_id=int(station_id),
                        commit_note=NOTE_TAG,
                    )
            existing.add(key)
            created += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}: rows={len(rows)} created_logical={created} skipped={skipped}'
            )
        )
