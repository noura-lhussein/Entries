"""Water endpoints.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`. Helpers live in `admin_support.py`.

The rainfall dashboard is Info-only (accepted dynamic_forms rows + station/basin
master tables for map/filters). Dams remain hybrid: KPIs from Info with legacy
map/filter fallback when entity-level Info is missing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from accounts.drf_permissions import CanAccessWater
from config.api_errors import Gone, detail_error, not_found
from config.serialize import model_to_dict
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .admin_registry import ADMIN_RESOURCES, get_resource_spec
from .admin_support import (
    _admin_save,
    _apply_audit,
    _get_admin_object,
    _json_body,
    _qp,
    build_admin_list_payload,
)
from .dams_dashboard import build_dams_dashboard_payload
from .drinking_water_admin import get_drinking_water_station
from .drinking_water_dashboard import (
    _parse_bool_choices,
    _parse_choice_filter,
    build_drinking_water_dashboard_payload,
    list_drinking_water_stations,
)
from .import_services import get_water_import_status
from .info_dashboard import build_dams_map_catalog_info

_ENTRY_MOVED = (
    "Water daily entry / imports moved to report_moe Form Builder / Info. "
    "Use report_moe UI/API."
)
_PDF_FORMATS = ("pdf", "application/pdf")
_XLSX_FORMATS = (
    "xlsx",
    "excel",
    "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# Drinking-water filters, grouped by how their raw value is interpreted. Listing
# them beats twenty-odd near-identical keyword arguments at every call site.
_BOOL_FILTERS = (
    "station_working",
    "boosting_station",
    "well_station",
    "filtration_station",
    "needs_solar_power",
    "grid_power",
    "previously_rehabilitated",
    "public_grid_supply",
    "grid_connection_working",
    "solar_power_available",
    "alternative_power_source",
    "needs_solar_installation",
    "solar_space_available",
)
_TEXT_FILTERS = (
    "governorate",
    "district",
    "subdistrict",
    "org_unit",
    "community",
    "search",
)
_CHOICE_FILTERS = {
    "safety_procedures": ("no", "partially", "yes"),
    "electrical_connection_efficiency": ("1", "2", "3"),
}


class ServiceUnavailable(APIException):
    """503, matching what the template endpoints answered before."""

    status_code = 503


def _int_or_none(raw: str | None) -> int | None:
    value = (raw or "").strip()
    return int(value) if value.isdigit() else None


def _text(request, key: str) -> str | None:
    return (request.query_params.get(key) or "").strip() or None


def _drinking_filters(request) -> dict[str, Any]:
    filters: dict[str, Any] = {k: _text(request, k) for k in _TEXT_FILTERS}
    filters["enrollment_year"] = _int_or_none(request.query_params.get("enrollment_year"))
    for key in _BOOL_FILTERS:
        filters[key] = _parse_bool_choices(request.query_params.get(key))
    for key, choices in _CHOICE_FILTERS.items():
        filters[key] = _parse_choice_filter(request.query_params.get(key), choices)
    return filters


def _spec_or_404(slug: str):
    spec = get_resource_spec(slug)
    if not spec:
        raise not_found("Unknown resource.")
    return spec


def _facts_or_404(payload, missing: str):
    if payload is None:
        raise not_found(missing)
    return Response(payload)


def _read_only(message: str) -> Response:
    return Response({"detail": message}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


def _template(builder):
    try:
        return builder()
    except RuntimeError as exc:
        raise ServiceUnavailable(str(exc))


# ── Dashboards ───────────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def sector_info_dashboard(request):
    """Info-first sector KPI strip (national water title)."""
    from water.info_dashboard import build_water_info_sector_payload

    return Response(
        build_water_info_sector_payload(year=_int_or_none(request.query_params.get("year")))
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def rainfall_dashboard(request):
    from water.info_dashboard import build_rainfall_info_dashboard
    from water.models import RainfallBasin, RainfallStation

    year_int = _int_or_none(request.query_params.get("year"))
    basin_slug = _text(request, "basin")
    gov = _text(request, "governorate")

    info_payload = build_rainfall_info_dashboard(
        year=year_int, basin_slug=basin_slug, governorate=gov
    )
    if info_payload is not None:
        return Response(info_payload)

    basins = list(
        RainfallBasin.objects.order_by("name_en").values("slug", "name_en", "name_ar")
    )
    gov_qs = RainfallStation.objects.exclude(governorate="")
    if basin_slug:
        gov_qs = gov_qs.filter(basin__slug=basin_slug)
    governorates = sorted(gov_qs.values_list("governorate", flat=True).order_by().distinct())
    return Response(
        {
            "status": "empty",
            "source": "dynamic_forms",
            "filters": {
                "years": [],
                "basins": basins,
                "governorates": governorates,
            },
            "selected_year": year_int,
            "selected_basin": basin_slug,
            "selected_governorate": gov,
            "kpis": [],
            "insights": [
                {
                    "id": "empty",
                    "text_en": "No accepted rainfall Info yet for this scope.",
                    "text_ar": "لا توجد بيانات هطول معتمدة (Info) لهذا النطاق بعد.",
                    "severity": "info",
                }
            ],
            "charts": {},
            "map": {"stations": [], "basin_choropleth": None},
        }
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def dams_dashboard(request):
    from water.info_dashboard import build_dams_info_dashboard

    year_int = _int_or_none(request.query_params.get("year"))
    gov = _text(request, "governorate")

    info_payload = build_dams_info_dashboard(year=year_int, governorate=gov)
    legacy_map = build_dams_dashboard_payload(
        year=(info_payload or {}).get("selected_year") or year_int, governorate=gov
    )
    if info_payload is not None:
        if not info_payload.get("map", {}).get("dams"):
            info_payload["map"] = legacy_map.get("map") or {"dams": []}
        info_payload["filters"] = legacy_map.get("filters") or info_payload.get("filters")
        return Response(info_payload)

    # build_dams_info_dashboard bails out for any governorate filter, so fall back
    # to the legacy DamStorageReading aggregation, which does support it, instead
    # of reporting "no data imported" when readings actually exist.
    if legacy_map.get("status") == "ready":
        return Response(legacy_map)
    return Response(
        {
            "status": "empty",
            "source": "dynamic_forms",
            "filters": legacy_map.get("filters") or {"years": [], "governorates": []},
            "selected_year": legacy_map.get("selected_year"),
            "selected_governorate": gov,
            "kpis": [],
            "insights": [],
            "charts": {},
            "map": legacy_map.get("map") or {"dams": []},
        }
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def dams_map_catalog(request):
    return Response(build_dams_map_catalog_info())


@api_view(["GET"])
@permission_classes([CanAccessWater])
def euphrates_dashboard(request):
    from water.info_dashboard import build_euphrates_info_dashboard

    month_val = _text(request, "month")
    info_payload = build_euphrates_info_dashboard(month=month_val)
    if info_payload is not None:
        return Response(info_payload)
    return Response(
        {
            "status": "empty",
            "source": "dynamic_forms",
            "report_label": "",
            "filters": {"months": []},
            "selected_month": month_val,
            "kpis": [],
            "insights": [],
            "charts": {},
            "month_summary": {},
            "executive": {
                "labels": [],
                "inflow": {"values": []},
                "generation": {"values": []},
                "storage": {"values": []},
            },
            "dams": [],
            "readings_table": [],
        }
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def drinking_water_dashboard(request):
    from water.info_dashboard import apply_drinking_info_kpis

    payload = build_drinking_water_dashboard_payload(**_drinking_filters(request))
    return Response(apply_drinking_info_kpis(payload))


@api_view(["GET"])
@permission_classes([CanAccessWater])
def drinking_water_stations(request):
    return Response(
        list_drinking_water_stations(
            offset=int(request.query_params.get("offset") or 0),
            limit=int(request.query_params.get("limit") or 50),
            **_drinking_filters(request),
        )
    )


# ── Entity report facts ──────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def drinking_water_station_report_facts(request, station_id: int):
    from .report_forms_read import drinking_station_with_report_facts

    return _facts_or_404(
        drinking_station_with_report_facts(station_id), "Station not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def dam_report_facts(request, dam_id: int):
    from .report_forms_read import dam_with_report_facts

    return _facts_or_404(dam_with_report_facts(dam_id), "Dam not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def rainfall_station_report_facts(request, station_id: int):
    from .report_forms_read import rainfall_station_with_report_facts

    return _facts_or_404(
        rainfall_station_with_report_facts(station_id), "Station not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def rainfall_basin_report_facts(request, basin_id: int):
    from .report_forms_read import rainfall_basin_with_report_facts

    return _facts_or_404(rainfall_basin_with_report_facts(basin_id), "Basin not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def spring_report_facts(request, feature_id: int):
    from .report_forms_read import spring_with_report_facts

    return _facts_or_404(spring_with_report_facts(feature_id), "Spring not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def lake_report_facts(request, feature_id: int):
    from .report_forms_read import lake_with_report_facts

    return _facts_or_404(lake_with_report_facts(feature_id), "Lake not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def river_report_facts(request, feature_id: int):
    from .report_forms_read import river_with_report_facts

    return _facts_or_404(river_with_report_facts(feature_id), "River not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def stream_report_facts(request, feature_id: int):
    from .report_forms_read import stream_with_report_facts

    return _facts_or_404(stream_with_report_facts(feature_id), "Stream not found.")


@api_view(["GET"])
@permission_classes([CanAccessWater])
def geology_unit_report_facts(request, feature_id: int):
    from .report_forms_read import geology_unit_with_report_facts

    return _facts_or_404(
        geology_unit_with_report_facts(feature_id), "Geology unit not found."
    )


# ── Exports ──────────────────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def report_export(request):
    """Per-section water dashboard export (Excel / PDF) for water viewers."""
    from .report_export import export_water_dashboard_xlsx
    from .report_pdf import export_water_report_pdf

    section = (_qp(request, "section") or "").strip().lower()
    if not section:
        raise detail_error(
            "section query param required (rainfall|dams|euphrates|drinking-water)."
        )
    kwargs = {
        "section": section,
        "year": _int_or_none(_qp(request, "year")),
        "month": _text(request, "month"),
        "basin": _text(request, "basin"),
        "governorate": _text(request, "governorate"),
    }
    fmt = (_qp(request, "format") or "xlsx").strip().lower()
    if fmt in _PDF_FORMATS:
        return export_water_report_pdf(**kwargs)
    if fmt in _XLSX_FORMATS:
        return export_water_dashboard_xlsx(**kwargs)
    raise detail_error("Query parameter format must be xlsx or pdf.")


# ── Admin: status / lookups ──────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def import_status(request):
    return Response(get_water_import_status())


@api_view(["GET"])
@permission_classes([CanAccessWater])
def lookups(request):
    from .manual_entry import get_lookups

    return Response(get_lookups())


# ── Admin: imports / clears (all retired) ────────────────────────────────────


@api_view(["POST"])
@permission_classes([CanAccessWater])
@parser_classes([MultiPartParser, FormParser])
def import_moved(request, **kwargs):
    """Every import and clear route answers the same 410."""
    raise Gone(_ENTRY_MOVED)


# ── Admin: exports / templates ───────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def export_drinking_water_survey(request):
    from .drinking_water_survey_export import drinking_water_survey_export_response

    return _template(drinking_water_survey_export_response)


@api_view(["GET"])
@permission_classes([CanAccessWater])
def template_rainfall(request):
    from .template_generator import rainfall_template_response

    return _template(rainfall_template_response)


@api_view(["GET"])
@permission_classes([CanAccessWater])
def template_dams_metadata(request):
    from .template_generator import dam_metadata_template_response

    return _template(dam_metadata_template_response)


@api_view(["GET"])
@permission_classes([CanAccessWater])
def template_dams_storage(request):
    from .template_generator import dam_storage_template_response

    return _template(dam_storage_template_response)


@api_view(["GET"])
@permission_classes([CanAccessWater])
def template_euphrates(request):
    from .template_generator import euphrates_template_response

    return _template(euphrates_template_response)


@api_view(["GET"])
@permission_classes([CanAccessWater])
def template_drinking_water_survey(request):
    from .drinking_water_survey_export import drinking_water_survey_template_response

    return _template(drinking_water_survey_template_response)


# ── Admin: manual daily entry (reads live, writes retired) ───────────────────


@api_view(["GET", "POST"])
@permission_classes([CanAccessWater])
def euphrates_daily(request):
    from .manual_entry import get_euphrates_reading

    if request.method == "POST":
        raise Gone(_ENTRY_MOVED)
    try:
        reading_date = datetime.strptime(
            (request.query_params.get("date") or "").strip(), "%Y-%m-%d"
        ).date()
    except ValueError:
        raise detail_error("Invalid date.")
    return Response({"reading": get_euphrates_reading(reading_date)})


@api_view(["POST"])
@permission_classes([CanAccessWater])
def dam_storage_daily(request):
    raise Gone(_ENTRY_MOVED)


@api_view(["POST"])
@permission_classes([CanAccessWater])
def rainfall_daily(request):
    raise Gone(_ENTRY_MOVED)


@api_view(["GET", "POST"])
@permission_classes([CanAccessWater])
def drinking_water_daily(request):
    if request.method == "POST":
        raise Gone(_ENTRY_MOVED)
    try:
        station_pk = int(request.query_params.get("station_id"))
    except (TypeError, ValueError):
        raise detail_error("Invalid station_id.")
    return Response({"station": get_drinking_water_station(station_pk)})


# ── Admin registry CRUD ──────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessWater])
def admin_registry(request):
    groups: dict[str, dict] = {}
    for spec in ADMIN_RESOURCES.values():
        group = groups.setdefault(
            spec.group_en,
            {"group_en": spec.group_en, "group_ar": spec.group_ar, "resources": []},
        )
        group["resources"].append(spec.slug)
    return Response(
        {
            "resources": [spec.to_dict() for spec in ADMIN_RESOURCES.values()],
            "groups": list(groups.values()),
        }
    )


@api_view(["GET"])
@permission_classes([CanAccessWater])
def admin_options(request, slug: str):
    spec = _spec_or_404(slug)
    if spec.gis_layer_id or spec.model is None:
        return Response({"options": []})
    options = []
    for row in spec.model.objects.all()[:300]:
        pk_val = getattr(row, spec.lookup_field, row.pk)
        if spec.lookup_field == "snapshot_date":
            pk_val = row.snapshot_date.isoformat()
        options.append({"value": pk_val, "label": str(row)})
    return Response({"options": options})


@api_view(["GET", "POST"])
@permission_classes([CanAccessWater])
def admin_list(request, slug: str):
    spec = _spec_or_404(slug)
    if request.method == "GET":
        return Response(build_admin_list_payload(request, spec))

    if spec.read_only:
        return _read_only("This resource is read-only.")
    if spec.gis_layer_id:
        return _read_only("GIS feature writes moved to report_moe.")
    if spec.model is None:
        raise not_found("Unknown resource.")
    instance = _admin_save(spec.model(), _json_body(request), partial=False)
    _apply_audit(instance, request.user)
    return Response(model_to_dict(instance), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([CanAccessWater])
def admin_detail(request, slug: str, pk: str):
    from map_layers.water_feature_admin import get_feature as get_gis_feature

    spec = _spec_or_404(slug)

    if request.method == "GET":
        if spec.gis_layer_id:
            return Response(get_gis_feature(spec.gis_layer_id, pk))
        try:
            return Response(model_to_dict(_get_admin_object(spec, pk)))
        except Exception as exc:  # noqa: BLE001 — any lookup failure is a miss
            raise not_found("Not found.") from exc

    if spec.read_only:
        return _read_only("This resource is read-only.")
    if spec.gis_layer_id:
        return _read_only("GIS feature writes moved to report_moe.")
    try:
        instance = _get_admin_object(spec, pk)
    except Exception as exc:  # noqa: BLE001
        raise not_found("Not found.") from exc

    if request.method == "DELETE":
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    instance = _admin_save(instance, _json_body(request), partial=True)
    _apply_audit(instance, request.user)
    return Response(model_to_dict(instance))
