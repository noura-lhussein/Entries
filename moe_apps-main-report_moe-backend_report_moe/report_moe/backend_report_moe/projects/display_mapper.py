"""
Map report_moe.project_budget rows to the portal DevelopmentProject DTO shape.

Source tables live in schema `report_moe`, reached by plain ORM.
report_moe has no moeds Sector taxonomy — portal sector is passed through for UI only.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .display_models import ReportBudgetProject
from .models import Sector

# Portal DTO statuses expected by the existing dashboard UI.
PORTAL_STATUS_ACTIVE = 'active'
PORTAL_STATUS_PLANNED = 'planned'
PORTAL_STATUS_COMPLETED = 'completed'
PORTAL_STATUS_SUSPENDED = 'suspended'

_STATUS_MAP: dict[str, tuple[str, str, str]] = {
    ReportBudgetProject.Status.DRAFT: (PORTAL_STATUS_PLANNED, 'Planned', 'مخطط'),
    ReportBudgetProject.Status.ACTIVE: (PORTAL_STATUS_ACTIVE, 'Active', 'نشط'),
    ReportBudgetProject.Status.ON_HOLD: (PORTAL_STATUS_SUSPENDED, 'Suspended', 'موقوف'),
    ReportBudgetProject.Status.COMPLETED: (PORTAL_STATUS_COMPLETED, 'Completed', 'مكتمل'),
    ReportBudgetProject.Status.CANCELLED: (PORTAL_STATUS_SUSPENDED, 'Suspended', 'موقوف'),
}


def _float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def map_budget_status(raw: str) -> tuple[str, str, str]:
    return _STATUS_MAP.get(raw, (PORTAL_STATUS_PLANNED, raw or 'Unknown', raw or 'غير معروف'))


def project_budget_usd(project: ReportBudgetProject) -> float:
    approved = _float(project.approved_budget)
    if approved > 0:
        return approved
    return _float(project.proposed_budget)


def project_spent_usd(project: ReportBudgetProject) -> float:
    return _float(project.budget_expenditure)


def project_utilization_pct(project: ReportBudgetProject) -> float:
    budget = project_budget_usd(project)
    spent = project_spent_usd(project)
    if budget > 0:
        return round(spent / budget * 100, 1)
    return round(_float(project.percentage_completion), 1)


def map_report_project_to_portal(
    project: ReportBudgetProject,
    *,
    sector: str | None = None,
) -> dict[str, Any]:
    """One explicit mapper: report_moe row → portal list/dashboard DTO."""
    budget = project_budget_usd(project)
    spent = project_spent_usd(project)
    remaining = max(budget - spent, 0.0)
    utilization = project_utilization_pct(project)
    status, status_en, status_ar = map_budget_status(project.status)

    gov = project.governorate
    foundation = project.foundation
    sector_value = sector or Sector.MULTI
    sector_display = dict(Sector.choices).get(sector_value, sector_value)

    title_en = (project.name_en or '').strip() or project.name_ar
    title_ar = (project.name_ar or '').strip() or title_en
    if foundation:
        org_name = (foundation.name_en or '').strip() or foundation.name_ar
        org_name_ar = (foundation.name_ar or '').strip()
    else:
        org_name = ''
        org_name_ar = ''

    return {
        'id': project.id,
        'code': project.code or '',
        'title_en': title_en,
        'title_ar': title_ar,
        'governorate_id': project.governorate_id,
        'governorate_pcode': (gov.code if gov else '') or '',
        'governorate_name_en': (gov.name_en if gov else '') or (gov.name_ar if gov else '') or '',
        'governorate_name_ar': (gov.name_ar if gov else '') or '',
        'organization_id': project.foundation_id,
        'organization_slug': f'foundation-{project.foundation_id}',
        'organization_acronym': '',
        'organization_name_en': org_name or org_name_ar,
        'sector': sector_value,
        'sector_display': sector_display,
        'status': status,
        'status_display': status_ar if status_ar else status_en,
        'budget_usd': budget,
        'amount_spent_usd': spent,
        'remaining_usd': remaining,
        'utilization_pct': utilization,
        'reporting_through': project.end_date.isoformat() if project.end_date else None,
        'start_year': project.start_date.year if project.start_date else None,
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'location': (project.description or '').strip()[:500],
        'logo': None,
        'logo_url': None,
        'is_active': not project.deleted and project.status != ReportBudgetProject.Status.CANCELLED,
        'created_at': project.created_at.isoformat() if project.created_at else None,
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
        # Extra fields used when building dashboard charts from DTOs.
        '_gov_key': (gov.code if gov else '') or str(project.governorate_id),
        '_org_key': f'foundation-{project.foundation_id}',
        '_org_label_en': org_name or org_name_ar or f'Foundation {project.foundation_id}',
        '_org_label_ar': org_name_ar or org_name or f'مؤسسة {project.foundation_id}',
        '_completion_pct': round(_float(project.percentage_completion), 1),
    }
