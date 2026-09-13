"""Shared helpers for the electricity endpoints.

Split out of the old Ninja `api.py`. Still electricity-specific: the sector apps
each grew their own variant of this admin plumbing and they have drifted, so
unifying them is a separate exercise from changing frameworks.
"""

from __future__ import annotations

import json
from datetime import date, datetime, time
from typing import Any

from config.api_errors import detail_error, not_found
from config.serialize import apply_model_update, model_to_dict
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, Q
from map_layers.electricity_feature_admin import (
    list_features as list_gis_features,
)

from .admin_registry import AdminResourceSpec
from .models import DailyReport, DataSource

_AUDIT_SKIP = frozenset({
    'id',
    'pk',
    'created_at',
    'updated_at',
    'created_by',
    'updated_by',
    'created_by_id',
    'updated_by_id',
    'built_at',
})

_PLANT_FIELDS = (
    'id',
    'code',
    'name_ar',
    'name_en',
    'plant_type',
    'fuel_type',
    'governorate',
    'latitude',
    'longitude',
    'operator_company',
    'status',
    'installed_capacity_mw',
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


def _as_time(value: Any) -> time | None:
    if value is None or value == '':
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    text = str(value).strip()
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise detail_error(f'Invalid time format: {value}')


def _parse_optional_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return _as_date(raw)


def _model_pick(instance: Model, keys: tuple[str, ...]) -> dict[str, Any]:
    data = model_to_dict(instance)
    return {k: data[k] for k in keys if k in data}


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
        return spec.model.objects.get(snapshot_date=pk)
    return spec.model.objects.get(pk=pk)


def _admin_save(instance: Model, payload: dict[str, Any], *, partial: bool) -> Model:
    apply_model_update(instance, _writable_payload(payload), partial=partial)
    try:
        instance.full_clean()
    except DjangoValidationError as exc:
        raise detail_error(_validation_error_message(exc)) from exc
    instance.save()
    return instance


def _normalize_report_upsert(data: dict[str, Any]) -> dict[str, Any]:
    if 'report_date' not in data:
        raise detail_error('report_date is required.')
    payload = dict(data)
    payload['report_date'] = _as_date(payload['report_date'], label='report_date')
    if 'reference_hour' in payload:
        payload['reference_hour'] = _as_time(payload.get('reference_hour'))
    if 'peak_generation_time' in payload:
        payload['peak_generation_time'] = _as_time(payload.get('peak_generation_time'))
    payload.setdefault('status', DailyReport.Status.DRAFT)
    payload.setdefault('notes_ar', '')
    payload.setdefault('notes_en', '')
    payload.setdefault('maintenance_groups_ar', '')
    for key in (
        'metrics',
        'governorate_loads',
        'hydro_readings',
        'fuel_tank_readings',
        'generation_unit_readings',
        'generation_incidents',
        'grid_incidents',
    ):
        payload.setdefault(key, [])
    return payload


def _normalize_daily_ops_payload(data: dict[str, Any]) -> dict[str, Any]:
    if 'report_date' not in data:
        raise detail_error('report_date is required.')
    payload = dict(data)
    payload['report_date'] = _as_date(payload['report_date'], label='report_date')
    payload.setdefault('generation', [])
    payload.setdefault('demand', None)
    payload.setdefault('grid_outages', [])
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

    if spec.gis_layer_id:
        payload = list_gis_features(
            spec.gis_layer_id,
            search=search,
            page=page,
            page_size=page_size,
            sort=sort_col,
            direction=sort_dir,
        )
        payload['slug'] = spec.slug
        return payload

    if spec.model is None:
        raise not_found('Unknown resource.')

    allowed_fields = {f.name for f in spec.model._meta.fields}
    if sort_col in allowed_fields and sort_col in spec.list_display:
        ordering = [f'-{sort_col}' if sort_dir == 'desc' else sort_col]
    elif spec.default_sort_column and spec.default_sort_column in allowed_fields:
        default_col = spec.default_sort_column
        ordering = [
            f'-{default_col}' if spec.default_sort_direction == 'desc' else default_col,
        ]
    else:
        ordering = list(spec.model._meta.ordering or ['-pk'])

    qs = spec.model.objects.all().order_by(*ordering)
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
            qs = spec.model.objects.filter(q).order_by(*ordering)

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

