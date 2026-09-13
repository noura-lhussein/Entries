"""
Shared reader for accepted dynamic_forms Info rows linked to moeds master entities.
"""

from __future__ import annotations

from typing import Any

from django.db import DatabaseError
from django.db.models import Q

from projects.display_models import ReportDynamicFormsAttribute, ReportDynamicFormsInfo

ACCEPTED = 'accept'


def accepted_rows_for_entity(*, entity_type: str, entity_id: int) -> list[ReportDynamicFormsInfo]:
    """
    Rows stamped with entity_type/entity_id, plus sibling fields that share row_key.
    """
    direct = list(
        ReportDynamicFormsInfo.objects
        .filter(
            entity_type=entity_type,
            entity_id=entity_id,
            confirmed=ACCEPTED,
        )
        .order_by('-created_at', '-id')
    )
    if not direct:
        return []

    row_keys = {row.row_key for row in direct if row.row_key}
    if not row_keys:
        return direct

    siblings = list(
        ReportDynamicFormsInfo.objects
        .filter(row_key__in=row_keys, confirmed=ACCEPTED)
        .filter(Q(entity_id__isnull=True) | Q(entity_id=entity_id))
        .order_by('-created_at', '-id')
    )
    by_id = {row.id: row for row in direct}
    for row in siblings:
        by_id[row.id] = row
    return list(by_id.values())


def latest_accepted_facts_for_entity(
    *,
    entity_type: str,
    entity_id: int,
) -> list[dict[str, Any]]:
    """Latest accepted Info rows for one master entity, grouped by attribute_id."""
    try:
        rows = accepted_rows_for_entity(
            entity_type=entity_type, entity_id=entity_id)
    except DatabaseError:
        return []

    latest_by_attr: dict[int, ReportDynamicFormsInfo] = {}
    for row in sorted(
        rows,
        key=lambda r: (
            r.attribute_id,
            -(r.created_at.timestamp() if r.created_at else 0),
            -r.id,
        ),
    ):
        if row.attribute_id not in latest_by_attr:
            latest_by_attr[row.attribute_id] = row

    if not latest_by_attr:
        return []

    attr_ids = list(latest_by_attr.keys())
    try:
        labels = {
            a.id: a
            for a in ReportDynamicFormsAttribute.objects.filter(
                id__in=attr_ids
            )
        }
    except DatabaseError:
        labels = {}

    out: list[dict[str, Any]] = []
    for attr_id, info in sorted(latest_by_attr.items(), key=lambda x: x[0]):
        attr = labels.get(attr_id)
        out.append(
            {
                'attribute_id': attr_id,
                'attribute_label': getattr(attr, 'label', None) or str(attr_id),
                'attribute_type': getattr(attr, 'type', None) or '',
                'value': info.value,
                'created_at': info.created_at.isoformat() if info.created_at else None,
                'row_key': str(info.row_key) if info.row_key else None,
                'source': 'dynamic_forms',
            }
        )
    return out


def facts_payload(
    *,
    entity_type: str,
    entity_id: int,
    master: dict[str, Any],
) -> dict[str, Any]:
    facts = latest_accepted_facts_for_entity(
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return {
        **master,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'report_facts': facts,
        'has_report_facts': bool(facts),
        'fallback': 'legacy' if not facts else 'report_forms',
    }
