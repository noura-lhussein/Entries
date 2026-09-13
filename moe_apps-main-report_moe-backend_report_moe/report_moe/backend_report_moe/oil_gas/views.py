"""Oil & gas endpoints.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`. Helpers live in `admin_support.py`.

Master catalogues, daily entry and operational targets all answer 410: they are
edited through report_moe's master-data screens and Info forms, which are now the
same backend.
"""

from __future__ import annotations

from accounts.drf_permissions import CanAccessOilGas
from config.api_errors import Gone, detail_error, not_found
from config.serialize import model_to_dict
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .admin_registry import ADMIN_RESOURCES, get_resource_spec
from .admin_support import (
    _FACILITY_FIELDS,
    _REFINERY_FIELDS,
    _TARGET_FIELDS,
    _admin_save,
    _apply_audit,
    _as_date,
    _field_to_dict,
    _get_admin_object,
    _json_body,
    _model_pick,
    _parse_optional_date,
    _qp,
    build_admin_list_payload,
)
from .map_layers import fetch_oil_gas_layer_geojson
from .models import DailyReport, Facility, Field, OperationalTarget, Refinery

_DAILY_ENTRY_MOVED = (
    "Daily petroleum entry moved to report_moe Form Builder / Info. "
    "Use report_moe UI/API."
)
_TARGETS_MOVED = "Operational target {verb} moved to report_moe Info. Use operational-target titles."
_MASTER_MOVED = "Master field {verb} moved to report_moe master-data. Use report_moe UI/API."
_PDF_FORMATS = ("pdf", "application/pdf")
_XLSX_FORMATS = (
    "xlsx",
    "excel",
    "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
_TARGET_SCOPES = ("national", "field", "refinery", "facility")


def _spec_or_404(slug: str):
    spec = get_resource_spec(slug)
    if not spec:
        raise not_found("Unknown resource.")
    return spec


def _required_date(request, *, message: str = "date query param required (YYYY-MM-DD)."):
    """The two wordings below are the ones the old API used, verbatim.

    The report routes and the target routes phrase the same error differently.
    It reads like an oversight, but the text is part of the response the portal
    already shows, so it is preserved rather than tidied.
    """
    raw = _qp(request, "date")
    if not raw:
        raise detail_error(message)
    return _as_date(raw)


_REPORT_DATE_REQUIRED = "Query parameter date is required (YYYY-MM-DD)."


def _facts_or_404(payload, missing: str):
    if payload is None:
        raise not_found(missing)
    return Response(payload)


def _read_only(message: str) -> Response:
    return Response({"detail": message}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def dashboard(request):
    """Portal dashboard from accepted Info only (not DailyReport)."""
    from datetime import date

    from .info_dashboard import (
        build_info_dashboard_payload,
        build_info_monthly_dashboard_payload,
        list_info_available_months,
    )

    period = (_qp(request, "period") or "day").strip().lower()
    if period not in ("day", "month"):
        raise detail_error("Invalid period. Use day or month.")

    if period == "month":
        month_raw = (_qp(request, "month") or "").strip()
        if month_raw:
            try:
                year_text, month_text = month_raw.split("-", 1)
                year, month_num = int(year_text), int(month_text)
                if month_num < 1 or month_num > 12:
                    raise ValueError
            except ValueError as exc:
                raise detail_error("Invalid month format. Use YYYY-MM.") from exc
        else:
            months = list_info_available_months()
            if not months:
                today = date.today()
                year, month_num = today.year, today.month
            else:
                year, month_num = (int(p) for p in months[0].split("-"))
        return Response(build_info_monthly_dashboard_payload(year, month_num))

    payload = build_info_dashboard_payload(_parse_optional_date(_qp(request, "date")))
    payload["period"] = "day"
    return Response(payload)


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def trend(request, metric_key: str):
    from .info_dashboard import build_info_metric_trend

    return Response(
        build_info_metric_trend(
            metric_key,
            days=int(_qp(request, "days") or 30),
            end_date=_parse_optional_date(_qp(request, "date")),
        )
    )


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def report_dates(request):
    from .services import list_available_dates
    from .snapshot_builder import list_snapshot_dates

    merged = sorted({*list_available_dates(), *list_snapshot_dates()}, reverse=True)
    return Response({"dates": merged[:90]})


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def report_list(request):
    reports = DailyReport.objects.order_by("-report_date")[:60]
    return Response(
        [
            {
                "id": r.id,
                "report_date": r.report_date.isoformat(),
                "status": r.status,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in reports
        ]
    )


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def report_detail(request):
    from .services import build_report_detail_payload

    payload = build_report_detail_payload(
        _required_date(request, message=_REPORT_DATE_REQUIRED)
    )
    if not payload:
        raise not_found("Report not found.")
    return Response(payload)


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def report_export(request):
    from .report_export import export_oil_gas_report_xlsx
    from .report_pdf import export_oil_gas_report_pdf

    parsed = _required_date(request, message=_REPORT_DATE_REQUIRED)
    fmt = (_qp(request, "format") or "xlsx").strip().lower()
    if fmt in _PDF_FORMATS:
        response = export_oil_gas_report_pdf(parsed)
    elif fmt in _XLSX_FORMATS:
        response = export_oil_gas_report_xlsx(parsed)
    else:
        raise detail_error("Query parameter format must be xlsx or pdf.")
    if response is None:
        raise not_found("Report not found.")
    return response


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def report_template(request):
    from .report_template_import import export_oil_gas_executive_template_xlsx

    raw = _qp(request, "date")
    return export_oil_gas_executive_template_xlsx(_as_date(raw) if raw else None)


@api_view(["POST"])
@permission_classes([CanAccessOilGas])
@parser_classes([MultiPartParser, FormParser])
def report_import(request):
    from .report_template_import import import_oil_gas_executive_upload

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
    result = import_oil_gas_executive_upload(upload, publish=publish_flag)
    if not result.get("ok"):
        raise detail_error(result.get("error") or "Import failed.")
    return Response(result)


@api_view(["POST"])
@permission_classes([CanAccessOilGas])
def report_upsert(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def map_layer_geojson(request, layer_id: str):
    filters = {
        "governorate": _qp(request, "governorate"),
        "district": _qp(request, "district"),
        "subdistrict": _qp(request, "subdistrict"),
    }
    try:
        return Response(fetch_oil_gas_layer_geojson(layer_id, filters))
    except KeyError as exc:
        raise not_found("Layer not found.") from exc


# ── Master catalogues (read-only here; edited in report_moe master-data) ──────


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def facility_list(request):
    qs = Facility.objects.order_by("name_en")
    sector = (_qp(request, "sector") or "").strip()
    facility_type = (_qp(request, "facility_type") or "").strip()
    if sector:
        qs = qs.filter(sector=sector)
    if facility_type:
        qs = qs.filter(facility_type=facility_type)
    return Response([_model_pick(f, _FACILITY_FIELDS) for f in qs])


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def refinery_list(request):
    return Response(
        [
            _model_pick(r, _REFINERY_FIELDS)
            for r in Refinery.objects.order_by("refinery_name")
        ]
    )


@api_view(["GET", "POST"])
@permission_classes([CanAccessOilGas])
def field_list(request):
    if request.method == "POST":
        raise Gone(_MASTER_MOVED.format(verb="create"))
    qs = Field.objects.prefetch_related("wells").order_by("name_en")
    return Response([_field_to_dict(f) for f in qs])


@api_view(["GET", "PATCH", "PUT"])
@permission_classes([CanAccessOilGas])
def field_detail(request, code: str):
    if request.method in ("PATCH", "PUT"):
        raise Gone(_MASTER_MOVED.format(verb="update"))
    try:
        field = Field.objects.prefetch_related("wells").get(code=code)
    except Field.DoesNotExist as exc:
        raise not_found("Not found.") from exc
    return Response(_field_to_dict(field))


# ── Entity report facts ──────────────────────────────────────────────────────
# One shape, six entity types: each reads accepted Info for that entity.


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def oil_field_report_facts(request, field_id: int):
    from .report_forms_read import oil_field_with_report_facts

    return _facts_or_404(oil_field_with_report_facts(field_id), "Oil field not found.")


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def oil_refinery_report_facts(request, refinery_id: int):
    from .report_forms_read import oil_refinery_with_report_facts

    return _facts_or_404(
        oil_refinery_with_report_facts(refinery_id), "Refinery not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def fuel_station_report_facts(request, facility_id: int):
    from .report_forms_read import fuel_station_with_report_facts

    return _facts_or_404(
        fuel_station_with_report_facts(facility_id), "Fuel station not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def oil_well_report_facts(request, well_id: int):
    from .report_forms_read import oil_well_with_report_facts

    return _facts_or_404(oil_well_with_report_facts(well_id), "Oil well not found.")


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def storage_depot_report_facts(request, facility_id: int):
    from .report_forms_read import storage_depot_with_report_facts

    return _facts_or_404(
        storage_depot_with_report_facts(facility_id), "Storage depot not found."
    )


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def pipeline_report_facts(request, pipeline_id: int):
    from .report_forms_read import pipeline_with_report_facts

    return _facts_or_404(pipeline_with_report_facts(pipeline_id), "Pipeline not found.")


# ── Daily operations / targets ───────────────────────────────────────────────


@api_view(["POST"])
@permission_classes([CanAccessOilGas])
def daily_operations_upsert(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["POST"])
@permission_classes([CanAccessOilGas])
def daily_operations_publish(request):
    raise Gone(_DAILY_ENTRY_MOVED)


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
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


@api_view(["GET", "POST"])
@permission_classes([CanAccessOilGas])
def target_list(request):
    if request.method == "POST":
        raise Gone(_TARGETS_MOVED.format(verb="create"))

    from projects.targets_info import (
        filter_info_targets,
        list_info_targets,
        serialize_info_target,
    )

    from oil_gas.info_scope import oil_gas_category_id_override, oil_gas_category_name

    metric_key = _qp(request, "metric_key")
    scope_type = _qp(request, "scope_type")
    scope_code = _qp(request, "scope_code")
    period_start = _qp(request, "period_start")

    info_rows = list_info_targets(
        oil_gas_category_name(),
        settings_id=oil_gas_category_id_override(),
        env_id_name="OIL_GAS_TITLE_CATEGORY_ID",
    )
    if info_rows:
        filtered = filter_info_targets(
            info_rows,
            metric_key=metric_key,
            scope_type=scope_type,
            scope_code=scope_code,
            period_start=period_start,
        )
        return Response([serialize_info_target(t) for t in filtered])

    qs = OperationalTarget.objects.all().order_by("-period_start", "metric_key")
    if metric_key:
        qs = qs.filter(metric_key=metric_key)
    if scope_type:
        qs = qs.filter(scope_type=scope_type)
    if scope_code:
        qs = qs.filter(scope_code=scope_code)
    if period_start:
        qs = qs.filter(period_start=period_start)
    return Response([_model_pick(t, _TARGET_FIELDS) for t in qs])


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def target_compare(request):
    from .target_resolver import build_target_comparison, list_targets_for_scope

    on_date = _required_date(request)
    scope_type = _qp(request, "scope_type") or "national"
    if scope_type not in _TARGET_SCOPES:
        raise detail_error("Invalid scope_type.")
    scope_code = _qp(request, "scope_code") or ""
    metric_key = (_qp(request, "metric_key") or "").strip()
    if metric_key:
        rows = [
            build_target_comparison(
                metric_key, on_date, scope_type=scope_type, scope_code=scope_code
            )
        ]
    else:
        rows = list_targets_for_scope(
            on_date, scope_type=scope_type, scope_code=scope_code
        )
    return Response({"date": on_date.isoformat(), "comparisons": rows})


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def target_coverage(request):
    from .target_coverage import build_target_coverage

    return Response(build_target_coverage(_required_date(request)))


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def target_field_matrix(request):
    from .target_resolver import _info_target_rows, build_target_comparison

    parsed = _required_date(request)
    field_codes = sorted(
        {
            t.get("scope_code") or ""
            for t in _info_target_rows()
            if t["scope_type"] == OperationalTarget.ScopeType.FIELD
            and t["metric_key"] == "crude_oil_bbl"
            and t.get("scope_code")
        }
    )
    if not field_codes:
        field_codes = list(
            OperationalTarget.objects.filter(
                scope_type=OperationalTarget.ScopeType.FIELD,
                metric_key="crude_oil_bbl",
            )
            .order_by("scope_code")
            .values_list("scope_code", flat=True)
            .distinct()
        )
    if not field_codes:
        field_codes = Field.objects.order_by("name_en").values_list("code", flat=True)

    field_meta = {
        f.code: {"name_en": f.name_en, "name_ar": f.name_ar, "status": f.status}
        for f in Field.objects.filter(code__in=list(field_codes))
    }
    rows = []
    for code in field_codes:
        row = build_target_comparison(
            "crude_oil_bbl",
            parsed,
            scope_type=OperationalTarget.ScopeType.FIELD,
            scope_code=code,
        )
        meta = field_meta.get(code, {})
        row["name_en"] = meta.get("name_en", code)
        row["name_ar"] = meta.get("name_ar", code)
        row["field_status"] = meta.get("status", "")
        rows.append(row)
    return Response({"date": parsed.isoformat(), "fields": rows})


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
def target_monthly(request):
    from .target_resolver import build_monthly_rollup

    return Response(
        build_monthly_rollup(
            _required_date(request),
            scope_type=_qp(request, "scope_type") or OperationalTarget.ScopeType.NATIONAL,
            scope_code=_qp(request, "scope_code") or "",
        )
    )


@api_view(["GET", "PATCH", "PUT", "DELETE"])
@permission_classes([CanAccessOilGas])
def target_detail(request, pk: int):
    if request.method in ("PATCH", "PUT"):
        raise Gone(_TARGETS_MOVED.format(verb="update"))
    if request.method == "DELETE":
        raise Gone(_TARGETS_MOVED.format(verb="delete"))
    try:
        instance = OperationalTarget.objects.get(pk=pk)
    except OperationalTarget.DoesNotExist as exc:
        raise not_found("Not found.") from exc
    return Response(_model_pick(instance, _TARGET_FIELDS))


# ── Admin registry CRUD ──────────────────────────────────────────────────────


@api_view(["GET"])
@permission_classes([CanAccessOilGas])
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
@permission_classes([CanAccessOilGas])
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
@permission_classes([CanAccessOilGas])
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
@permission_classes([CanAccessOilGas])
def admin_detail(request, slug: str, pk: str):
    spec = _spec_or_404(slug)

    if request.method == "GET":
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
