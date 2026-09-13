"""
Build dashboard alert lists from accepted Info under sector TitleCategory.

Titles follow «تنبيهات تشغيلية - …».
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
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

TITLE_PREFIX = 'تنبيهات تشغيلية'
ACTIVE_STATUSES = frozenset({'active', 'open', 'نشط', 'مفتوح'})


def _parse_date(value: str) -> date | None:
    text = str(value or '').strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
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


def list_info_alerts(
    category_name: str,
    *,
    title_name_pattern: str = TITLE_PREFIX,
    settings_id: int | None = None,
    env_id_name: str = '',
    on_date: date | None = None,
    active_only: bool = True,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """
    Accepted Info alert rows for dashboards.

    Each item: severity, message_ar, message_en, start_date, status, row_key.
    """
    cid = resolve_title_category_id(
        category_name, settings_id=settings_id, env_id_name=env_id_name
    )
    title_ids = _title_ids_matching(cid, title_name_pattern=title_name_pattern)
    if not title_ids:
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

    alerts: list[dict[str, Any]] = []
    for rk, facts in _row_facts(list(by_id.values()), attrs).items():
        severity = (facts.get('severity') or 'info').strip() or 'info'
        message_ar = (facts.get('message_ar') or '').strip()
        message_en = (facts.get('message_en') or '').strip()
        if not message_ar and not message_en:
            continue
        start = _parse_date(facts.get('start_date', ''))
        status = (facts.get('status') or 'active').strip() or 'active'
        if active_only and status.lower() not in ACTIVE_STATUSES and status not in ACTIVE_STATUSES:
            continue
        if on_date is not None and start is not None and start > on_date:
            continue
        alerts.append(
            {
                'severity': severity,
                'message_ar': message_ar,
                'message_en': message_en or message_ar,
                'start_date': start.isoformat() if start else None,
                'status': status,
                'row_key': rk,
                'source': 'info',
            }
        )

    alerts.sort(key=lambda a: a.get('start_date') or '', reverse=True)
    return alerts
