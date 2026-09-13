"""Development-project endpoints for the portal.

Converted from Django Ninja; URLs, payloads and status codes are unchanged and
guarded by `tests/parity`.

Reads come from the reporting side (`display_services`), which before the merge
meant a second database connection and is now a plain ORM query. Writes answer
410: projects are edited in report_moe's budget module and institutions in its
master-data screens — both part of this same backend now.
"""

from __future__ import annotations

from typing import Any

from accounts.drf_permissions import CanManageControlPanel, CanManageProjects
from config.api_errors import Gone, detail_error, not_found
from config.serialize import model_to_dict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .display_models import ReportBudgetProject
from .display_services import (
    build_report_projects_dashboard,
    build_report_projects_summary,
    get_report_project,
    list_report_projects,
)
from .models import ProjectOrganization, Sector
from .services import build_projects_meta, get_organization, list_organizations


def serialize_organization(organization: ProjectOrganization) -> dict[str, Any]:
    return {
        "id": organization.id,
        "slug": organization.slug,
        "acronym": organization.acronym,
        "name_en": organization.name_en,
        "governorate_id": organization.governorate_id,
        "governorate_name_en": organization.governorate_name_en,
        "governorate_name_ar": organization.governorate_name_ar,
    }


def _strip_internal(row: dict[str, Any]) -> dict[str, Any]:
    """Drop `_`-prefixed keys the query helpers use for their own bookkeeping."""
    return {key: value for key, value in row.items() if not key.startswith("_")}


def _sector(request, *, required: bool = False) -> str | None:
    value = (request.query_params.get("sector") or "").strip()
    if required and (not value or value not in Sector.values):
        raise detail_error("Sector is required.")
    if value and value not in Sector.values:
        raise detail_error("Invalid sector.")
    return value or None


@api_view(["GET", "POST"])
@permission_classes([CanManageProjects])
def project_list(request):
    if request.method == "POST":
        raise Gone(
            "Project create moved to report_moe budget module. Use report_moe UI/API."
        )
    rows = list_report_projects(
        sector=_sector(request),
        include_inactive=request.query_params.get("include_inactive") == "1",
    )
    return Response([_strip_internal(row) for row in rows])


@api_view(["GET"])
@permission_classes([CanManageControlPanel])
def projects_meta(request):
    payload = build_projects_meta()
    return Response(
        {
            "sectors": payload["sectors"],
            "statuses": payload["statuses"],
            "governorates": [model_to_dict(row) for row in payload["governorates"]],
            "organizations": [
                serialize_organization(row) for row in payload["organizations"]
            ],
        }
    )


@api_view(["GET", "POST"])
@permission_classes([CanManageControlPanel])
def organization_list(request):
    if request.method == "POST":
        raise Gone(
            "Organization create moved to report_moe master-data. Use report_moe UI/API."
        )
    return Response([serialize_organization(row) for row in list_organizations()])


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([CanManageControlPanel])
def organization_detail(request, pk: int):
    if request.method == "PATCH":
        raise Gone(
            "Organization update moved to report_moe master-data. Use report_moe UI/API."
        )
    if request.method == "DELETE":
        raise Gone(
            "Organization delete moved to report_moe master-data. Use report_moe UI/API."
        )
    try:
        return Response(serialize_organization(get_organization(pk)))
    except ProjectOrganization.DoesNotExist:
        raise not_found()


@api_view(["GET"])
@permission_classes([CanManageProjects])
def projects_summary(request):
    return Response(build_report_projects_summary(sector=_sector(request)))


@api_view(["GET"])
@permission_classes([CanManageProjects])
def projects_dashboard(request):
    return Response(
        build_report_projects_dashboard(sector=_sector(request, required=True))
    )


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([CanManageProjects])
def project_detail(request, pk: int):
    if request.method in ("PATCH", "DELETE"):
        verb = "update" if request.method == "PATCH" else "delete"
        raise Gone(
            f"Project {verb} moved to report_moe budget module. Use report_moe UI/API."
        )
    try:
        return Response(_strip_internal(get_report_project(pk)))
    except ReportBudgetProject.DoesNotExist:
        raise not_found()


@api_view(["GET", "PUT"])
@permission_classes([CanManageProjects])
def project_monitoring(request, pk: int):
    raise Gone(
        "Project monitoring moved to report_moe budget module. Use report_moe UI/API."
    )
