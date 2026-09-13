"""
Migrate moeds OperationalTarget rows into accepted Info under sector titles.

Prereqs:
  python manage.py seed_operational_targets_info_forms

Usage:
  python manage.py migrate_operational_targets_to_info --sector oil_gas --sub-main-id 15
  python manage.py migrate_operational_targets_to_info --sector electricity --sub-main-id 15 --apply
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from dynamic_forms.models import Attribute, Info, SubMainSection, Title

NOTE_TAG = '[operational-targets-migration]'

SECTOR_CONFIG: dict[str, dict[str, str]] = {
    'oil_gas': {
        'table': 'oil_gas_operationaltarget',
        'title': 'أهداف تشغيلية - النفط والغاز',
        'row_ns': 'op-target-oil-gas',
    },
    'electricity': {
        'table': 'electricity_operationaltarget',
        'title': 'أهداف تشغيلية - الكهرباء',
        'row_ns': 'op-target-electricity',
    },
    'water': {
        'table': 'water_operationaltarget',
        'title': 'أهداف تشغيلية - المياه',
        'row_ns': 'op-target-water',
    },
    'geology': {
        'table': 'geology_operationaltarget',
        'title': 'أهداف تشغيلية - الجيولوجيا',
        'row_ns': 'op-target-geology',
    },
}

FIELD_KEYS = (
    'metric_key',
    'scope_type',
    'scope_code',
    'period_type',
    'period_start',
    'period_end',
    'target_value',
    'unit',
    'label_ar',
    'label_en',
    'notes',
)


def _attrs(title_name: str) -> tuple[Title, dict[str, Attribute]]:
    title = Title.objects.filter(name=title_name).first()
    if title is None:
        raise CommandError(
            f'Title missing: {title_name}. Run seed_operational_targets_info_forms.'
        )
    by_label = {a.label: a for a in Attribute.objects.filter(title=title)}
    by_key = {a.key: a for a in Attribute.objects.filter(title=title) if a.key}
    return title, {**by_key, **by_label}


def _fmt(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, 'f')
    return str(value)


def _create_info(
    *,
    attribute: Attribute,
    sub_main: SubMainSection,
    row_key: uuid.UUID,
    value: str,
) -> bool:
    exists = Info.objects.filter(
        attribute=attribute,
        sub_main=sub_main,
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
        commit_note=NOTE_TAG,
    )
    return True


def _row_key(ns: str, row: dict[str, Any]) -> uuid.UUID:
    metric = str(row.get('metric_key') or '')
    scope_type = str(row.get('scope_type') or '')
    scope_code = str(row.get('scope_code') or '')
    period_type = str(row.get('period_type') or '')
    period_start = _fmt(row.get('period_start'))
    return uuid.uuid5(
        uuid.NAMESPACE_URL,
        f'{ns}|{metric}|{scope_type}|{scope_code}|{period_type}|{period_start}',
    )


class Command(BaseCommand):
    help = 'Migrate OperationalTarget rows from moeds into accepted Info (dry-run default).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sector',
            type=str,
            required=True,
            choices=sorted(SECTOR_CONFIG.keys()),
        )
        parser.add_argument('--sub-main-id', type=int, required=True)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        sector = options['sector']
        cfg = SECTOR_CONFIG[sector]
        sub = SubMainSection.objects.filter(pk=options['sub_main_id']).first()
        if sub is None:
            raise CommandError(f'SubMainSection {options["sub_main_id"]} not found.')

        apply = bool(options['apply'])
        _, attrs = _attrs(cfg['title'])
        for key in FIELD_KEYS:
            if key not in attrs:
                raise CommandError(f'Missing attribute {key} on title {cfg["title"]}.')

        rows = self._fetch_rows(cfg['table'])
        created = skipped = 0

        for row in rows:
            rk = _row_key(cfg['row_ns'], row)
            if not apply:
                created += len(FIELD_KEYS)
                continue
            with transaction.atomic():
                for key in FIELD_KEYS:
                    attr = attrs[key]
                    value = _fmt(row.get(key))
                    if _create_info(
                        attribute=attr,
                        sub_main=sub,
                        row_key=rk,
                        value=value,
                    ):
                        created += 1
                    else:
                        skipped += 1

        mode = 'APPLIED' if apply else 'DRY-RUN'
        self.stdout.write(
            self.style.SUCCESS(
                f'{mode} sector={sector}: rows={len(rows)} created≈{created} skipped≈{skipped}'
            )
        )

    def _fetch_rows(self, table: str) -> list[dict[str, Any]]:
        cols = ', '.join(FIELD_KEYS)
        sql = f"""
            SELECT {cols}
            FROM {table}
            ORDER BY period_start DESC, metric_key, scope_type, scope_code
        """
        with connections['default'].cursor() as cursor:
            cursor.execute(sql)
            names = [c[0] for c in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]
