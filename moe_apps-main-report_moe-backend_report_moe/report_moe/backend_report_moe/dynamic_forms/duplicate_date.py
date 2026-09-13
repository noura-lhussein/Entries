"""Prevent more than one Info logical row for the same report date (per title)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.db.models import Q

from .entity_registry import is_entity_attribute
from .models import Attribute, Info

# Priority order only, for titles carrying more than one date field. Membership
# here does NOT make a field the report date -- Attribute.is_report_date does.
DATE_KEYS = frozenset({'report_date', 'reading_date', 'update_date'})
DATE_LABELS = frozenset({'تاريخ التقرير', 'تاريخ القراءة', 'تاريخ التحديث'})
ACTIVE_STATUSES = (
    Info.ConfirmStatus.WAITING,
    Info.ConfirmStatus.ACCEPT,
)


def normalize_date_value(raw: Any) -> str | None:
    """Return YYYY-MM-DD or None if not a usable date."""
    if raw is None:
        return None
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw.isoformat()
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    text = str(raw).strip()
    if not text:
        return None
    # ISO / HTML date
    if len(text) >= 10 and text[4] == '-' and text[7] == '-':
        try:
            return date.fromisoformat(text[:10]).isoformat()
        except ValueError:
            return None
    # DD/MM/YYYY or DD-MM-YYYY
    for sep in ('/', '-', '.'):
        parts = text.split(sep)
        if len(parts) == 3 and len(parts[2]) == 4:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                return date(y, m, d).isoformat()
            except ValueError:
                return None
    return None


def is_date_attribute(attr: Attribute) -> bool:
    """True only for the date that identifies one report.

    Attribute.is_report_date is the authority. Matching on type/key/label used to
    catch every date field, which wrongly blocked a second incident on the same
    day in the event-log titles -- they name their field تاريخ التقرير too. The
    lists below now only order competing date fields, they no longer select them.
    """
    return bool(attr.is_report_date)


def _date_attr_priority(attr: Attribute) -> int:
    key = (attr.key or '').strip()
    label = (attr.label or '').strip()
    if key == 'report_date' or label == 'تاريخ التقرير':
        return 0
    if key == 'reading_date' or label == 'تاريخ القراءة':
        return 1
    if key == 'update_date' or label == 'تاريخ التحديث':
        return 2
    return 9


def extract_date_and_entity(
    items: list[dict],
    *,
    title_id: int | None,
) -> tuple[str | None, str, int | None, Attribute | None]:
    """
    From submitted attribute_values, resolve report date + optional entity.
    Returns (date_yyyy_mm_dd, entity_type, entity_id, date_attribute).
    """
    if not items:
        return None, '', None, None

    attr_ids = [item.get('id') for item in items if item.get('id') is not None]
    attrs = {
        a.id: a
        for a in Attribute.objects.filter(id__in=attr_ids).select_related('title')
    }
    if title_id is not None:
        attrs = {i: a for i, a in attrs.items() if a.title_id == title_id}

    date_candidates: list[tuple[int, Attribute, str]] = []
    entity_type = ''
    entity_id: int | None = None

    for item in items:
        attr = attrs.get(item.get('id'))
        if not attr:
            continue
        raw = item.get('value', '')
        if is_date_attribute(attr):
            normalized = normalize_date_value(raw)
            if normalized:
                date_candidates.append(
                    (_date_attr_priority(attr), attr, normalized))
        elif is_entity_attribute(attr.type):
            try:
                eid = int(str(raw).strip())
            except (TypeError, ValueError):
                continue
            if eid:
                entity_type = attr.type or entity_type
                entity_id = eid

    if not date_candidates:
        return None, entity_type, entity_id, None

    date_candidates.sort(key=lambda x: x[0])
    _prio, date_attr, date_value = date_candidates[0]
    return date_value, entity_type, entity_id, date_attr


def find_duplicate_date_conflict(
    *,
    title_id: int,
    sub_main_id: int,
    date_value: str,
    date_attr: Attribute,
    entity_type: str = '',
    entity_id: int | None = None,
) -> dict[str, Any] | None:
    """
    If an active Info row already exists for this title/sub_main/date/(entity),
    return conflict details; otherwise None.
    """
    qs = Info.objects.filter(
        attribute_id=date_attr.id,
        sub_main_id=sub_main_id,
        archived=False,
        confirmed__in=ACTIVE_STATUSES,
    ).filter(
        Q(value=date_value)
        | Q(value__startswith=f'{date_value}T')
        | Q(value__startswith=f'{date_value} ')
    )

    # Prefer matching entity scope when the new row is entity-linked.
    if entity_type and entity_id is not None:
        # Rows stamped on the date field or siblings sharing row_key with entity.
        entity_row_keys = (
            Info.objects.filter(
                attribute__title_id=title_id,
                sub_main_id=sub_main_id,
                entity_type=entity_type,
                entity_id=entity_id,
                archived=False,
                confirmed__in=ACTIVE_STATUSES,
            )
            .exclude(row_key__isnull=True)
            .values_list('row_key', flat=True)
            .distinct()
        )
        qs = qs.filter(Q(entity_type=entity_type, entity_id=entity_id) | Q(
            row_key__in=entity_row_keys))
    else:
        # National / non-entity rows: ignore entity-linked dated rows if any.
        qs = qs.filter(Q(entity_id__isnull=True) | Q(entity_type=''))

    existing = qs.order_by('-created_at', '-id').first()
    if not existing:
        return None

    return {
        'code': 'duplicate_report_date',
        'date': date_value,
        'title_id': title_id,
        'sub_main_id': sub_main_id,
        'entity_type': entity_type or None,
        'entity_id': entity_id,
        'existing_row_key': str(existing.row_key) if existing.row_key else None,
        'existing_info_id': existing.id,
        'confirmed': existing.confirmed,
        'detail': (
            f'يوجد تقرير مسجّل مسبقاً لهذا القسم بتاريخ {date_value}. '
            'لا يمكن إدخال أكثر من تقرير لنفس التاريخ.'
        ),
    }


def check_submit_duplicate_date(
    *,
    title_id: int | None,
    sub_main_id: int,
    items: list[dict],
) -> dict[str, Any] | None:
    if not title_id or not items:
        return None
    date_value, entity_type, entity_id, date_attr = extract_date_and_entity(
        items, title_id=title_id
    )
    if not date_value or date_attr is None:
        return None
    return find_duplicate_date_conflict(
        title_id=title_id,
        sub_main_id=sub_main_id,
        date_value=date_value,
        date_attr=date_attr,
        entity_type=entity_type,
        entity_id=entity_id,
    )
