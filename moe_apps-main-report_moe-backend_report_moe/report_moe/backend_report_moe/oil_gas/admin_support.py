"""Shared helpers for the oil & gas endpoints.

Split out of the old Ninja `api.py`. Still sector-specific: the four sector apps
each grew their own variant of this admin plumbing and they have drifted, so
unifying them is a separate exercise from changing frameworks.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from config.api_errors import detail_error
from config.serialize import apply_model_update, model_to_dict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, Q

from .admin_registry import AdminResourceSpec
from .models import DailyReport, DataSource, Field, Well
from .services import (
    upsert_metric,  # retained for unused _upsert_oil_gas_report helper
)

_AUDIT_SKIP = frozenset({
    'id',
    'pk',
    'created_at',
    'updated_at',
    'created_by',
    'updated_by',
    'created_by_id',
    'updated_by_id',
})

_WELL_FIELDS = (
    'id',
    'well_code',
    'well_type',
    'status',
    'production_capacity_bpd',
    'latitude',
    'longitude',
)
_FIELD_WRITE_FIELDS = (
    'code',
    'name_ar',
    'name_en',
    'field_type',
    'governorate',
    'latitude',
    'longitude',
    'operator_company',
    'status',
    'design_capacity_bpd',
)
_FACILITY_FIELDS = (
    'id',
    'code',
    'name_en',
    'name_ar',
    'facility_type',
    'sector',
    'location',
    'governorate',
    'latitude',
    'longitude',
    'status',
)
_REFINERY_FIELDS = (
    'id',
    'refinery_name',
    'governorate',
    'latitude',
    'longitude',
    'status',
    'design_capacity_bpd',
)
_TARGET_FIELDS = (
    'id',
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
    'created_at',
    'updated_at',
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qp(request, name: str, default: str | None = None) -> str | None:
    value = request.GET.get(name, default)
    if value is None:
        return None
    return str(value)


def _json_body(request) -> dict[str, Any]:
    try:
        raw = request.body.decode('utf-8') if request.body else '{}'
        data = json.loads(raw or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise detail_error('Invalid JSON body.') from exc
    if not isinstance(data, dict):
        raise detail_error('JSON object required.')
    return data


def _as_date(value: Any, *, label: str = 'date') -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as exc:
        raise detail_error(f'Invalid {label} format. Use YYYY-MM-DD.') from exc


def _parse_optional_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return _as_date(raw)


def _model_pick(instance: Model, keys: tuple[str, ...]) -> dict[str, Any]:
    data = model_to_dict(instance)
    return {k: data[k] for k in keys if k in data}


def _well_to_dict(well: Well) -> dict[str, Any]:
    return _model_pick(well, _WELL_FIELDS)


def _field_to_dict(field: Field) -> dict[str, Any]:
    data = model_to_dict(field)
    data['wells'] = [_well_to_dict(w) for w in field.wells.all()]
    return data


def _writable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in _AUDIT_SKIP}


def _validation_error_message(exc: DjangoValidationError) -> str:
    if hasattr(exc, 'message_dict'):
        parts = []
        for field, messages in exc.message_dict.items():
            joined = '; '.join(str(m) for m in messages)
            parts.append(f'{field}: {joined}')
        return ' '.join(parts) or str(exc)
    if hasattr(exc, 'messages'):
        return ' '.join(str(m) for m in exc.messages)
    return str(exc)


def _apply_audit(instance: Model, user) -> None:
    if hasattr(instance, 'updated_by_id'):
        instance.updated_by = user
        instance.save(update_fields=['updated_by'])
    if hasattr(instance, 'source') and not instance.source:
        instance.source = DataSource.MANUAL
        instance.save(update_fields=['source'])
    if hasattr(instance, 'created_by_id') and instance.created_by_id is None:
        instance.created_by = user
        instance.save(update_fields=['created_by'])


def _get_admin_object(spec: AdminResourceSpec, pk: str) -> Model:
    if spec.lookup_field == 'snapshot_date':
        qs = spec.base_queryset()
        return qs.get(snapshot_date=pk)
    return spec.base_queryset().get(pk=pk)


def _admin_save(instance: Model, payload: dict[str, Any], *, partial: bool, spec: AdminResourceSpec | None = None) -> Model:
    data = _writable_payload(payload)
    if spec and spec.default_create_values and not partial and not instance.pk:
        for key, value in spec.default_create_values.items():
            data.setdefault(key, value)
    if spec and spec.default_create_values and (not partial or instance.pk):
        # Keep locked type fields consistent on create/update.
        for key, value in spec.default_create_values.items():
            if key in spec.locked_fields:
                data[key] = value
    apply_model_update(instance, data, partial=partial)
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        raise detail_error(_validation_error_message(exc)) from exc
    instance.save()
    return instance


def _upsert_oil_gas_report(data: dict[str, Any], user) -> DailyReport:
    if 'report_date' not in data:
        raise detail_error('report_date is required.')
    metrics = data.get('metrics') or []
    if not isinstance(metrics, list):
        raise detail_error('metrics must be a list.')
    report_date = _as_date(data['report_date'], label='report_date')
    status = data.get('status', DailyReport.Status.DRAFT)
    report, _ = DailyReport.objects.update_or_create(
        report_date=report_date,
        defaults={
            'status': status,
            'notes_ar': data.get('notes_ar', ''),
            'notes_en': data.get('notes_en', ''),
            'created_by': user,
        },
    )
    for item in metrics:
        if not isinstance(item, dict) or 'metric_key' not in item or 'value' not in item:
            raise detail_error('Each metric requires metric_key and value.')
        try:
            value = Decimal(str(item['value']))
        except (InvalidOperation, TypeError) as exc:
            raise detail_error(f'Invalid metric value for {item.get("metric_key")}.') from exc
        upsert_metric(
            report,
            str(item['metric_key']),
            value,
            str(item.get('dimension') or ''),
            str(item.get('unit') or ''),
        )
    return report


def _normalize_daily_ops_payload(data: dict[str, Any]) -> dict[str, Any]:
    if 'production_date' not in data:
        raise detail_error('production_date is required.')
    payload = dict(data)
    payload['production_date'] = _as_date(payload['production_date'], label='production_date')
    for key in (
        'production',
        'refinery_outputs',
        'inventory',
        'exports',
        'losses',
        'power_gas_supply',
        'power_gas_requirement',
    ):
        payload.setdefault(key, [])
    payload.setdefault('notes_ar', '')
    payload.setdefault('notes_en', '')
    payload.setdefault('publish', False)
    return payload


# ---------------------------------------------------------------------------
# Dashboard / reports / maps
# ---------------------------------------------------------------------------


def build_admin_list_payload(request, spec) -> dict[str, Any]:
    """Paginated, searchable, sortable list for one admin resource.

    Lifted verbatim from the Ninja view so the payload keys, the pagination maths
    and the sort fallbacks stay exactly as the portal's admin tables expect.
    """
    search = (_qp(request, 'search') or '').strip()
    status_filter = (_qp(request, 'status') or '').strip()
    sort_col = (_qp(request, 'sort') or '').strip()
    sort_dir = (_qp(request, 'direction') or 'asc').lower()
    page = max(1, int(_qp(request, 'page') or 1))
    page_size = min(max(1, int(_qp(request, 'page_size') or 10)), 100)

    allowed_fields = {f.name for f in spec.model._meta.fields}
    if sort_col in allowed_fields and sort_col in spec.list_display:
        ordering = [f'-{sort_col}' if sort_dir == 'desc' else sort_col]
    else:
        ordering = list(spec.model._meta.ordering or ['-pk'])

    qs = spec.base_queryset().order_by(*ordering)
    if status_filter and 'status' in allowed_fields:
        qs = qs.filter(status=status_filter)
    if search and spec.list_display:
        q = Q()
        for col in spec.list_display:
            try:
                field = spec.model._meta.get_field(col)
                if field.get_internal_type() in ('CharField', 'TextField', 'SlugField'):
                    q |= Q(**{f'{col}__icontains': search})
            except Exception:
                continue
        if q.children:
            qs = qs.filter(q).order_by(*ordering)

    total_count = qs.count()
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = min(page, total_pages)
    offset = (page - 1) * page_size
    page_qs = list(qs[offset : offset + page_size])
    results = [model_to_dict(obj) for obj in page_qs]
    return {
        'slug': spec.slug,
        'count': len(results),
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': results,
    }

