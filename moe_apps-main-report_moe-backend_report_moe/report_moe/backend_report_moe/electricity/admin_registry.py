"""Electricity admin resource registry.

All sector writes moved to report_moe (master_data + Info forms).
Registry is empty so moeds admin CRUD returns 404.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import models
from map_layers.electricity_feature_admin import field_schema_for_layer, list_display_for_layer


@dataclass(frozen=True, slots=True)
class AdminResourceSpec:
    slug: str
    label_en: str
    label_ar: str
    group_en: str
    group_ar: str
    list_display: tuple[str, ...]
    model: type[models.Model] | None = None
    gis_layer_id: str | None = None
    read_only: bool = False
    lookup_field: str = 'pk'
    default_sort_column: str | None = None
    default_sort_direction: str = 'desc'

    def to_dict(self) -> dict[str, Any]:
        if self.gis_layer_id:
            fields = field_schema_for_layer(self.gis_layer_id)
            display = list(self.list_display) if self.list_display else list(list_display_for_layer(self.gis_layer_id))
        else:
            assert self.model is not None
            fields = _model_field_schema(self.model)
            display = list(self.list_display)
        return {
            'slug': self.slug,
            'label_en': self.label_en,
            'label_ar': self.label_ar,
            'group_en': self.group_en,
            'group_ar': self.group_ar,
            'list_display': display,
            'read_only': self.read_only,
            'lookup_field': self.lookup_field,
            'default_sort_column': self.default_sort_column,
            'default_sort_direction': self.default_sort_direction,
            'fields': fields,
            'gis_layer_id': self.gis_layer_id,
        }


def _field_type_name(field: models.Field) -> str:
    if getattr(field, 'choices', None):
        return 'choice'
    if isinstance(field, models.ForeignKey):
        return 'foreign_key'
    if isinstance(field, models.BooleanField):
        return 'boolean'
    if isinstance(field, models.DateTimeField):
        return 'datetime'
    if isinstance(field, models.DateField):
        return 'date'
    if isinstance(field, (models.DecimalField, models.FloatField, models.IntegerField, models.PositiveIntegerField)):
        return 'number'
    if isinstance(field, models.TextField):
        return 'textarea'
    return 'string'


def _model_field_schema(model: type[models.Model]) -> list[dict[str, Any]]:
    schema: list[dict[str, Any]] = []
    for field in model._meta.fields:
        if field.auto_created and not field.concrete:
            continue
        entry: dict[str, Any] = {
            'name': field.name,
            'type': _field_type_name(field),
            'required': not field.null and not field.blank and not getattr(field, 'auto_now', False) and not getattr(field, 'auto_now_add', False),
            'read_only': bool(
                getattr(field, 'auto_now', False)
                or getattr(field, 'auto_now_add', False)
                or (field.primary_key and field.name != 'id')
            ),
        }
        if isinstance(field, models.ForeignKey):
            entry['related_model'] = field.related_model._meta.label_lower.split('.')[-1]
            entry['related_slug'] = _slug_for_model(field.related_model)
        if getattr(field, 'choices', None):
            entry['choices'] = [{'value': c[0], 'label': str(c[1])} for c in field.choices]
        if hasattr(field, 'max_length') and field.max_length:
            entry['max_length'] = field.max_length
        if isinstance(field, models.DecimalField):
            entry['decimal_places'] = field.decimal_places
        schema.append(entry)
    return schema


def _slug_for_model(model: type[models.Model]) -> str | None:
    for spec in ADMIN_RESOURCES.values():
        if spec.model is model:
            return spec.slug
    return None


ADMIN_RESOURCES: dict[str, AdminResourceSpec] = {}


def get_resource_spec(slug: str) -> AdminResourceSpec | None:
    return ADMIN_RESOURCES.get(slug)
