"""Shared JSON serialization helpers (ported from moeds config.serialize)."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from django.db import models
from django.db.models.fields.files import FieldFile


def _coerce_decimal(value: Any, field: models.DecimalField) -> Decimal | None:
    """Convert JSON numbers to Decimal without float binary artifacts."""
    if value is None or value == '':
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ValueError(f'Invalid decimal for {field.name}') from exc
    if field.decimal_places is not None:
        quant = Decimal(1).scaleb(-field.decimal_places)
        decimal_value = decimal_value.quantize(quant, rounding=ROUND_HALF_UP)
    return decimal_value


def _json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, FieldFile):
        return value.url if value else None
    if isinstance(value, models.Model):
        return value.pk
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _json_value(v) for k, v in value.items()}
    return str(value)


def model_to_dict(instance: models.Model, *, exclude: set[str] | None = None) -> dict[str, Any]:
    skip = exclude or set()
    data: dict[str, Any] = {}
    for field in instance._meta.fields:
        if field.name in skip:
            continue
        data[field.name] = _json_value(
            getattr(instance, field.attname if field.is_relation else field.name)
        )
        if field.is_relation and field.name not in skip:
            attname = field.attname
            if attname != field.name:
                data[attname] = _json_value(getattr(instance, attname))
    return data


def _related_display_labels(related: models.Model) -> tuple[str, str]:
    name_ar = str(getattr(related, 'name_ar', '') or '').strip()
    name_en = str(getattr(related, 'name_en', '') or '').strip()
    fallback = str(related).strip()
    return (name_ar or name_en or fallback, name_en or name_ar or fallback)


def model_to_admin_dict(instance: models.Model, *, exclude: set[str] | None = None) -> dict[str, Any]:
    """Like model_to_dict, plus bilingual labels for ForeignKey columns."""
    data = model_to_dict(instance, exclude=exclude)
    for field in instance._meta.fields:
        if not isinstance(field, models.ForeignKey):
            continue
        if exclude and field.name in exclude:
            continue
        related = getattr(instance, field.name, None)
        if related is None:
            continue
        label_ar, label_en = _related_display_labels(related)
        data[f'{field.name}_label_ar'] = label_ar
        data[f'{field.name}_label_en'] = label_en
    return data


def requires_client_pk(model: type[models.Model]) -> bool:
    """True when the primary key is neither auto-generated nor defaulted.

    `projects_projectgovernorate` / `projects_projectorganization` declare
    `PositiveSmallIntegerField(primary_key=True)` over columns that are NOT identity
    columns, so a create is impossible unless the client supplies the id.
    """
    pk = model._meta.pk
    if pk is None:
        return False
    # AutoFieldMeta makes this cover BigAutoField / SmallAutoField too.
    if isinstance(pk, models.AutoField):
        return False
    return not pk.has_default()


def apply_model_update(
    instance: models.Model,
    payload: dict[str, Any],
    *,
    partial: bool = False,
    allow_pk: bool = False,
) -> models.Model:
    """Assign writable fields from a dict onto a model instance (no save)."""
    del partial  # API parity with moeds; unused
    field_map = {
        f.name: f
        for f in instance._meta.fields
        if allow_pk or not f.primary_key
    }
    for key, value in payload.items():
        if key not in field_map:
            if key.endswith('_id') and key[:-3] in field_map:
                setattr(instance, key, value)
            continue
        field = field_map[key]
        if getattr(field, 'auto_now', False) or getattr(field, 'auto_now_add', False):
            continue
        if field.is_relation:
            setattr(instance, field.attname, value)
        elif isinstance(field, models.DecimalField):
            setattr(instance, key, _coerce_decimal(value, field))
        else:
            setattr(instance, key, value)
    return instance
