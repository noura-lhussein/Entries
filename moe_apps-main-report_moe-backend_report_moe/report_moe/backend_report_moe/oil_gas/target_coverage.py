from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .models import Field, OperationalTarget
from .target_catalog import SNAPSHOT_TARGET_MAP, TARGET_METRIC_BY_KEY
from .target_resolver import resolve_target


@dataclass(frozen=True, slots=True)
class TargetCoverageSlot:
    metric_key: str
    scope_type: str
    scope_code: str
    period_hint: str  # 'daily' | 'monthly' — preferred period when creating
    group: str


# National metrics required for minister dashboard KPI achievement (daily or monthly resolves)
NATIONAL_KPI_METRIC_KEYS: tuple[str, ...] = tuple(dict.fromkeys(SNAPSHOT_TARGET_MAP.values()))

# National monthly plan rows (monthly plan table)
NATIONAL_MONTHLY_METRIC_KEYS: tuple[str, ...] = NATIONAL_KPI_METRIC_KEYS

# Per-field metrics for field targets table
FIELD_DAILY_METRIC_KEYS: tuple[str, ...] = ('crude_oil_bbl',)


def _required_slots(on_date: date) -> list[TargetCoverageSlot]:
    slots: list[TargetCoverageSlot] = []
    for metric_key in NATIONAL_KPI_METRIC_KEYS:
        slots.append(
            TargetCoverageSlot(
                metric_key=metric_key,
                scope_type=OperationalTarget.ScopeType.NATIONAL,
                scope_code='',
                period_hint='daily',
                group='national_kpi',
            )
        )
    for metric_key in NATIONAL_MONTHLY_METRIC_KEYS:
        slots.append(
            TargetCoverageSlot(
                metric_key=metric_key,
                scope_type=OperationalTarget.ScopeType.NATIONAL,
                scope_code='',
                period_hint='monthly',
                group='monthly_plan',
            )
        )
    for field in Field.objects.order_by('name_en'):
        for metric_key in FIELD_DAILY_METRIC_KEYS:
            slots.append(
                TargetCoverageSlot(
                    metric_key=metric_key,
                    scope_type=OperationalTarget.ScopeType.FIELD,
                    scope_code=field.code,
                    period_hint='daily',
                    group='field_targets',
                )
            )
    return slots


def _has_kpi_target(metric_key: str, on_date: date, scope_type: str, scope_code: str) -> OperationalTarget | None:
    return resolve_target(metric_key, on_date, scope_type=scope_type, scope_code=scope_code)


def _has_monthly_plan_target(metric_key: str, on_date: date) -> OperationalTarget | None:
    month_start = on_date.replace(day=1)
    return (
        OperationalTarget.objects.filter(
            metric_key=metric_key,
            scope_type=OperationalTarget.ScopeType.NATIONAL,
            scope_code='',
            period_type=OperationalTarget.PeriodType.MONTHLY,
            period_start=month_start,
        )
        .order_by('-updated_at')
        .first()
    )


def _slot_payload(slot: TargetCoverageSlot, on_date: date) -> dict[str, Any]:
    spec = TARGET_METRIC_BY_KEY.get(slot.metric_key)
    if slot.group == 'monthly_plan':
        row = _has_monthly_plan_target(slot.metric_key, on_date)
    else:
        row = _has_kpi_target(slot.metric_key, on_date, slot.scope_type, slot.scope_code)
    scope_label_en = slot.scope_code or 'National'
    scope_label_ar = 'وطني'
    if slot.scope_type == OperationalTarget.ScopeType.FIELD and slot.scope_code:
        field = Field.objects.filter(code=slot.scope_code).first()
        if field:
            scope_label_en = field.name_en
            scope_label_ar = field.name_ar

    period_start = on_date.isoformat()
    if slot.period_hint == 'monthly':
        period_start = on_date.replace(day=1).isoformat()

    return {
        'metric_key': slot.metric_key,
        'label_en': spec.label_en if spec else slot.metric_key,
        'label_ar': spec.label_ar if spec else slot.metric_key,
        'unit': spec.unit if spec else '',
        'scope_type': slot.scope_type,
        'scope_code': slot.scope_code,
        'scope_label_en': scope_label_en,
        'scope_label_ar': scope_label_ar,
        'period_hint': slot.period_hint,
        'period_start': period_start,
        'group': slot.group,
        'status': 'ok' if row else 'missing',
        'target_id': row.id if row else None,
        'resolved_period_type': row.period_type if row else None,
        'target_value': float(row.target_value) if row else None,
    }


def build_target_coverage(on_date: date) -> dict[str, Any]:
    items = [_slot_payload(slot, on_date) for slot in _required_slots(on_date)]
    configured = sum(1 for item in items if item['status'] == 'ok')
    total = len(items)

    groups_meta = {
        'national_kpi': {
            'label_en': 'National KPI targets',
            'label_ar': 'أهداف المؤشرات',
            'description_en': 'Required for dashboard KPI achievement badges',
            'description_ar': 'مطلوبة لإظهار الإنجاز في مؤشرات لوحة التحكم',
        },
        'monthly_plan': {
            'label_en': 'Monthly plan targets',
            'label_ar': 'أهداف الخطة الشهرية',
            'description_en': 'Required for the monthly plan table on the dashboard',
            'description_ar': 'مطلوبة لجدول الخطة الشهرية في لوحة التحكم',
        },
        'field_targets': {
            'label_en': 'Field production targets',
            'label_ar': 'أهداف إنتاج الحقول',
            'description_en': 'Required for the field targets table (one per field)',
            'description_ar': 'مطلوبة لجدول أهداف الحقول (هدف لكل حقل)',
        },
    }

    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in groups_meta}
    for item in items:
        grouped[item['group']].append(item)

    return {
        'date': on_date.isoformat(),
        'summary': {
            'configured': configured,
            'required': total,
            'missing': total - configured,
            'complete': configured == total,
            'coverage_pct': round((configured / total) * 100, 1) if total else 100.0,
        },
        'groups': [
            {
                'id': group_id,
                **groups_meta[group_id],
                'configured': sum(1 for i in grouped[group_id] if i['status'] == 'ok'),
                'required': len(grouped[group_id]),
                'items': grouped[group_id],
            }
            for group_id in groups_meta
        ],
    }
