"""
Registry of entity Attribute types → master catalogs in schema `moeds`.

Form Builder entity fields are auto-dropdowns; options come from these sources.
ORM tables and GIS features share the same EntityTypeSpec + filter_kwargs pattern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class EntityTypeSpec:
    """One Form Builder entity field type."""

    attr_type: str
    label_en: str
    label_ar: str
    model_label: str
    id_field: str = 'id'
    label_field: str = 'name'
    fallback_label_field: str | None = None
    filter_kwargs: dict[str, Any] = field(default_factory=dict)
    # master_data resource slug for "manage values" UI (optional).
    admin_slug: str | None = None


ENTITY_TYPE_SPECS: dict[str, EntityTypeSpec] = {
    'drinking_station': EntityTypeSpec(
        attr_type='drinking_station',
        label_en='Drinking water station',
        label_ar='محطة مياه شرب',
        model_label='water.DrinkingWaterStation',
        label_field='name',
        admin_slug='drinking-water-stations',
    ),
    'dam': EntityTypeSpec(
        attr_type='dam',
        label_en='Dam',
        label_ar='سد',
        model_label='water.Dam',
        label_field='name',
        admin_slug='dams',
    ),
    'rainfall_station': EntityTypeSpec(
        attr_type='rainfall_station',
        label_en='Rainfall station',
        label_ar='محطة هطول',
        model_label='water.RainfallStation',
        label_field='name',
        admin_slug='rainfall-stations',
    ),
    'rainfall_basin': EntityTypeSpec(
        attr_type='rainfall_basin',
        label_en='Rainfall basin',
        label_ar='حوض هطول',
        model_label='water.RainfallBasin',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='rainfall-basins',
    ),
    'spring': EntityTypeSpec(
        attr_type='spring',
        label_en='Spring',
        label_ar='نبع',
        model_label='map_layers.GisWaterFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'water-springs'},
        admin_slug='springs',
    ),
    'lake': EntityTypeSpec(
        attr_type='lake',
        label_en='Lake',
        label_ar='بحيرة',
        model_label='map_layers.GisWaterFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'water-lakes'},
        admin_slug='lakes',
    ),
    'river': EntityTypeSpec(
        attr_type='river',
        label_en='River',
        label_ar='نهر',
        model_label='map_layers.GisWaterFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'water-rivers'},
        admin_slug='rivers',
    ),
    'stream': EntityTypeSpec(
        attr_type='stream',
        label_en='Stream',
        label_ar='مجرى مائي',
        model_label='map_layers.GisWaterFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'water-streams'},
        admin_slug='streams',
    ),
    'geology_unit': EntityTypeSpec(
        attr_type='geology_unit',
        label_en='Geology unit',
        label_ar='وحدة جيولوجية',
        model_label='map_layers.GisWaterFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'geology-official'},
        admin_slug='gis-geology-official',
    ),
    'ore_product': EntityTypeSpec(
        attr_type='ore_product',
        label_en='Ore product',
        label_ar='منتج خامات',
        model_label='geology.OreProduct',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='ore-products',
    ),
    'power_plant': EntityTypeSpec(
        attr_type='power_plant',
        label_en='Power plant',
        label_ar='محطة توليد',
        model_label='electricity.PowerPlant',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='power-plants',
    ),
    'substation': EntityTypeSpec(
        attr_type='substation',
        label_en='Substation',
        label_ar='محطة تحويل',
        model_label='electricity.Substation',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='substations',
    ),
    'transmission_line': EntityTypeSpec(
        attr_type='transmission_line',
        label_en='Transmission line',
        label_ar='خط نقل',
        model_label='electricity.TransmissionLine',
        label_field='name',
        admin_slug='transmission-lines',
    ),
    'power_gis_substation_66': EntityTypeSpec(
        attr_type='power_gis_substation_66',
        label_en='GIS substation 66 kV',
        label_ar='محطة تحويل GIS 66 ك.ف',
        model_label='map_layers.GisElectricityFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'power-gis-substations-66'},
        admin_slug='gis-substations-66',
    ),
    'power_gis_substation_230': EntityTypeSpec(
        attr_type='power_gis_substation_230',
        label_en='GIS substation 230 kV',
        label_ar='محطة تحويل GIS 230 ك.ف',
        model_label='map_layers.GisElectricityFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'power-gis-substations-230'},
        admin_slug='gis-substations-230',
    ),
    'power_gis_substation_400': EntityTypeSpec(
        attr_type='power_gis_substation_400',
        label_en='GIS substation 400 kV',
        label_ar='محطة تحويل GIS 400 ك.ف',
        model_label='map_layers.GisElectricityFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'power-gis-substations-400'},
        admin_slug='gis-substations-400',
    ),
    'power_gis_renewable': EntityTypeSpec(
        attr_type='power_gis_renewable',
        label_en='Renewable energy site (GIS)',
        label_ar='موقع طاقة متجددة (GIS)',
        model_label='map_layers.GisElectricityFeature',
        label_field='name',
        filter_kwargs={'layer_id': 'power-gis-renewable-sites'},
        admin_slug='gis-renewable-sites',
    ),
    'fuel_tank_station': EntityTypeSpec(
        attr_type='fuel_tank_station',
        label_en='Fuel tank station',
        label_ar='محطة خزانات وقود',
        model_label='electricity.FuelTankStation',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='fuel-tank-stations',
    ),
    'hydro_dam': EntityTypeSpec(
        attr_type='hydro_dam',
        label_en='Hydro dam (daily report)',
        label_ar='سد (تقرير يومي)',
        model_label='electricity.HydroDam',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='hydro-dams',
    ),
    'load_governorate': EntityTypeSpec(
        attr_type='load_governorate',
        label_en='Load governorate',
        label_ar='محافظة (أحمال)',
        model_label='electricity.LoadGovernorate',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='load-governorates',
    ),
    'oil_field': EntityTypeSpec(
        attr_type='oil_field',
        label_en='Oil/gas field',
        label_ar='حقل نفط/غاز',
        model_label='oil_gas.Field',
        label_field='name_ar',
        fallback_label_field='name_en',
        admin_slug='fields',
    ),
    'oil_well': EntityTypeSpec(
        attr_type='oil_well',
        label_en='Oil/gas well',
        label_ar='بئر',
        model_label='oil_gas.Well',
        label_field='well_code',
        fallback_label_field='name_ar',
        admin_slug='wells',
    ),
    'oil_refinery': EntityTypeSpec(
        attr_type='oil_refinery',
        label_en='Refinery',
        label_ar='مصفاة',
        model_label='oil_gas.Refinery',
        label_field='refinery_name',
        fallback_label_field='name_ar',
        admin_slug='refineries',
    ),
    'fuel_station': EntityTypeSpec(
        attr_type='fuel_station',
        label_en='Fuel station',
        label_ar='محطة وقود',
        model_label='oil_gas.Facility',
        label_field='name_ar',
        fallback_label_field='name_en',
        filter_kwargs={'facility_type': 'fuel_station'},
        admin_slug='fuel-stations',
    ),
    'storage_depot': EntityTypeSpec(
        attr_type='storage_depot',
        label_en='Storage depot',
        label_ar='مستودع وقود',
        model_label='oil_gas.Facility',
        label_field='name_ar',
        fallback_label_field='name_en',
        filter_kwargs={'facility_type': 'storage_depot'},
        admin_slug='storage-depots',
    ),
    'pipeline': EntityTypeSpec(
        attr_type='pipeline',
        label_en='Pipeline',
        label_ar='أنبوب نفط',
        model_label='oil_gas.Pipeline',
        label_field='name_ar',
        fallback_label_field='name',
        admin_slug='pipelines',
    ),
}

# Stable ordered list for UI / validation.
ALL_ENTITY_TYPES: tuple[str, ...] = tuple(ENTITY_TYPE_SPECS.keys())


def is_entity_attribute(attr_type: str) -> bool:
    return attr_type in ENTITY_TYPE_SPECS


def get_entity_spec(attr_type: str) -> EntityTypeSpec | None:
    return ENTITY_TYPE_SPECS.get(attr_type)


def _option_label(obj, spec: EntityTypeSpec) -> str:
    primary = getattr(obj, spec.label_field, None)
    if primary is not None and str(primary).strip():
        return str(primary).strip()
    if spec.fallback_label_field:
        secondary = getattr(obj, spec.fallback_label_field, None)
        if secondary is not None and str(secondary).strip():
            return str(secondary).strip()
    return str(getattr(obj, spec.id_field))


def list_entity_options(
    attr_type: str,
    *,
    query: str = '',
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return [{id, label}] for a dropdown entity type."""
    from django.apps import apps
    from django.db import DatabaseError
    from django.db.models import Q

    spec = get_entity_spec(attr_type)
    if spec is None:
        return []
    app_label, model_name = spec.model_label.split('.', 1)
    model = apps.get_model(app_label, model_name)
    try:
        qs = model.objects.all()
        if spec.filter_kwargs:
            qs = qs.filter(**spec.filter_kwargs)
        qs = qs.order_by(spec.label_field, spec.id_field)
        q = (query or '').strip()
        if q:
            label_q = Q(**{f'{spec.label_field}__icontains': q})
            if spec.fallback_label_field:
                label_q |= Q(**{f'{spec.fallback_label_field}__icontains': q})
            qs = qs.filter(label_q)
        rows = []
        for obj in qs[: max(1, min(limit, 500))]:
            pk = getattr(obj, spec.id_field)
            label = _option_label(obj, spec)
            if not label:
                continue
            rows.append({'id': int(pk), 'label': label})
        return rows
    except DatabaseError:
        return []


