"""
Snapshot DrinkingWaterStation operational counts into national water Info,
and per-station working status into «تحديث محطات مياه الشرب».

Prereqs:
  python manage.py seed_drinking_station_pilot_form
  python manage.py seed_water_sector_info_forms

Usage:
  python manage.py migrate_drinking_stations_to_info --sub-main-id 20 --user 1
  python manage.py migrate_drinking_stations_to_info --sub-main-id 20 --user 1 --apply
"""

from __future__ import annotations

import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.info_confirmation import ACCEPT
from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[drinking-stations-migration]'
TITLE_NATIONAL_CODE = 'water.national'
TITLE_ENTITY_CODE = 'water.drinking_station_entity'
ENTITY_TYPE = 'drinking_station'

# station-table column -> Attribute.key. Boolean columns are stringified as
# 'true'/'false'/'' (NULL); everything else is passed through as text.
STATION_COLUMNS = [
    'is_operational', 'non_operational_reason', 'is_boosting_station',
    'is_well_station', 'is_filtration_station', 'needs_solar_power',
    'has_grid_power', 'building_condition', 'safety_procedures',
    'previously_rehabilitated', 'rehabilitation_type',
    'has_water_hammer_protection', 'water_hammer_efficiency',
    'has_public_grid_supply', 'grid_connection_working',
    'electrical_connection_efficiency', 'electrical_panel_efficiency',
    'transformer_efficiency', 'solar_power_available',
    'solar_system_efficiency', 'needs_solar_installation',
    'generator_available', 'alternative_power_source',
    'solar_space_available', 'grid_power_productivity',
    'solar_power_productivity', 'is_water_analyzed',
    'lab_equipment_status', 'has_water_tanks',
]
BOOLEAN_COLUMNS = {
    'is_operational', 'is_boosting_station', 'is_well_station',
    'is_filtration_station', 'needs_solar_power', 'has_grid_power',
    'previously_rehabilitated', 'has_water_hammer_protection',
    'has_public_grid_supply', 'grid_connection_working',
    'solar_power_available', 'needs_solar_installation',
    'generator_available', 'alternative_power_source',
    'solar_space_available', 'is_water_analyzed', 'has_water_tanks',
}


class Command(BaseCommand):
    help = 'Migrate drinking-station snapshot KPIs/status into Info (dry-run default).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--user', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument(
            '--date',
            type=str,
            default='',
            help='Snapshot report date (YYYY-MM-DD). Default: today.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        user = User.objects.filter(pk=options['user']).first()
        if user is None:
            raise CommandError(f'User {options["user"]} not found.')
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')
        apply = bool(options['apply'])
        date_s = (options['date'] or '').strip() or date.today().isoformat()

        national = Title.objects.filter(code=TITLE_NATIONAL_CODE).first()
        entity_title = Title.objects.filter(code=TITLE_ENTITY_CODE).first()
        if national is None or entity_title is None:
            raise CommandError('Missing titles. Run drinking + water sector seeds.')

        nat_attrs = {a.key: a for a in Attribute.objects.filter(title=national) if a.key}
        date_attr = nat_attrs.get('report_date')
        total_attr = nat_attrs.get('drinking_stations_total')
        op_attr = nat_attrs.get('drinking_stations_operational')
        if not date_attr or not total_attr or not op_attr:
            raise CommandError('National drinking attributes missing. Re-seed sector forms.')

        ent_by_key: dict[str, Attribute] = {
            a.key: a for a in Attribute.objects.filter(title=entity_title) if a.key
        }
        ent_entity = ent_by_key.get('drinking_station')
        ent_date = ent_by_key.get('assessment_date')
        if not ent_entity or not ent_date:
            raise CommandError('Drinking entity attributes missing. Re-seed drinking pilot form.')
        missing_cols = [c for c in STATION_COLUMNS if c not in ent_by_key]
        if missing_cols:
            raise CommandError(f'Missing entity attribute keys: {missing_cols}')

        columns_sql = ', '.join(STATION_COLUMNS)
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*),
                       COUNT(*) FILTER (WHERE is_operational IS TRUE)
                FROM water_drinkingwaterstation
                """
            )
            total, operational = cursor.fetchone()
            cursor.execute(
                f"""
                SELECT id, {columns_sql}
                FROM water_drinkingwaterstation
                ORDER BY id
                """
            )
            stations = cursor.fetchall()

        created = skipped = 0
        row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'drinking-national-{date_s}')
        pairs = [
            (date_attr, date_s),
            (total_attr, str(int(total or 0))),
            (op_attr, str(int(operational or 0))),
        ]
        if apply:
            with transaction.atomic():
                for attr, value in pairs:
                    if Info.objects.filter(attribute=attr, sub_main=sub, row_key=row_key).exists():
                        skipped += 1
                        continue
                    Info.objects.create(
                        attribute=attr,
                        sub_main=sub,
                        row_key=row_key,
                        value=value,
                        confirmed=ACCEPT,
                        commit_note=NOTE_TAG,
                    )
                    created += 1
        else:
            created += len(pairs)

        for row in stations:
            station_id = row[0]
            col_values = dict(zip(STATION_COLUMNS, row[1:]))
            ek = uuid.uuid5(uuid.NAMESPACE_URL, f'drinking-entity-{station_id}-{date_s}')
            cells = [(ent_entity, str(station_id)), (ent_date, date_s)]
            for col, raw in col_values.items():
                if raw is None:
                    continue
                if col in BOOLEAN_COLUMNS:
                    value = 'true' if raw else 'false'
                else:
                    value = str(raw).strip()
                    if not value:
                        continue
                cells.append((ent_by_key[col], value))
            if not apply:
                created += 1
                continue
            if Info.objects.filter(
                attribute=ent_date,
                entity_type=ENTITY_TYPE,
                entity_id=station_id,
                value=date_s,
                confirmed=ACCEPT,
            ).exists():
                skipped += 1
                continue
            with transaction.atomic():
                for attr, value in cells:
                    if Info.objects.filter(attribute=attr, sub_main=sub, row_key=ek).exists():
                        continue
                    Info.objects.create(
                        attribute=attr,
                        sub_main=sub,
                        row_key=ek,
                        user=user,
                        value=value,
                        confirmed=ACCEPT,
                        entity_type=ENTITY_TYPE,
                        entity_id=int(station_id),
                        commit_note=NOTE_TAG,
                    )
            created += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode}: national total={total} operational={operational} '
                f'stations={len(stations)} created≈{created} skipped≈{skipped}'
            )
        )
