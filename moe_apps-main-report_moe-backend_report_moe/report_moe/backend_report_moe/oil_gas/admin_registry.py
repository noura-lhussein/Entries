from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.db import models
from django.db.models import QuerySet


@dataclass(frozen=True, slots=True)
class AdminResourceSpec:
    slug: str
    label_en: str
    label_ar: str
    group_en: str
    group_ar: str
    model: type[models.Model]
    list_display: tuple[str, ...]
    read_only: bool = False
    lookup_field: str = 'pk'
    """Optional ORM filters applied to list/detail/options querysets."""
    queryset_filters: dict[str, Any] = field(default_factory=dict)
    """Values forced on create (e.g. facility_type for fuel-stations)."""
    default_create_values: dict[str, Any] = field(default_factory=dict)
    """Fields forced read-only in the admin form schema."""
    locked_fields: tuple[str, ...] = ()
    """Fields omitted from the admin form (still on the model)."""
    hidden_fields: tuple[str, ...] = ()

    def base_queryset(self) -> QuerySet:
        qs = self.model.objects.all()
        if self.queryset_filters:
            qs = qs.filter(**self.queryset_filters)
        return qs

    def to_dict(self) -> dict[str, Any]:
        fields = _model_field_schema(self.model)
        if self.hidden_fields:
            hidden = set(self.hidden_fields)
            fields = [entry for entry in fields if entry['name'] not in hidden]
        if self.locked_fields:
            locked = set(self.locked_fields)
            for entry in fields:
                if entry['name'] in locked:
                    entry['read_only'] = True
                    entry['required'] = False
        return {
            'slug': self.slug,
            'label_en': self.label_en,
            'label_ar': self.label_ar,
            'group_en': self.group_en,
            'group_ar': self.group_ar,
            'list_display': list(self.list_display),
            'read_only': self.read_only,
            'lookup_field': self.lookup_field,
            'fields': fields,
            'default_create_values': dict(self.default_create_values),
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
    for model_field in model._meta.fields:
        if model_field.auto_created and not model_field.concrete:
            continue
        entry: dict[str, Any] = {
            'name': model_field.name,
            'type': _field_type_name(field),
            'required': not model_field.null and not model_field.blank and not getattr(field, 'auto_now', False) and not getattr(field, 'auto_now_add', False),
            'read_only': bool(
                getattr(field, 'auto_now', False)
                or getattr(field, 'auto_now_add', False)
                or (model_field.primary_key and model_field.name != 'id')
            ),
        }
        if isinstance(field, models.ForeignKey):
            entry['related_model'] = model_field.related_model._meta.label_lower.split('.')[-1]
            entry['related_slug'] = _slug_for_model(model_field.related_model)
        if getattr(field, 'choices', None):
            entry['choices'] = [{'value': c[0], 'label': str(c[1])} for c in model_field.choices]
        if hasattr(field, 'max_length') and model_field.max_length:
            entry['max_length'] = model_field.max_length
        if isinstance(field, models.DecimalField):
            entry['decimal_places'] = field.decimal_places
        schema.append(entry)
    return schema


def _slug_for_model(model: type[models.Model]) -> str | None:
    for spec in ADMIN_RESOURCES.values():
        if spec.model is model:
            return spec.slug
    return None


# All sector writes moved to report_moe (master_data + Info forms).
ADMIN_RESOURCES: dict[str, AdminResourceSpec] = {}


def get_resource_spec(slug: str) -> AdminResourceSpec | None:
    return ADMIN_RESOURCES.get(slug)
