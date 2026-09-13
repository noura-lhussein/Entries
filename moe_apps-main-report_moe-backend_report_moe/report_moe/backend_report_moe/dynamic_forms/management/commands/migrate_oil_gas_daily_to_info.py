"""
Migrate published moeds oil_gas DailyReport/DailyMetric rows into accepted Info.

Prereqs:
  python manage.py seed_oil_gas_daily_info_forms

Usage:
  python manage.py migrate_oil_gas_daily_to_info --sub-main-id 15
  python manage.py migrate_oil_gas_daily_to_info --sub-main-id 15 --apply
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[oil-gas-daily-migration]'
TITLE_NATIONAL = 'مؤشرات التقرير اليومي للنفط والغاز'
TITLE_FIELD_CODE = 'oil_gas.field_entity'
TITLE_REFINERY_CODE = 'oil_gas.refinery_entity'
ENTITY_OIL_FIELD = 'oil_field'
ENTITY_OIL_REFINERY = 'oil_refinery'

EXECUTIVE_METRIC_KEYS = frozenset(
    {
        'total_oil_production_bbl',
        'total_crude_transferred_bbl',
        'local_clean_gas_mm3',
        'clean_gas_import_azerbaijan_mm3',
        'clean_gas_import_jordan_mm3',
        'total_clean_gas_mm3',
        'clean_gas_distributed_mm3',
        'electricity_clean_gas_consumption_mm3',
        'mazut_sold_thu_fri_m3',
        'gasoline_90_95_sold_thu_fri_m3',
        'domestic_lpg_sold_m3',
        'fuel_oil_sold_m3',
        'brent_crude_price_usd_bbl',
        'gas_price_usd_mmbtu',
    }
)


def _attrs(title_name: str) -> tuple[Title, dict[str, Attribute]]:
    title = Title.objects.filter(name=title_name).first()
    if title is None:
        raise CommandError(f'Title missing: {title_name}. Run seed_oil_gas_daily_info_forms.')
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return title, {**by_key, **by_label}


def _create_info(
    *,
    attribute: Attribute,
    sub_main: SubMainSection,
    row_key: uuid.UUID,
    value: str,
    entity_type: str = '',
    entity_id: int | None = None,
) -> bool:
    # Matches the DB's real UniqueConstraint scope — (attribute, row_key) only,
    # not sub_main (see the same fix in migrate_electricity_daily_to_info.py).
    exists = Info.objects.filter(
        attribute=attribute,
        row_key=row_key,
    ).exists()
    if exists:
        return False
    Info.objects.create(
        attribute=attribute,
        sub_main=sub_main,
        row_key=row_key,
        value=value,
        confirmed=Info.ConfirmStatus.ACCEPT,
        entity_type=entity_type or '',
        entity_id=entity_id,
        commit_note=NOTE_TAG,
    )
    return True


def _attrs_by_code(title_code: str) -> tuple[Title | None, dict[str, Attribute]]:
    title = Title.objects.filter(code=title_code).first()
    if title is None:
        return None, {}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return title, by_key


class Command(BaseCommand):
    help = 'Migrate published oil & gas DailyReport metrics into Info (default dry-run).'

    def add_arguments(self, parser):
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--limit-dates', type=int, default=0, help='0 = all published dates')

    def handle(self, *args, **options):
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')

        apply = bool(options['apply'])
        limit = int(options['limit_dates'] or 0)
        _, nat_attrs = _attrs(TITLE_NATIONAL)
        field_title, field_attrs = _attrs_by_code(TITLE_FIELD_CODE)
        refinery_title, refinery_attrs = _attrs_by_code(TITLE_REFINERY_CODE)
        if field_title is None or refinery_title is None:
            self.stderr.write(self.style.WARNING(
                'Field/refinery entity titles missing — run seed_oil_gas_daily_info_forms. '
                'Skipping entity-level migration.'
            ))

        reports = self._fetch_reports(limit)
        created = skipped = 0

        for report in reports:
            report_id = int(report['id'])
            report_date: date = report['report_date']
            date_s = report_date.isoformat()
            self.stdout.write(f'--- {date_s} (report_id={report_id}) ---')

            if apply:
                with transaction.atomic():
                    c, s = self._migrate_national(sub, nat_attrs, report_id, date_s, apply=True)
            else:
                c, s = self._migrate_national(sub, nat_attrs, report_id, date_s, apply=False)
            created += c
            skipped += s

        if field_attrs:
            def run_field():
                return self._migrate_fields(sub, field_attrs, apply)
            c, s = (self._atomic(run_field) if apply else run_field())
            created += c
            skipped += s

        if refinery_attrs:
            def run_refinery():
                return self._migrate_refineries(sub, refinery_attrs, apply)
            c, s = (self._atomic(run_refinery) if apply else run_refinery())
            created += c
            skipped += s

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(f'{mode}: created≈{created}, skipped≈{skipped}'))

    @staticmethod
    def _atomic(fn):
        with transaction.atomic():
            return fn()

    def _fetch_reports(self, limit: int) -> list[dict[str, Any]]:
        sql = """
            SELECT id, report_date, notes_ar, notes_en
            FROM oil_gas_dailyreport
            WHERE status = 'published'
            ORDER BY report_date DESC
        """
        if limit > 0:
            sql += f' LIMIT {int(limit)}'
        with connections['default'].cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0] for c in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _migrate_fields(self, sub, attrs, apply: bool):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT field_id, production_date, crude_oil_bbl, natural_gas_mmscf,
                       condensate_bbl, water_cut_percent, operating_hours
                FROM oil_gas_dailyproduction
                ORDER BY production_date
                """
            )
            rows = cursor.fetchall()
        col_keys = [
            'crude_oil_bbl', 'natural_gas_mmscf', 'condensate_bbl',
            'water_cut_percent', 'operating_hours',
        ]
        for field_id, prod_date, *values in rows:
            date_s = prod_date.isoformat()
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'og-field-{date_s}-{field_id}')
            pairs = [
                (attrs.get('oil_field'), str(field_id), ENTITY_OIL_FIELD, field_id),
                (attrs.get('production_date'), date_s, ENTITY_OIL_FIELD, field_id),
            ]
            for key, val in zip(col_keys, values):
                if val is None:
                    continue
                pairs.append((attrs.get(key), str(val), ENTITY_OIL_FIELD, field_id))
            for attr, value, et, eid in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr, sub_main=sub, row_key=row_key, value=value,
                        entity_type=et, entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_refineries(self, sub, attrs, apply: bool):
        created = skipped = 0
        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT refinery_id, production_date, gasoline_ton, diesel_ton,
                       fuel_oil_ton, lpg_ton
                FROM oil_gas_refinerydailyoutput
                ORDER BY production_date
                """
            )
            rows = cursor.fetchall()
        col_keys = ['gasoline_ton', 'diesel_ton', 'fuel_oil_ton', 'lpg_ton']
        for refinery_id, prod_date, *values in rows:
            date_s = prod_date.isoformat()
            row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'og-refinery-{date_s}-{refinery_id}')
            pairs = [
                (attrs.get('oil_refinery'), str(refinery_id), ENTITY_OIL_REFINERY, refinery_id),
                (attrs.get('production_date'), date_s, ENTITY_OIL_REFINERY, refinery_id),
            ]
            for key, val in zip(col_keys, values):
                if val is None:
                    continue
                pairs.append((attrs.get(key), str(val), ENTITY_OIL_REFINERY, refinery_id))
            for attr, value, et, eid in pairs:
                if attr is None or value == '':
                    continue
                if apply:
                    if _create_info(
                        attribute=attr, sub_main=sub, row_key=row_key, value=value,
                        entity_type=et, entity_id=eid,
                    ):
                        created += 1
                    else:
                        skipped += 1
                else:
                    created += 1
        return created, skipped

    def _migrate_national(self, sub, attrs, report_id, date_s, *, apply: bool):
        created = skipped = 0
        date_attr = attrs.get('تاريخ التقرير') or attrs.get('report_date')
        if date_attr is None:
            self.stderr.write(self.style.ERROR('Missing date attribute تاريخ التقرير'))
            return 0, 0

        with connections['default'].cursor() as cursor:
            cursor.execute(
                """
                SELECT metric_key, value
                FROM oil_gas_dailymetric
                WHERE report_id = %s AND (dimension IS NULL OR dimension = '')
                """,
                [report_id],
            )
            metrics = [
                (str(k), v)
                for k, v in cursor.fetchall()
                if str(k) in EXECUTIVE_METRIC_KEYS
            ]

        row_key = uuid.uuid5(uuid.NAMESPACE_URL, f'og-national-{date_s}')
        if not apply:
            return 1 + len([k for k, _ in metrics if k in attrs]), 0

        if _create_info(attribute=date_attr, sub_main=sub, row_key=row_key, value=date_s):
            created += 1
        else:
            skipped += 1

        for key, value in metrics:
            attr = attrs.get(key)
            if attr is None:
                continue
            if _create_info(
                attribute=attr,
                sub_main=sub,
                row_key=row_key,
                value='' if value is None else str(value),
            ):
                created += 1
            else:
                skipped += 1
        return created, skipped
