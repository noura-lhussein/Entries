"""
Generic import channel documentation / wrapper for sector daily data → Info.

Pending value: Info.ConfirmStatus.WAITING (not ACCEPT). Use --pending to write
WAITING; omit --pending to write ACCEPT (migration-style). Default is dry-run.

Specialized PDF importers should use Form Builder Excel import for structured
Titles (Title excel-import API). This command is for SQL backfills
and channel documentation.

Usage:
  python manage.py import_sector_daily_to_info --sector water --sub-main-id 20
  python manage.py import_sector_daily_to_info --sector water --channel rainfall \\
      --sub-main-id 20 --apply --pending
  python manage.py import_sector_daily_to_info --sector electricity \\
      --source-file report.xlsx --sub-main-id 15 --title-name "..." --dry-run
"""

from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[sector-daily-import]'

WATER_NATIONAL = 'مؤشرات قطاع المياه'
EUPHRATES_TITLE = 'مؤشرات سلسلة الفرات'
EUPHRATES_KEYS = (
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


def _confirm_status(*, pending: bool) -> str:
    # WAITING = not yet reviewed; ACCEPT = published to dashboards.
    return Info.ConfirmStatus.WAITING if pending else Info.ConfirmStatus.ACCEPT


def _attrs_for_title(title_name: str) -> dict[str, Attribute]:
    title = Title.objects.filter(name=title_name).first()
    if title is None:
        raise CommandError(f'Missing title: {title_name}')
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return {**by_key, **by_label}


def _create_info(
    attribute: Attribute,
    sub: SubMainSection,
    row_key: uuid.UUID,
    value: str,
    *,
    confirmed: str,
) -> bool:
    if Info.objects.filter(attribute=attribute, sub_main=sub, row_key=row_key).exists():
        return False
    Info.objects.create(
        attribute=attribute,
        sub_main=sub,
        row_key=row_key,
        value=value,
        confirmed=confirmed,
        commit_note=NOTE_TAG,
    )
    return True


class Command(BaseCommand):
    help = (
        'Import / document sector daily channels into Info (dry-run default). '
        'ConfirmStatus.WAITING when --pending; else ACCEPT. '
        'For structured PDF/xlsx titles prefer Form Builder Excel import API. '
        'Water channels reuse migrate_water_* / migrate_euphrates SQL patterns.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--sector',
            required=True,
            choices=('electricity', 'oil_gas', 'water'),
        )
        parser.add_argument('--source-file', default='', help='Optional path (xlsx/pdf) for stubs')
        parser.add_argument('--sub-main-id', type=int, default=0)
        parser.add_argument(
            '--title-name',
            default='',
            help='Override Title.name (default: sector national title)',
        )
        parser.add_argument(
            '--channel',
            default='rainfall',
            choices=('rainfall', 'dams', 'euphrates', 'file'),
            help='Water SQL channel, or file for electricity/oil_gas stubs',
        )
        parser.add_argument('--year', type=int, default=0)
        parser.add_argument(
            '--pending',
            action='store_true',
            help='Write confirmed=WAITING (not ACCEPT). Dashboards ignore WAITING.',
        )
        parser.add_argument('--apply', action='store_true', help='Persist Info rows')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Explicit dry-run (default when --apply is omitted)',
        )

    def handle(self, *args, **options):
        sector = options['sector']
        apply = bool(options['apply']) and not bool(options['dry_run'])
        pending = bool(options['pending'])
        confirmed = _confirm_status(pending=pending)
        source = (options.get('source_file') or '').strip()
        sub_main_id = int(options.get('sub_main_id') or 0)
        title_name = (options.get('title_name') or '').strip()
        channel = options['channel']
        year = int(options.get('year') or 0)

        self.stdout.write(
            'NOTE: Specialized PDF importers should use Form Builder Excel '
            'import for structured Titles (Title excel-import API).'
        )
        self.stdout.write(
            f'ConfirmStatus target: {confirmed} '
            f'({"WAITING=pending review" if pending else "ACCEPT=dashboard-ready"})'
        )

        if sector in ('electricity', 'oil_gas') or channel == 'file':
            self._handle_file_stub(sector, source, apply)
            return

        if sector != 'water':
            raise CommandError(f'Unsupported sector/channel: {sector}/{channel}')

        if sub_main_id <= 0:
            raise CommandError('--sub-main-id is required for water SQL channels.')
        sub = SubMainSection.objects.filter(pk=sub_main_id).first()
        if sub is None:
            raise CommandError(f'SubMainSection {sub_main_id} not found.')

        if channel == 'rainfall':
            self._import_water_rainfall(sub, title_name or WATER_NATIONAL, year, apply, confirmed)
        elif channel == 'dams':
            self._import_water_dams(sub, title_name or WATER_NATIONAL, year, apply, confirmed)
        elif channel == 'euphrates':
            self._import_euphrates(sub, title_name or EUPHRATES_TITLE, year, apply, confirmed)
        else:
            raise CommandError(f'Unknown water channel: {channel}')

    def _handle_file_stub(self, sector: str, source: str, apply: bool) -> None:
        if not source:
            self.stdout.write(
                self.style.WARNING(
                    f'{sector}: no --source-file. Use '
                    f'import_{sector}_report_file_to_info or Form Builder Excel import.'
                )
            )
            return
        path = Path(source)
        if not path.exists():
            raise CommandError(f'Source file not found: {path}')
        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            f'{mode}: {sector} file={path} — PDF/xlsx→Info mapping must use the '
            f'seeded national title. Prefer import_{sector}_report_file_to_info '
            f'or Form Builder Excel import. apply={apply} (this wrapper does not write).'
        )

    def _import_water_rainfall(
        self,
        sub: SubMainSection,
        title_name: str,
        year: int,
        apply: bool,
        confirmed: str,
    ) -> None:
        attrs = _attrs_for_title(title_name)
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        stations_attr = attrs.get('rainfall_stations_reporting')
        total_attr = attrs.get('rainfall_total_mm')
        if not date_attr or not stations_attr or not total_attr:
            raise CommandError('National water rainfall attributes missing.')

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
        for d, stations, total_mm in rows:
            day: date = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
            date_s = day.isoformat()
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'water-rain-import-{date_s}')
            if not apply:
                created += 3
                continue
            with transaction.atomic():
                for attr, value in (
                    (date_attr, date_s),
                    (stations_attr, str(stations)),
                    (total_attr, str(total_mm)),
                ):
                    if _create_info(attr, sub, row_key, value, confirmed=confirmed):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode} water/rainfall: days={len(rows)} created≈{created} '
                f'skipped≈{skipped} confirmed={confirmed}'
            )
        )

    def _import_water_dams(
        self,
        sub: SubMainSection,
        title_name: str,
        year: int,
        apply: bool,
        confirmed: str,
    ) -> None:
        attrs = _attrs_for_title(title_name)
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        storage_attr = attrs.get('dam_storage_total_mcm') or attrs.get('total_dam_storage_mcm')
        # 'dams_with_readings' is the actual key seed_water_sector_info_forms.py
        # assigns (see NATIONAL_METRICS there) — the two candidates that used to
        # be here alone ('dams_reporting'/'dam_stations_reporting') never
        # matched anything, so this field silently stayed empty on every import.
        dams_attr = (
            attrs.get('dams_with_readings')
            or attrs.get('dams_reporting')
            or attrs.get('dam_stations_reporting')
        )
        if not date_attr:
            raise CommandError('National water date attribute missing.')

        sql = """
            SELECT reading_date::date AS d,
                   COUNT(DISTINCT dam_id) AS dams,
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

        created = skipped = 0
        for d, dams, total_mcm in rows:
            day: date = d if isinstance(d, date) else date.fromisoformat(str(d)[:10])
            date_s = day.isoformat()
            # Same namespace as migrate_water_dams_national_to_info.py so both
            # commands land on the same logical row for a given date instead of
            # creating two separate national-summary rows for the same day.
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'water-dams-national-{date_s}')
            pairs: list[tuple[Attribute, str]] = [(date_attr, date_s)]
            if dams_attr is not None:
                pairs.append((dams_attr, str(dams)))
            if storage_attr is not None:
                pairs.append((storage_attr, str(total_mcm)))
            if not apply:
                created += len(pairs)
                continue
            with transaction.atomic():
                for attr, value in pairs:
                    if _create_info(attr, sub, row_key, value, confirmed=confirmed):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode} water/dams: days={len(rows)} created≈{created} '
                f'skipped≈{skipped} confirmed={confirmed}'
            )
        )

    def _import_euphrates(
        self,
        sub: SubMainSection,
        title_name: str,
        year: int,
        apply: bool,
        confirmed: str,
    ) -> None:
        attrs = _attrs_for_title(title_name)
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        if date_attr is None:
            raise CommandError('Date attribute missing on Euphrates title.')

        cols = ', '.join(EUPHRATES_KEYS)
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
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'euphrates-import-{date_s}')
            pairs: list[tuple[Attribute, str]] = [(date_attr, date_s)]
            if label_attr is not None and report_label:
                pairs.append((label_attr, report_label))
            for key, raw in zip(EUPHRATES_KEYS, values, strict=True):
                attr = attrs.get(key)
                if attr is None or raw is None:
                    continue
                pairs.append((attr, str(raw)))
            if not apply:
                created += len(pairs)
                continue
            with transaction.atomic():
                for attr, value in pairs:
                    if _create_info(attr, sub, row_key, value, confirmed=confirmed):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode} water/euphrates: days={len(rows)} created≈{created} '
                f'skipped≈{skipped} confirmed={confirmed}'
            )
        )
