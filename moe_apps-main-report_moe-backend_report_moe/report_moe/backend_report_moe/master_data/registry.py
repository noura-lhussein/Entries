"""Unified master-data resource registry for report_moe entity catalogs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from django.db import models

from . import gis as gis_admin
from .models import (
    Dam,
    Dataset,
    DatasetResource,
    DrinkingWaterStation,
    FuelTankStation,
    HydroDam,
    LoadGovernorate,
    OilFacility,
    OilField,
    OilPipeline,
    OilRefinery,
    OilWell,
    OreProduct,
    PowerPlant,
    ProjectGovernorate,
    ProjectOrganization,
    RainfallBasin,
    RainfallStation,
    Substation,
    TransmissionLine,
)

Sector = Literal['oil_gas', 'electricity', 'water', 'mineral', 'portal', 'projects']


@dataclass(frozen=True, slots=True)
class AdminResourceSpec:
    slug: str
    label_en: str
    label_ar: str
    group_en: str
    group_ar: str
    sector: Sector
    list_display: tuple[str, ...]
    model: type[models.Model] | None = None
    gis_layer_id: str | None = None
    read_only: bool = False
    lookup_field: str = 'pk'
    default_sort_column: str | None = None
    default_sort_direction: str = 'asc'
    search_fields: tuple[str, ...] = ()
    queryset_filters: dict[str, Any] = field(default_factory=dict)
    default_create_values: dict[str, Any] = field(default_factory=dict)
    locked_fields: tuple[str, ...] = ()
    hidden_fields: tuple[str, ...] = ()
    # Form-builder entity type that opens this resource (optional).
    entity_attr_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        if self.gis_layer_id:
            fields = gis_admin.field_schema_for_layer(self.gis_layer_id)
            display = list(self.list_display) or list(gis_admin.list_display_for_layer(self.gis_layer_id))
        else:
            assert self.model is not None
            fields = _model_field_schema(self.model, hidden=self.hidden_fields, locked=self.locked_fields)
            display = list(self.list_display)
        return {
            'slug': self.slug,
            'label_en': self.label_en,
            'label_ar': self.label_ar,
            'group_en': self.group_en,
            'group_ar': self.group_ar,
            'sector': self.sector,
            'list_display': display,
            'read_only': self.read_only,
            'lookup_field': self.lookup_field,
            'default_sort_column': self.default_sort_column,
            'default_sort_direction': self.default_sort_direction,
            'default_create_values': dict(self.default_create_values),
            'fields': fields,
            'gis_layer_id': self.gis_layer_id,
            'entity_attr_type': self.entity_attr_type,
            'has_map': bool(
                self.gis_layer_id
                or (self.model is not None and _model_has_lat_lon(self.model))
            ),
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
    if isinstance(
        field,
        (
            models.DecimalField,
            models.FloatField,
            models.IntegerField,
            models.PositiveIntegerField,
            models.PositiveSmallIntegerField,
            models.SmallIntegerField,
            models.BigIntegerField,
        ),
    ):
        return 'number'
    if isinstance(field, models.TextField):
        return 'textarea'
    return 'string'


def _model_has_lat_lon(model: type[models.Model]) -> bool:
    names = {f.name for f in model._meta.fields}
    return 'latitude' in names and 'longitude' in names


def _model_field_schema(
    model: type[models.Model],
    *,
    hidden: tuple[str, ...] = (),
    locked: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    hide = set(hidden)
    lock = set(locked)
    schema: list[dict[str, Any]] = []
    for model_field in model._meta.fields:
        if model_field.auto_created and not model_field.concrete:
            continue
        if model_field.name in hide:
            continue
        entry: dict[str, Any] = {
            'name': model_field.name,
            'type': _field_type_name(field),
            'required': (
                not model_field.null
                and not model_field.blank
                and not getattr(field, 'auto_now', False)
                and not getattr(field, 'auto_now_add', False)
            ),
            'read_only': bool(
                model_field.name in lock
                or getattr(field, 'auto_now', False)
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


def _res(
    slug: str,
    label_en: str,
    label_ar: str,
    *,
    sector: Sector,
    group_en: str,
    group_ar: str,
    list_display: tuple[str, ...],
    model: type[models.Model] | None = None,
    gis_layer_id: str | None = None,
    search_fields: tuple[str, ...] = (),
    queryset_filters: dict[str, Any] | None = None,
    default_create_values: dict[str, Any] | None = None,
    locked_fields: tuple[str, ...] = (),
    hidden_fields: tuple[str, ...] = (),
    entity_attr_type: str | None = None,
    default_sort_column: str | None = None,
    read_only: bool = False,
) -> AdminResourceSpec:
    return AdminResourceSpec(
        slug=slug,
        label_en=label_en,
        label_ar=label_ar,
        group_en=group_en,
        group_ar=group_ar,
        sector=sector,
        list_display=list_display,
        model=model,
        gis_layer_id=gis_layer_id,
        search_fields=search_fields,
        queryset_filters=queryset_filters or {},
        default_create_values=default_create_values or {},
        locked_fields=locked_fields,
        hidden_fields=hidden_fields,
        entity_attr_type=entity_attr_type,
        default_sort_column=default_sort_column,
        read_only=read_only,
    )


_ELEC = ('Electricity', 'الكهرباء')
_WATER = ('Water resources', 'الموارد المائية')
_OIL = ('Petroleum', 'البترول')
_MIN = ('Mineral resources', 'الثروة المعدنية')
_PORTAL = ('Data library', 'مكتبة البيانات')
_PROJECTS = ('Institutions', 'المؤسسات')


ADMIN_RESOURCES: dict[str, AdminResourceSpec] = {
    # ---- Electricity ORM ----
    'power-plants': _res(
        'power-plants', 'Generation plants', 'محطات التوليد',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=PowerPlant,
        list_display=('name_ar', 'code', 'plant_type', 'status', 'installed_capacity_mw'),
        search_fields=('name_ar', 'name_en', 'code', 'governorate'),
        entity_attr_type='power_plant',
    ),
    'substations': _res(
        'substations', 'Substations (operational)', 'محطات التحويل (تشغيلي)',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=Substation,
        list_display=('name_ar', 'code', 'role', 'status', 'voltage_kv'),
        search_fields=('name_ar', 'name_en', 'code', 'governorate'),
        entity_attr_type='substation',
    ),
    'transmission-lines': _res(
        'transmission-lines', 'Transmission lines (operational)', 'خطوط النقل (تشغيلي)',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=TransmissionLine,
        list_display=('name', 'status', 'capacity_mw', 'voltage_kv'),
        search_fields=('name', 'source_location', 'destination_location'),
        entity_attr_type='transmission_line',
    ),
    'fuel-tank-stations': _res(
        'fuel-tank-stations', 'Fuel tank stations', 'محطات خزانات الوقود',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=FuelTankStation,
        list_display=('name_ar', 'name_en', 'code', 'max_capacity_tons'),
        search_fields=('name_ar', 'name_en', 'code'),
        entity_attr_type='fuel_tank_station',
    ),
    'hydro-dams': _res(
        'hydro-dams', 'Hydro dams (daily report)', 'سدود (تقرير يومي)',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=HydroDam,
        list_display=('name_ar', 'name_en', 'code'),
        search_fields=('name_ar', 'name_en', 'code'),
        entity_attr_type='hydro_dam',
    ),
    'load-governorates': _res(
        'load-governorates', 'Load governorates', 'محافظات الأحمال',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        model=LoadGovernorate,
        list_display=('name_ar', 'name_en', 'code'),
        search_fields=('name_ar', 'name_en', 'code'),
        entity_attr_type='load_governorate',
    ),
    # ---- Electricity GIS ----
    'gis-substations-400': _res(
        'gis-substations-400', '400 kV substations', 'محطات 400 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-substations-400',
        list_display=('name', 'status', 'latitude', 'longitude'),
        entity_attr_type='power_gis_substation_400',
    ),
    'gis-substations-230': _res(
        'gis-substations-230', '230 kV substations', 'محطات 230 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-substations-230',
        list_display=('name', 'status', 'latitude', 'longitude'),
        entity_attr_type='power_gis_substation_230',
    ),
    'gis-substations-66': _res(
        'gis-substations-66', '66 kV substations', 'محطات 66 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-substations-66',
        list_display=('name', 'status', 'latitude', 'longitude'),
        entity_attr_type='power_gis_substation_66',
    ),
    'gis-renewable-sites': _res(
        'gis-renewable-sites', 'Renewable energy sites', 'مواقع الطاقات المتجددة',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-renewable-sites',
        list_display=('name', 'site_type', 'latitude', 'longitude'),
        entity_attr_type='power_gis_renewable',
    ),
    'gis-lines-400': _res(
        'gis-lines-400', '400 kV lines', 'خطوط 400 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-lines-400',
        list_display=('name', 'status', 'latitude', 'longitude'),
    ),
    'gis-lines-230': _res(
        'gis-lines-230', '230 kV lines', 'خطوط 230 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-lines-230',
        list_display=('name', 'status', 'latitude', 'longitude'),
    ),
    'gis-lines-66': _res(
        'gis-lines-66', '66 kV lines', 'خطوط 66 ك.ف',
        sector='electricity', group_en=_ELEC[0], group_ar=_ELEC[1],
        gis_layer_id='power-gis-lines-66',
        list_display=('name', 'status', 'latitude', 'longitude'),
    ),
    # ---- Water ORM ----
    'drinking-water-stations': _res(
        'drinking-water-stations', 'Drinking water stations', 'محطات مياه الشرب',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        model=DrinkingWaterStation,
        list_display=('station_code', 'name', 'governorate', 'latitude', 'longitude', 'is_operational'),
        search_fields=('station_code', 'name', 'governorate', 'district'),
        entity_attr_type='drinking_station',
    ),
    'dams': _res(
        'dams', 'Dams', 'السدود',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        model=Dam,
        list_display=('name', 'governorate', 'latitude', 'longitude', 'max_storage_mcm', 'purpose'),
        search_fields=('name', 'governorate', 'purpose'),
        entity_attr_type='dam',
    ),
    'rainfall-basins': _res(
        'rainfall-basins', 'Rainfall basins', 'أحواض الهطول',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        model=RainfallBasin,
        list_display=('slug', 'name_en', 'name_ar', 'latitude', 'longitude', 'area_km2'),
        search_fields=('slug', 'name_en', 'name_ar'),
        entity_attr_type='rainfall_basin',
    ),
    'rainfall-stations': _res(
        'rainfall-stations', 'Rainfall stations', 'محطات الهطول',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        model=RainfallStation,
        list_display=('name', 'basin', 'governorate', 'latitude', 'longitude'),
        search_fields=('name', 'governorate'),
        entity_attr_type='rainfall_station',
    ),
    # ---- Water GIS ----
    'lakes': _res(
        'lakes', 'Lakes', 'البحيرات',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        gis_layer_id='water-lakes',
        list_display=('name', 'governorate_name', 'latitude', 'longitude'),
        entity_attr_type='lake',
    ),
    'rivers': _res(
        'rivers', 'Rivers', 'الأنهار',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        gis_layer_id='water-rivers',
        list_display=('name', 'river_type', 'latitude', 'longitude'),
        entity_attr_type='river',
    ),
    'streams': _res(
        'streams', 'Streams', 'المسيلات',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        gis_layer_id='water-streams',
        list_display=('name', 'arc_id', 'latitude', 'longitude'),
        entity_attr_type='stream',
    ),
    'springs': _res(
        'springs', 'Springs', 'الينابيع',
        sector='water', group_en=_WATER[0], group_ar=_WATER[1],
        gis_layer_id='water-springs',
        list_display=('name', 'governorate_name', 'latitude', 'longitude', 'elevation_m'),
        entity_attr_type='spring',
    ),
    # ---- Mineral / geology GIS ----
    'gis-geology-official': _res(
        'gis-geology-official', 'Geology units (official)', 'الوحدات الجيولوجية',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-official',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
        entity_attr_type='geology_unit',
    ),
    'gis-geology-era': _res(
        'gis-geology-era', 'Geology by era', 'الجيولوجيا حسب العصر',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-era',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'gis-geology-cenozoic': _res(
        'gis-geology-cenozoic', 'Cenozoic units', 'وحدات حقبة الحياة الحديثة',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-cenozoic',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'gis-geology-quaternary': _res(
        'gis-geology-quaternary', 'Quaternary units', 'وحدات رباعي',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-quaternary',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'gis-geology-mesozoic': _res(
        'gis-geology-mesozoic', 'Mesozoic units', 'وحدات حقبة الحياة الوسطى',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-mesozoic',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'gis-geology-sedimentary': _res(
        'gis-geology-sedimentary', 'Sedimentary units', 'وحدات رسوبية',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-sedimentary',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'gis-geology-volcanic': _res(
        'gis-geology-volcanic', 'Volcanic units', 'وحدات بركانية',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        gis_layer_id='geology-volcanic',
        list_display=('name', 'era', 'litho_type', 'latitude', 'longitude'),
    ),
    'ore-products': _res(
        'ore-products', 'Ore products', 'منتجات الخامات',
        sector='mineral', group_en=_MIN[0], group_ar=_MIN[1],
        model=OreProduct,
        list_display=('name_ar', 'name_en', 'production_type', 'unit', 'sort_order'),
        search_fields=('name_ar', 'name_en'),
        entity_attr_type='ore_product',
    ),
    # ---- Oil & gas ----
    'fields': _res(
        'fields', 'Oil fields', 'حقول النفط',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilField,
        list_display=('name_ar', 'name_en', 'code', 'field_type', 'governorate', 'status', 'latitude', 'longitude'),
        search_fields=('name_ar', 'name_en', 'code', 'governorate'),
        entity_attr_type='oil_field',
    ),
    'wells': _res(
        'wells', 'Oil wells', 'آبار النفط',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilWell,
        list_display=('name_ar', 'name_en', 'well_code', 'field', 'well_type', 'status', 'latitude', 'longitude'),
        search_fields=('name_ar', 'name_en', 'well_code', 'well_type'),
        entity_attr_type='oil_well',
    ),
    'refineries': _res(
        'refineries', 'Refineries', 'المصافي',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilRefinery,
        list_display=('name_ar', 'refinery_name', 'governorate', 'status', 'latitude', 'longitude'),
        search_fields=('name_ar', 'refinery_name', 'governorate'),
        entity_attr_type='oil_refinery',
    ),
    'pipelines': _res(
        'pipelines', 'Pipelines', 'خطوط الأنابيب',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilPipeline,
        list_display=(
            'name', 'status', 'length_km', 'source_location', 'destination_location',
            'source_latitude', 'source_longitude', 'dest_latitude', 'dest_longitude',
        ),
        search_fields=('name', 'name_ar', 'source_location', 'destination_location'),
        entity_attr_type='pipeline',
    ),
    'fuel-stations': _res(
        'fuel-stations', 'Fuel stations', 'محطات الوقود',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilFacility,
        list_display=('name_ar', 'name_en', 'code', 'governorate', 'location', 'status', 'latitude', 'longitude'),
        search_fields=('name_ar', 'name_en', 'code', 'governorate', 'location'),
        queryset_filters={'facility_type': 'fuel_station'},
        default_create_values={'facility_type': 'fuel_station', 'sector': 'oil-gas'},
        locked_fields=('facility_type', 'sector'),
        entity_attr_type='fuel_station',
    ),
    'storage-depots': _res(
        'storage-depots', 'Storage depots', 'مستودعات الوقود',
        sector='oil_gas', group_en=_OIL[0], group_ar=_OIL[1],
        model=OilFacility,
        list_display=('name_ar', 'name_en', 'code', 'governorate', 'location', 'status', 'latitude', 'longitude'),
        search_fields=('name_ar', 'name_en', 'code', 'governorate', 'location'),
        queryset_filters={'facility_type': 'storage_depot'},
        default_create_values={'facility_type': 'storage_depot', 'sector': 'oil-gas'},
        locked_fields=('facility_type', 'sector'),
        entity_attr_type='storage_depot',
    ),
    # ---- Portal datasets ----
    'datasets': _res(
        'datasets', 'Datasets', 'مجموعات البيانات',
        sector='portal', group_en=_PORTAL[0], group_ar=_PORTAL[1],
        model=Dataset,
        list_display=('title_en', 'title_ar', 'slug', 'sector', 'status', 'is_active'),
        search_fields=('title_en', 'title_ar', 'slug', 'sector'),
        hidden_fields=('download_count', 'view_count'),
    ),
    'dataset-resources': _res(
        'dataset-resources', 'Dataset resources', 'ملفات مجموعات البيانات',
        sector='portal', group_en=_PORTAL[0], group_ar=_PORTAL[1],
        model=DatasetResource,
        list_display=('dataset', 'file', 'sort_order', 'created_at'),
        search_fields=('file',),
    ),
    # ---- Projects / institutions ----
    'project-organizations': _res(
        'project-organizations', 'Organizations / institutions', 'المؤسسات',
        sector='projects', group_en=_PROJECTS[0], group_ar=_PROJECTS[1],
        model=ProjectOrganization,
        list_display=('id', 'slug', 'acronym', 'name_en', 'governorate'),
        search_fields=('slug', 'acronym', 'name_en'),
    ),
    'project-governorates': _res(
        'project-governorates', 'Governorates (portal)', 'المحافظات (بوابة)',
        sector='projects', group_en=_PROJECTS[0], group_ar=_PROJECTS[1],
        model=ProjectGovernorate,
        list_display=('id', 'pcode', 'name_en', 'name_ar'),
        search_fields=('pcode', 'name_en', 'name_ar'),
    ),
}


def get_resource_spec(slug: str) -> AdminResourceSpec | None:
    return ADMIN_RESOURCES.get(slug)


def get_resource_by_entity_type(attr_type: str) -> AdminResourceSpec | None:
    for spec in ADMIN_RESOURCES.values():
        if spec.entity_attr_type == attr_type:
            return spec
    return None


def registry_payload(*, allowed_sectors: set[Sector] | None = None) -> dict[str, Any]:
    resources = []
    groups: dict[str, dict[str, Any]] = {}
    for spec in ADMIN_RESOURCES.values():
        if allowed_sectors is not None and spec.sector not in allowed_sectors:
            continue
        resources.append(spec.to_dict())
        key = spec.group_en
        if key not in groups:
            groups[key] = {
                'group_en': spec.group_en,
                'group_ar': spec.group_ar,
                'sector': spec.sector,
                'resources': [],
            }
        groups[key]['resources'].append(spec.slug)
    return {
        'resources': resources,
        'groups': list(groups.values()),
    }
