"""Read services for portal projects — sourced from report_moe mirrors."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import QuerySet

from .display_mapper import (
    PORTAL_STATUS_ACTIVE,
    PORTAL_STATUS_COMPLETED,
    PORTAL_STATUS_PLANNED,
    PORTAL_STATUS_SUSPENDED,
    map_report_project_to_portal,
)
from .display_models import ReportBudgetProject
from .models import Sector


def _active_projects_qs() -> QuerySet[ReportBudgetProject]:
    return (
        ReportBudgetProject.objects
        .filter(deleted=False)
        .select_related('foundation', 'governorate')
        .order_by('code', 'id')
    )


def list_report_projects(
    *,
    sector: str | None = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    # report_moe projects have no moeds sector field; sector is UI context only.
    rows = [
        map_report_project_to_portal(row, sector=sector)
        for row in _active_projects_qs()
    ]
    if not include_inactive:
        rows = [row for row in rows if row['is_active']]
    return rows


def get_report_project(project_id: int, *, sector: str | None = None) -> dict[str, Any]:
    project = (
        ReportBudgetProject.objects
        .filter(deleted=False)
        .select_related('foundation', 'governorate')
        .get(pk=project_id)
    )
    return map_report_project_to_portal(project, sector=sector)


def build_report_projects_summary(*, sector: str | None = None) -> dict[str, Any]:
    rows = list_report_projects(sector=sector)
    sector_display = dict(Sector.choices).get(sector or '', 'All projects') if sector else 'All projects'

    total_budget = sum(float(r['budget_usd']) for r in rows)
    total_spent = sum(float(r['amount_spent_usd']) for r in rows)
    remaining = max(total_budget - total_spent, 0.0)
    utilization = round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0.0

    reporting_through = None
    for row in rows:
        iso = row.get('reporting_through')
        if iso and (reporting_through is None or iso > reporting_through):
            reporting_through = iso

    by_org: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row['_org_key']
        bucket = by_org.setdefault(
            key,
            {
                'slug': key,
                'acronym': row.get('organization_acronym') or '',
                'name_en': row['_org_label_en'],
                'project_count': 0,
                'total_budget_usd': 0.0,
                'total_spent_usd': 0.0,
            },
        )
        bucket['project_count'] += 1
        bucket['total_budget_usd'] += float(row['budget_usd'])
        bucket['total_spent_usd'] += float(row['amount_spent_usd'])

    institutions = []
    for bucket in sorted(by_org.values(), key=lambda item: item['project_count'], reverse=True):
        inst_budget = bucket['total_budget_usd']
        inst_spent = bucket['total_spent_usd']
        inst_remaining = max(inst_budget - inst_spent, 0.0)
        inst_util = round(inst_spent / inst_budget * 100, 1) if inst_budget > 0 else 0.0
        institutions.append(
            {
                **bucket,
                'total_budget_usd': round(inst_budget, 2),
                'total_spent_usd': round(inst_spent, 2),
                'remaining_usd': round(inst_remaining, 2),
                'utilization_pct': inst_util,
            }
        )

    return {
        'sector': sector,
        'sector_display': sector_display,
        'reporting_through': reporting_through,
        'national': {
            'project_count': len(rows),
            'institution_count': len(institutions),
            'total_budget_usd': round(total_budget, 2),
            'total_spent_usd': round(total_spent, 2),
            'remaining_usd': round(remaining, 2),
            'utilization_pct': utilization,
        },
        'institutions': institutions,
    }


def _utilization_status(pct: float) -> str:
    if pct >= 100:
        return 'critical'
    if pct >= 85:
        return 'warning'
    return 'ok'


def _status_card(
    card_id: str,
    label_en: str,
    label_ar: str,
    value: str,
    status: str,
    detail_en: str = '',
    detail_ar: str = '',
) -> dict[str, str]:
    return {
        'id': card_id,
        'label_en': label_en,
        'label_ar': label_ar,
        'value': value,
        'status': status,
        'detail_en': detail_en,
        'detail_ar': detail_ar,
    }


def build_report_projects_dashboard(*, sector: str | None = None) -> dict[str, Any]:
    projects = list_report_projects(sector=sector)
    sector_display = dict(Sector.choices).get(sector, sector) if sector else 'All projects'

    if not projects:
        return {
            'status': 'empty',
            'sector': sector,
            'sector_display': sector_display,
            'reporting_through': None,
            'kpis': [],
            'status_cards': [],
            'charts': {},
            'projects': [],
        }

    total_budget = sum(float(p['budget_usd']) for p in projects)
    total_spent = sum(float(p['amount_spent_usd']) for p in projects)
    remaining = max(total_budget - total_spent, 0.0)
    utilization = round(total_spent / total_budget * 100, 1) if total_budget > 0 else 0.0

    reporting_through = None
    for project in projects:
        iso = project.get('reporting_through')
        if iso and (reporting_through is None or iso > reporting_through):
            reporting_through = iso

    status_counts: dict[str, int] = defaultdict(int)
    for project in projects:
        status_counts[project['status']] += 1

    institution_keys = {p['_org_key'] for p in projects}

    kpis = [
        {
            'id': 'project_count',
            'label_en': 'Projects',
            'label_ar': 'المشاريع',
            'value': len(projects),
            'unit': '',
            'target_value': None,
            'achievement_pct': None,
            'delta_pct': None,
            'status': 'neutral',
        },
        {
            'id': 'total_budget',
            'label_en': 'Total budget',
            'label_ar': 'إجمالي الميزانية',
            'value': round(total_budget, 2),
            'unit': 'USD',
            'target_value': None,
            'achievement_pct': None,
            'delta_pct': None,
            'status': 'ok',
        },
        {
            'id': 'amount_spent',
            'label_en': 'Amount spent',
            'label_ar': 'المنفق',
            'value': round(total_spent, 2),
            'unit': 'USD',
            'target_value': round(total_budget, 2),
            'achievement_pct': utilization,
            'delta_pct': None,
            'status': _utilization_status(utilization),
        },
        {
            'id': 'remaining',
            'label_en': 'Remaining',
            'label_ar': 'المتبقي',
            'value': round(remaining, 2),
            'unit': 'USD',
            'target_value': None,
            'achievement_pct': None,
            'delta_pct': None,
            'status': 'neutral',
        },
        {
            'id': 'utilization',
            'label_en': 'Utilization',
            'label_ar': 'نسبة الاستخدام',
            'value': utilization,
            'unit': '%',
            'target_value': 100.0,
            'achievement_pct': utilization,
            'delta_pct': None,
            'status': _utilization_status(utilization),
        },
    ]

    status_cards = [
        _status_card(
            'active',
            'Active',
            'نشط',
            str(status_counts[PORTAL_STATUS_ACTIVE]),
            'ok',
            'Currently executing',
            'قيد التنفيذ',
        ),
        _status_card(
            'planned',
            'Planned',
            'مخطط',
            str(status_counts[PORTAL_STATUS_PLANNED]),
            'warning',
            'Approved, not started',
            'معتمد ولم يبدأ',
        ),
        _status_card(
            'completed',
            'Completed',
            'مكتمل',
            str(status_counts[PORTAL_STATUS_COMPLETED]),
            'ok',
            'Closed out',
            'مُغلق',
        ),
        _status_card(
            'suspended',
            'Suspended',
            'موقوف',
            str(status_counts[PORTAL_STATUS_SUSPENDED]),
            'critical',
            'On hold',
            'معلق',
        ),
        _status_card(
            'institutions',
            'Institutions',
            'المؤسسات',
            str(len(institution_keys)),
            'neutral',
            'Implementing partners',
            'جهات التنفيذ',
        ),
    ]

    gov_budget: dict[str, dict[str, str | float]] = defaultdict(
        lambda: {'name_en': '', 'name_ar': '', 'budget': 0.0, 'spent': 0.0},
    )
    for project in projects:
        key = project['_gov_key']
        row = gov_budget[key]
        row['name_en'] = project['governorate_name_en']
        row['name_ar'] = project['governorate_name_ar']
        row['budget'] += float(project['budget_usd'])
        row['spent'] += float(project['amount_spent_usd'])

    gov_rows = sorted(gov_budget.values(), key=lambda item: item['budget'], reverse=True)

    inst_budget: dict[str, dict[str, str | float]] = defaultdict(
        lambda: {'name_en': '', 'name_ar': '', 'budget': 0.0, 'spent': 0.0},
    )
    for project in projects:
        key = project['_org_key']
        row = inst_budget[key]
        row['name_en'] = project['_org_label_en']
        row['name_ar'] = project['_org_label_ar']
        row['budget'] += float(project['budget_usd'])
        row['spent'] += float(project['amount_spent_usd'])

    inst_rows = sorted(inst_budget.values(), key=lambda item: item['budget'], reverse=True)
    sorted_projects = sorted(projects, key=lambda p: p['utilization_pct'], reverse=True)

    charts = {
        'budget_by_governorate': {
            'labels_en': [str(row['name_en']) for row in gov_rows],
            'labels_ar': [str(row['name_ar'] or row['name_en']) for row in gov_rows],
            'values_usd': [round(float(row['budget']), 2) for row in gov_rows],
        },
        'spent_by_governorate': {
            'labels_en': [str(row['name_en']) for row in gov_rows],
            'labels_ar': [str(row['name_ar'] or row['name_en']) for row in gov_rows],
            'values_usd': [round(float(row['spent']), 2) for row in gov_rows],
        },
        'institution_spend': {
            'labels_en': [str(row['name_en']) for row in inst_rows],
            'labels_ar': [str(row['name_ar'] or row['name_en']) for row in inst_rows],
            'budget_usd': [round(float(row['budget']), 2) for row in inst_rows],
            'spent_usd': [round(float(row['spent']), 2) for row in inst_rows],
        },
        'status_mix': {
            'labels_en': ['Active', 'Planned', 'Completed', 'Suspended'],
            'labels_ar': ['نشط', 'مخطط', 'مكتمل', 'موقوف'],
            'values': [
                status_counts[PORTAL_STATUS_ACTIVE],
                status_counts[PORTAL_STATUS_PLANNED],
                status_counts[PORTAL_STATUS_COMPLETED],
                status_counts[PORTAL_STATUS_SUSPENDED],
            ],
        },
        'project_utilization': {
            'labels_en': [p['title_en'] for p in sorted_projects[:8]],
            'labels_ar': [p['title_ar'] or p['title_en'] for p in sorted_projects[:8]],
            'values_pct': [p['utilization_pct'] for p in sorted_projects[:8]],
        },
    }

    public_projects = [_strip_internal_keys(p) for p in projects]

    return {
        'status': 'ready',
        'sector': sector,
        'sector_display': sector_display,
        'reporting_through': reporting_through,
        'kpis': kpis,
        'status_cards': status_cards,
        'charts': charts,
        'projects': public_projects,
    }


def _strip_internal_keys(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith('_')}
