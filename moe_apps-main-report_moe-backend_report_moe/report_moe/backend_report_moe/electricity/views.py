"""Electricity endpoints.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`. Helpers live in `admin_support.py`.

Daily entry answers 410: electricity readings are entered through report_moe's
Form Builder and read back from accepted Info, which is now the same backend.
"""

from __future__ import annotations

from accounts.drf_permissions import CanAccessElectricity
from config.api_errors import Gone, detail_error, not_found
from config.serialize import model_to_dict
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .admin_registry import ADMIN_RESOURCES, get_resource_spec
from .admin_support import (
    _PLANT_FIELDS,
    _admin_save,
    _apply_audit,
    _as_date,
    _get_admin_object,
    _json_body,
    _model_pick,
    _parse_optional_date,
    _qp,
    build_admin_list_payload,
)
from .info_catalog import build_electricity_info_catalog
from .info_dashboard import build_info_dashboard_payload, build_info_metric_trend
from .map_layers import fetch_electricity_layer_geojson
from .models import DailyReport
from .operational_models import OperationalTarget, PowerPlant

_DAILY_ENTRY_MOVED = (
    "Daily electricity entry moved to report_moe Form Builder / Info. "
    "Use report_moe UI/API."
)
_PDF_FORMATS = ("pdf", "application/pdf")
_XLSX_FORMATS = (
    "xlsx",
    "excel",
    "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)


def _spec_or_404(slug: str):
    spec = get_resource_spec(slug)
    if not spec:
        raise not_found("Unknown resource.")
    return spec


def _required_date(request):
    raw = _qp(request, "date")
    if not raw:
        raise detail_error("date query param required (YYYY-MM-DD).")
    return _as_date(raw)


def _facts_or_404(payload, missing: str):
    if payload is None:
        raise not_found(missing)
    return Response(payload)


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def info_catalog(request):
    """Accepted electricity Info rows for the portal Data page (not Dataset)."""
    return Response(build_electricity_info_catalog())


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def dashboard(request):
    """Portal dashboard from accepted Info only (not DailyReport)."""
    period = (_qp(request, "period") or "day").lower()
    if period not in {"day", "month"}:
        raise detail_error("Invalid period. Use day or month.")

    if period == "month":
        month_param = _qp(request, "month")
        month = None
        if month_param:
            try:
                year_str, month_str = month_param.split("-", 1)
                month_num = int(month_str)
                if month_num < 1 or month_num > 12:
                    raise ValueError
                month = f"{int(year_str)}-{month_num:02d}"
            except ValueError as exc:
                raise detail_error("Invalid month format. Use YYYY-MM.") from exc
        return Response(build_info_dashboard_payload(period="month", month=month))

    return Response(
        build_info_dashboard_payload(
            period="day", report_date=_parse_optional_date(_qp(request, "date"))
        )
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def trend(request, metric_key: str):
    return Response(
        build_info_metric_trend(
            metric_key,
            days=int(_qp(request, "days") or 30),
            end_date=_parse_optional_date(_qp(request, "date")),
        )
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def report_dates(request):
    from .services import list_available_dates

    return Response({"dates": list_available_dates()})


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def report_list(request):
    reports = DailyReport.objects.order_by("-report_date")[:60]
    return Response(
        [
            {
                "id": r.id,
                "report_date": r.report_date.isoformat(),
                "status": r.status,
                "source_file": r.source_file,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in reports
        ]
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def report_detail(request):
    from .services import build_report_detail_payload

    payload = build_report_detail_payload(_required_date(request))
    if not payload:
        raise not_found("Report not found.")
    return Response(payload)


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def report_export(request):
    from .report_export import export_electricity_report_xlsx
    from .report_pdf import export_electricity_report_pdf

    parsed = _required_date(request)
    fmt = (_qp(request, "format") or "xlsx").strip().lower()
    if fmt in _PDF_FORMATS:
        response = export_electricity_report_pdf(parsed)
    elif fmt in _XLSX_FORMATS:
        response = export_electricity_report_xlsx(parsed)
    else:
        raise detail_error("Query parameter format must be xlsx or pdf.")
    if response is None:
        raise not_found("Report not found.")
    return response


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def report_template(request):
    from .report_template_import import export_electricity_report_template_xlsx

    raw = _qp(request, "date")
    return export_electricity_report_template_xlsx(_as_date(raw) if raw else None)


@api_view(["POST"])
@permission_classes([CanAccessElectricity])
@parser_classes([MultiPartParser, FormParser])
def report_import(request):
    from .report_template_import import import_electricity_report_upload

    upload = request.FILES.get("file")
    if upload is None:
        raise detail_error("file is required.")
    publish = request.data.get("publish")
    publish_flag = True
    if publish is not None:
        publish_flag = str(publish).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
            "published",
        )
    result = import_electricity_report_upload(upload, publish=publish_flag)
    if not result.get("ok"):
        raise detail_error(result.get("error") or "Import failed.")
    return Response(result)


@api_view(["POST"])
@permission_classes([CanAccessElectricity])
def report_upsert(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def map_layer_geojson(request, layer_id: str):
    filters = {
        "governorate": _qp(request, "governorate"),
        "district": _qp(request, "district"),
        "subdistrict": _qp(request, "subdistrict"),
    }
    try:
        return Response(fetch_electricity_layer_geojson(layer_id, filters))
    except KeyError as exc:
        raise not_found("Layer not found.") from exc


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def power_plant_list(request):
    return Response(
        [_model_pick(p, _PLANT_FIELDS) for p in PowerPlant.objects.order_by("name_en")]
    )


# ── Entity report facts ──────────────────────────────────────────────────────
# One shape, six entity types. Each reads accepted Info for that entity and
# returns the same envelope, so they differ only in resolver and 404 message.


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def power_plant_report_facts(request, plant_id: int):
    from .report_forms_read import power_plant_with_report_facts

    return _facts_or_404(power_plant_with_report_facts(plant_id), "Power plant not found.")


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def substation_report_facts(request, substation_id: int):
    from .report_forms_read import substation_with_report_facts

    return _facts_or_404(
        substation_with_report_facts(substation_id), "Substation not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def transmission_line_report_facts(request, line_id: int):
    from .report_forms_read import transmission_line_with_report_facts

    return _facts_or_404(
        transmission_line_with_report_facts(line_id), "Transmission line not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def gis_substation_66_report_facts(request, feature_id: int):
    from .report_forms_read import power_gis_substation_66_with_report_facts

    return _facts_or_404(
        power_gis_substation_66_with_report_facts(feature_id), "GIS substation not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def gis_substation_230_report_facts(request, feature_id: int):
    from .report_forms_read import power_gis_substation_230_with_report_facts

    return _facts_or_404(
        power_gis_substation_230_with_report_facts(feature_id),
        "GIS substation not found.",
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def gis_substation_400_report_facts(request, feature_id: int):
    from .report_forms_read import power_gis_substation_400_with_report_facts

    return _facts_or_404(
        power_gis_substation_400_with_report_facts(feature_id),
        "GIS substation not found.",
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def gis_renewable_report_facts(request, feature_id: int):
    from .report_forms_read import power_gis_renewable_with_report_facts

    return _facts_or_404(
        power_gis_renewable_with_report_facts(feature_id), "Renewable site not found."
    )


# ── Daily operations / targets ───────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([CanAccessElectricity])
def daily_operations_upsert(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["POST"])
@permission_classes([CanAccessElectricity])
def daily_operations_publish(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def target_catalog(request):
    from .target_catalog import TARGET_METRICS

    return Response(
        [
            {
                "key": spec.key,
                "label_en": spec.label_en,
                "label_ar": spec.label_ar,
                "unit": spec.unit,
                "higher_is_better": spec.higher_is_better,
            }
            for spec in TARGET_METRICS
        ]
    )


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def target_coverage(request):
    from .target_coverage import build_target_coverage

    return Response(build_target_coverage(_required_date(request)))


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def target_plant_matrix(request):
    from .target_resolver import _info_target_rows, build_target_comparison

    parsed = _required_date(request)
    plant_codes = sorted(
        {
            t.get("scope_code") or ""
            for t in _info_target_rows()
            if t["scope_type"] == OperationalTarget.ScopeType.PLANT
            and t["metric_key"] == "generation_mwh"
            and t.get("scope_code")
        }
    )
    if not plant_codes:
        plant_codes = list(
            OperationalTarget.objects.filter(
                scope_type=OperationalTarget.ScopeType.PLANT,
                metric_key="generation_mwh",
            )
            .values_list("scope_code", flat=True)
            .distinct()
        )
    if not plant_codes:
        plant_codes = PowerPlant.objects.values_list("code", flat=True)

    plant_meta = {
        p.code: {"name_en": p.name_en, "name_ar": p.name_ar, "status": p.status}
        for p in PowerPlant.objects.filter(code__in=list(plant_codes))
    }
    rows = []
    for code in plant_codes:
        row = build_target_comparison(
            "generation_mwh",
            parsed,
            scope_type=OperationalTarget.ScopeType.PLANT,
            scope_code=code,
        )
        meta = plant_meta.get(code, {})
        row["name_en"] = meta.get("name_en", code)
        row["name_ar"] = meta.get("name_ar", code)
        row["plant_status"] = meta.get("status", "")
        rows.append(row)
    return Response({"date": parsed.isoformat(), "plants": rows})


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
def target_monthly(request):
    from .target_resolver import build_monthly_rollup

    return Response(
        build_monthly_rollup(
            _required_date(request),
            scope_type=_qp(request, "scope_type") or OperationalTarget.ScopeType.NATIONAL,
            scope_code=_qp(request, "scope_code") or "",
        )
    )


# ── Admin registry CRUD ──────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessElectricity])
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
@permission_classes([CanAccessElectricity])
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


def _read_only(message: str) -> Response:
    return Response({"detail": message}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET", "POST"])
@permission_classes([CanAccessElectricity])
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
@permission_classes([CanAccessElectricity])
def admin_detail(request, slug: str, pk: str):
    from map_layers.electricity_feature_admin import get_feature as get_gis_feature

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
