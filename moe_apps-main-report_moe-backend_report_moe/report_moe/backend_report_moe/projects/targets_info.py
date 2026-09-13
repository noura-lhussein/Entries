"""
Load accepted operational-target Info rows for a sector TitleCategory.

Titles follow «أهداف تشغيلية - …». Returns dicts matching OperationalTarget fields.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import DatabaseError

from projects.display_models import (
    ReportDynamicFormsAttribute,
    ReportDynamicFormsInfo,
    ReportDynamicFormsTitle,
)
from projects.info_sector_scope import (
    accepted_infos_for_attribute_ids,
    attribute_ids_for_titles,
    resolve_title_category_id,
    title_ids_for_category,
)
from projects.report_forms_read import ACCEPTED

TITLE_PREFIX = 'أهداف تشغيلية'
TARGET_FIELD_KEYS = (
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


def _parse_date(value: str) -> date | None:
    text = str(value or '').strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _parse_decimal(value: str) -> Decimal | None:
    text = str(value or '').strip().replace(',', '.')
    if not text:
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def _title_ids_matching(
    category_id: int | None,
    *,
    title_name_pattern: str = TITLE_PREFIX,
) -> list[int]:
    if category_id is None:
        return []
    try:
        qs = ReportDynamicFormsTitle.objects.filter(
            category_id=category_id,
            deleted=False,
            name__startswith=title_name_pattern,
        )
        return list(qs.values_list('id', flat=True))
    except DatabaseError:
        return []


def _row_facts(
    infos: list[ReportDynamicFormsInfo],
    attrs: dict[int, ReportDynamicFormsAttribute],
) -> dict[str, dict[str, str]]:
    buckets: dict[str, dict[str, str]] = defaultdict(dict)
    for info in infos:
        attr = attrs.get(info.attribute_id)
        if attr is None or not info.row_key:
            continue
        rk = str(info.row_key)
        for name in (attr.key, attr.label):
            if name:
                buckets[rk][str(name)] = str(info.value or '')
    return buckets


def _facts_to_target(facts: dict[str, str], *, row_key: str) -> dict[str, Any] | None:
    metric_key = (facts.get('metric_key') or '').strip()
    period_start = _parse_date(facts.get('period_start', ''))
    target_value = _parse_decimal(facts.get('target_value', ''))
    if not metric_key or period_start is None or target_value is None:
        return None
    period_end = _parse_date(facts.get('period_end', ''))
    return {
        'id': None,
        'row_key': row_key,
        'metric_key': metric_key,
        'scope_type': (facts.get('scope_type') or 'national').strip() or 'national',
        'scope_code': (facts.get('scope_code') or '').strip(),
        'period_type': (facts.get('period_type') or 'daily').strip() or 'daily',
        'period_start': period_start,
        'period_end': period_end,
        'target_value': target_value,
        'unit': (facts.get('unit') or '').strip(),
        'label_ar': (facts.get('label_ar') or '').strip(),
        'label_en': (facts.get('label_en') or '').strip(),
        'notes': (facts.get('notes') or '').strip(),
        'created_at': None,
        'updated_at': None,
        'source': 'info',
    }


def list_info_targets(
    category_name: str,
    *,
    title_name_pattern: str = TITLE_PREFIX,
    settings_id: int | None = None,
    env_id_name: str = '',
    limit: int = 20000,
) -> list[dict[str, Any]]:
    """
    Accepted Info target rows for a TitleCategory, matching title_name_pattern.
    """
    cid = resolve_title_category_id(
        category_name, settings_id=settings_id, env_id_name=env_id_name
    )
    title_ids = _title_ids_matching(cid, title_name_pattern=title_name_pattern)
    if not title_ids:
        # Fallback: any title under category whose name contains the pattern.
        all_ids = title_ids_for_category(cid)
        if all_ids:
            try:
                title_ids = list(
                    ReportDynamicFormsTitle.objects
                    .filter(id__in=all_ids, name__contains=title_name_pattern)
                    .values_list('id', flat=True)
                )
            except DatabaseError:
                title_ids = []
    attr_ids = attribute_ids_for_titles(title_ids)
    infos = accepted_infos_for_attribute_ids(attr_ids, limit=limit)
    if not infos:
        return []

    try:
        attrs = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(
                id__in={r.attribute_id for r in infos}
            )
        }
    except DatabaseError:
        return []

    # Expand siblings sharing row_key (same accepted status).
    row_keys = {r.row_key for r in infos if r.row_key}
    by_id = {r.id: r for r in infos}
    if row_keys:
        try:
            for row in ReportDynamicFormsInfo.objects.filter(
                row_key__in=row_keys, confirmed=ACCEPTED
            ):
                by_id[row.id] = row
                if row.attribute_id not in attrs:
                    try:
                        a = ReportDynamicFormsAttribute.objects.get(
                            pk=row.attribute_id
                        )
                        attrs[a.id] = a
                    except Exception:
                        pass
        except DatabaseError:
            pass

    targets: list[dict[str, Any]] = []
    for rk, facts in _row_facts(list(by_id.values()), attrs).items():
        target = _facts_to_target(facts, row_key=rk)
        if target:
            targets.append(target)

    targets.sort(
        key=lambda t: (
            -(t['period_start'].toordinal() if isinstance(t['period_start'], date) else 0),
            t['metric_key'],
            t['scope_type'],
            t['scope_code'],
        )
    )
    return targets


def filter_info_targets(
    targets: list[dict[str, Any]],
    *,
    metric_key: str | None = None,
    scope_type: str | None = None,
    scope_code: str | None = None,
    period_start: str | date | None = None,
) -> list[dict[str, Any]]:
    ps: date | None = None
    if isinstance(period_start, date):
        ps = period_start
    elif period_start:
        ps = _parse_date(str(period_start))

    out: list[dict[str, Any]] = []
    for t in targets:
        if metric_key and t['metric_key'] != metric_key:
            continue
        if scope_type and t['scope_type'] != scope_type:
            continue
        # Only filter scope_code when a non-empty query value is provided.
        if scope_code and str(t.get('scope_code') or '') != str(scope_code):
            continue
        if ps is not None and t['period_start'] != ps:
            continue
        out.append(t)
    return out


def serialize_info_target(t: dict[str, Any]) -> dict[str, Any]:
    """JSON-friendly shape for API list endpoints."""
    period_start = t.get('period_start')
    period_end = t.get('period_end')
    target_value = t.get('target_value')
    return {
        'id': t.get('id'),
        'metric_key': t.get('metric_key'),
        'scope_type': t.get('scope_type'),
        'scope_code': t.get('scope_code') or '',
        'period_type': t.get('period_type'),
        'period_start': period_start.isoformat() if isinstance(period_start, date) else period_start,
        'period_end': period_end.isoformat() if isinstance(period_end, date) else period_end,
        'target_value': float(target_value) if target_value is not None else None,
        'unit': t.get('unit') or '',
        'label_ar': t.get('label_ar') or '',
        'label_en': t.get('label_en') or '',
        'notes': t.get('notes') or '',
        'created_at': t.get('created_at'),
        'updated_at': t.get('updated_at'),
        'source': t.get('source') or 'info',
    }


def target_as_namespace(t: dict[str, Any]):
    """Attribute-compatible object for resolvers that expect OperationalTarget fields."""
    from types import SimpleNamespace

    return SimpleNamespace(
        id=t.get('id'),
        metric_key=t['metric_key'],
        scope_type=t['scope_type'],
        scope_code=t.get('scope_code') or '',
        period_type=t['period_type'],
        period_start=t['period_start'],
        period_end=t.get('period_end'),
        target_value=t['target_value'],
        unit=t.get('unit') or '',
        label_ar=t.get('label_ar') or '',
        label_en=t.get('label_en') or '',
        notes=t.get('notes') or '',
        updated_at=t.get('updated_at') or datetime.min,
        created_at=t.get('created_at'),
        source='info',
    )
