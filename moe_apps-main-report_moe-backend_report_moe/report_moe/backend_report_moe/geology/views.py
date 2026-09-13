"""Geology & mineral-resources endpoints.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`. The admin helpers live in `admin_support.py`.

Daily-report writes answer 410: ore production is entered through report_moe's
Form Builder and read back from Info, which is now the same backend.
"""

from __future__ import annotations

from datetime import date

from accounts.drf_permissions import CanAccessMineral
from config.api_errors import Gone, detail_error, not_found
from config.serialize import model_to_dict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .admin_registry import ADMIN_RESOURCES, get_resource_spec, ordered_registry_groups
from .admin_support import (
    _admin_save,
    _apply_audit,
    _get_admin_object,
    _json_body,
    _layer_feature_counts,
    _qp,
)
from .models import DailyReport

# Formats accepted by the report export, mapped to their builder.
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


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def dashboard(request):
    from geology.info_dashboard import build_geology_info_dashboard

    plan_year = request.query_params.get("plan_year")
    return Response(
        build_geology_info_dashboard(
            layers=_layer_feature_counts(),
            plan_year=int(plan_year) if plan_year else None,
        )
    )


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def reports_export(request):
    plan_year = request.query_params.get("plan_year")
    year = int(plan_year) if plan_year else date.today().year
    fmt = (request.query_params.get("format") or "xlsx").strip().lower()

    if fmt in _PDF_FORMATS:
        from geology.report_pdf import export_geology_report_pdf

        response = export_geology_report_pdf(year)
    elif fmt in _XLSX_FORMATS:
        from geology.report_export import export_ore_production_xlsx

        response = export_ore_production_xlsx(year)
    else:
        raise detail_error("Unsupported format. Use pdf or xlsx.")

    if response is None:
        raise not_found("No ore production data for this year.")
    return response


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def admin_registry(request):
    return Response(
        {
            "resources": [spec.to_dict() for spec in ADMIN_RESOURCES.values()],
            "groups": ordered_registry_groups(),
        }
    )


@api_view(["GET", "POST"])
@permission_classes([CanAccessMineral])
def daily_report(request):
    if request.method == "POST":
        raise Gone(
            "Geology daily entry moved to report_moe Form Builder / Info. "
            "Use report_moe UI/API."
        )

    raw = _qp(request, "report_date")
    if not raw:
        raise detail_error("report_date query param required (YYYY-MM-DD).")
    try:
        row = DailyReport.objects.filter(report_date=raw[:10]).first()
    except Exception as exc:  # noqa: BLE001 — an unparseable date is a client error
        raise detail_error("Invalid report_date.") from exc
    if not row:
        return Response(
            {
                "report_date": raw[:10],
                "status": DailyReport.Status.DRAFT,
                "notes_ar": "",
                "notes_en": "",
                "exists": False,
            }
        )
    data = model_to_dict(row)
    data["exists"] = True
    return Response(data)


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def daily_report_template(request):
    raise Gone(
        "Ore production template moved to report_moe Form Builder. Use report_moe UI/API."
    )


@api_view(["GET"])
@permission_classes([CanAccessMineral])
def daily_report_export(request):
    raise Gone("Use /geology/reports/export/ for ore production export (Info-sourced).")


@api_view(["POST"])
@permission_classes([CanAccessMineral])
def daily_report_import(request):
    raise Gone(
        "Ore production import moved to report_moe Form Builder. Use report_moe UI/API."
    )


@api_view(["GET"])
@permission_classes([CanAccessMineral])
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
@permission_classes([CanAccessMineral])
def admin_list(request, slug: str):
    from .admin_support import build_admin_list_payload

    spec = _spec_or_404(slug)
    if request.method == "POST":
        return _admin_create(request, spec)
    return Response(build_admin_list_payload(request, spec))


def _admin_create(request, spec):
    from rest_framework import status

    if spec.read_only:
        return Response(
            {"detail": "This resource is read-only."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    if spec.gis_layer_id:
        return Response(
            {"detail": "GIS feature writes moved to report_moe."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    if spec.model is None:
        raise not_found("Unknown resource.")
    instance = _admin_save(spec.model(), _json_body(request), partial=False)
    _apply_audit(instance, request.user)
    return Response(model_to_dict(instance), status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([CanAccessMineral])
def admin_detail(request, slug: str, pk: str):
    from map_layers.water_feature_admin import get_feature as get_gis_feature
    from rest_framework import status

    spec = _spec_or_404(slug)

    if request.method == "GET":
        if spec.gis_layer_id:
            return Response(get_gis_feature(spec.gis_layer_id, pk))
        try:
            return Response(model_to_dict(_get_admin_object(spec, pk)))
        except Exception as exc:  # noqa: BLE001 — any lookup failure is a miss
            raise not_found() from exc

    if spec.read_only:
        return Response(
            {"detail": "This resource is read-only."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    if spec.gis_layer_id:
        return Response(
            {"detail": "GIS feature writes moved to report_moe."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
    try:
        instance = _get_admin_object(spec, pk)
    except Exception as exc:  # noqa: BLE001
        raise not_found() from exc

    if request.method == "DELETE":
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    instance = _admin_save(instance, _json_body(request), partial=True)
    _apply_audit(instance, request.user)
    return Response(model_to_dict(instance))