def batch_entity_labels(
    ids_by_type: dict[str, set[int]],
) -> dict[tuple[str, int], str]:
    """Resolve {(entity_type, id): label} for display in info-rows / tables."""
    from django.apps import apps
    from django.db import DatabaseError

    out: dict[tuple[str, int], str] = {}
    if not ids_by_type:
        return out

    for attr_type, ids in ids_by_type.items():
        if not ids:
            continue
        spec = get_entity_spec(attr_type)
        if spec is None:
            continue
        app_label, model_name = spec.model_label.split('.', 1)
        model = apps.get_model(app_label, model_name)
        try:
            qs = model.objects.filter(pk__in=ids)
            if spec.filter_kwargs:
                qs = qs.filter(**spec.filter_kwargs)
            for obj in qs:
                pk = int(getattr(obj, spec.id_field))
                label = _option_label(obj, spec)
                if label:
                    out[(attr_type, pk)] = label
        except (DatabaseError, TypeError, ValueError):
            continue
    return out


def parse_entity_id(raw_value: Any) -> int | None:
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    if text.isdigit():
        return int(text)
    return None


def apply_entity_to_info(info, attribute, raw_value: str) -> None:
    """Set info.value and entity_type/entity_id from an entity attribute submission."""
    from django.apps import apps
    from django.core.exceptions import ValidationError

    spec = get_entity_spec(attribute.type)
    if spec is None:
        info.value = raw_value
        return
    try:
        entity_id = int(str(raw_value).strip())
    except (TypeError, ValueError) as exc:
        raise ValidationError({'value': 'معرّف الكيان يجب أن يكون رقماً.'}) from exc
    if entity_id < 1:
        raise ValidationError({'value': 'معرّف الكيان غير صالح.'})

    app_label, model_name = spec.model_label.split('.', 1)
    model = apps.get_model(app_label, model_name)
    qs = model.objects.filter(pk=entity_id)
    if spec.filter_kwargs:
        qs = qs.filter(**spec.filter_kwargs)
    if not qs.exists():
        raise ValidationError({'value': 'الكيان المحدد غير موجود.'})

    info.value = str(entity_id)
    info.entity_type = spec.attr_type
    info.entity_id = entity_id
