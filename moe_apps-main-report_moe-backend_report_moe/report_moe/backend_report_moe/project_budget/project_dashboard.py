"""Aggregated statistics for the budget projects dashboard."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db.models import Avg, Count, F, Q, Sum
from django.utils import timezone

from .models import Milestone, Project, ProjectCategory

CATEGORY_SECTION_PREFIXES = ("31", "32", "33")


def _decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_percent(numerator: Decimal, denominator: Decimal) -> float | None:
    if denominator <= 0:
        return None
    return round(float(numerator / denominator * 100), 1)


def build_category_project_counts(projects_qs):
    """Distinct project counts and expenditure totals per category branch."""
    project_ids = list(projects_qs.values_list("pk", flat=True))
    if not project_ids:
        return [], 0, "0", []

    project_expenditure = {
        pk: _decimal(exp)
        for pk, exp in projects_qs.values_list("pk", "budget_expenditure")
    }

    links = Milestone.objects.filter(
        project_id__in=project_ids,
        deleted=False,
        category_id__isnull=False,
    ).values_list("project_id", "category_id").distinct()

    uncategorized_project_ids = set(
        Milestone.objects.filter(
            project_id__in=project_ids,
            deleted=False,
            category_id__isnull=True,
        )
        .values_list("project_id", flat=True)
        .distinct()
    )
    uncategorized_projects = len(uncategorized_project_ids)
    uncategorized_expenditure = sum(
        project_expenditure.get(project_id, Decimal("0"))
        for project_id in uncategorized_project_ids
    )

    categories = list(
        ProjectCategory.objects.filter(deleted=False).only(
            "id",
            "parent_id",
            "code",
            "name_ar",
            "name_en",
        )
    )
    by_id = {category.pk: category for category in categories}
    project_sets: dict[int, set[int]] = defaultdict(set)

    for project_id, category_id in links:
        category = by_id.get(category_id)
        if category is None:
            continue
        current = category
        seen: set[int] = set()
        while current is not None and current.pk not in seen:
            seen.add(current.pk)
            project_sets[current.pk].add(project_id)
            parent_id = current.parent_id
            current = by_id.get(parent_id) if parent_id else None

    def _category_expenditure(category_id: int) -> Decimal:
        return sum(
            project_expenditure.get(project_id, Decimal("0"))
            for project_id in project_sets.get(category_id, set())
        )

    by_category = [
        {
            "id": category.pk,
            "parent_id": category.parent_id,
            "code": category.code or "",
            "name": category.name_ar or category.name_en or "—",
            "project_count": len(project_sets.get(category.pk, set())),
            "total_expenditure": str(_category_expenditure(category.pk)),
        }
        for category in categories
    ]
    by_category.sort(key=lambda row: (row["code"], row["name"]))

    by_category_section = []
    for prefix in CATEGORY_SECTION_PREFIXES:
        section_project_ids: set[int] = set()
        for category in categories:
            if (category.code or "").startswith(prefix):
                section_project_ids.update(
                    project_sets.get(category.pk, set()))
        by_category_section.append(
            {
                "prefix": prefix,
                "project_count": len(section_project_ids),
                "total_expenditure": str(
                    sum(
                        project_expenditure.get(project_id, Decimal("0"))
                        for project_id in section_project_ids
                    )
                ),
            }
        )

    return (
        by_category,
        uncategorized_projects,
        str(uncategorized_expenditure),
        by_category_section,
    )


def build_project_dashboard(projects_qs):
    """Build dashboard payload from an already-scoped Project queryset."""
    today = timezone.localdate()
    active_statuses = {Project.Status.ACTIVE}
    terminal_statuses = {Project.Status.COMPLETED, Project.Status.CANCELLED}

    agg = projects_qs.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status=Project.Status.ACTIVE)),
        avg_completion=Avg("percentage_completion"),
        total_approved=Sum("approved_budget"),
        total_expenditure=Sum("budget_expenditure"),
    )

    over_budget_count = projects_qs.filter(
        approved_budget__gt=0,
        budget_expenditure__gt=F("approved_budget"),
    ).count()

    overdue_count = projects_qs.filter(
        end_date__lt=today,
    ).exclude(status__in=terminal_statuses).count()

    total_approved = _decimal(agg["total_approved"])
    total_expenditure = _decimal(agg["total_expenditure"])
    remaining = total_approved - total_expenditure

    project_ids = projects_qs.values_list("pk", flat=True)
    milestone_agg = Milestone.objects.filter(
        project_id__in=project_ids,
        deleted=False,
    ).aggregate(
        total=Count("id"),
        avg_completion=Avg("percentage_completion"),
    )

    by_status = [
        {"status": row["status"], "count": row["count"]}
        for row in projects_qs.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    ]

    by_governorate = [
        {
            "id": row["governorate_id"],
            "name": row["governorate__name_ar"] or row["governorate__name_en"] or "—",
            "count": row["count"],
        }
        for row in projects_qs.values("governorate_id", "governorate__name_ar", "governorate__name_en")
        .annotate(count=Count("id"))
        .order_by("-count", "governorate__name_ar")[:12]
    ]

    by_project_type = [
        {
            "id": row["annual_budget__project_type_id"],
            "name": row["annual_budget__project_type__name_ar"]
            or row["annual_budget__project_type__name_en"]
            or "—",
            "count": row["count"],
        }
        for row in projects_qs.values(
            "annual_budget__project_type_id",
            "annual_budget__project_type__name_ar",
            "annual_budget__project_type__name_en",
        )
        .annotate(count=Count("id"))
        .order_by("-count", "annual_budget__project_type__name_ar")[:12]
    ]

    def _project_row(p: Project) -> dict:
        approved = _decimal(p.approved_budget)
        spent = _decimal(p.budget_expenditure)
        exp_pct = _round_percent(spent, approved)
        return {
            "id": p.id,
            "code": p.code,
            "name_ar": p.name_ar,
            "status": p.status,
            "percentage_completion": float(p.percentage_completion or 0),
            "end_date": p.end_date.isoformat() if p.end_date else None,
            "approved_budget": str(approved),
            "budget_expenditure": str(spent),
            "expenditure_percent": exp_pct,
        }

    low_completion = [
        _project_row(p)
        for p in projects_qs.filter(status__in=active_statuses)
        .order_by("percentage_completion", "end_date")[:10]
    ]

    overdue_projects = [
        _project_row(p)
        for p in projects_qs.filter(end_date__lt=today)
        .exclude(status__in=terminal_statuses)
        .order_by("end_date")[:10]
    ]

    avg_completion = agg["avg_completion"]
    avg_milestone = milestone_agg["avg_completion"]

    (
        by_category,
        uncategorized_projects,
        uncategorized_expenditure,
        by_category_section,
    ) = build_category_project_counts(projects_qs)

    projects_with_milestones = (
        Milestone.objects.filter(project_id__in=project_ids, deleted=False)
        .values("project_id")
        .distinct()
        .count()
    )
    projects_without_milestones = (
        agg["total"] or 0) - projects_with_milestones

    return {
        "summary": {
            "total_projects": agg["total"] or 0,
            "active_projects": agg["active"] or 0,
            "avg_completion": round(float(avg_completion or 0), 1),
            "total_approved_budget": str(total_approved),
            "total_expenditure": str(total_expenditure),
            "expenditure_percent": _round_percent(total_expenditure, total_approved),
            "remaining_budget": str(remaining),
            "over_budget_count": over_budget_count,
            "overdue_count": overdue_count,
            "milestones_count": milestone_agg["total"] or 0,
            "avg_milestone_completion": round(float(avg_milestone or 0), 1),
            "projects_without_milestones": max(projects_without_milestones, 0),
        },
        "by_status": by_status,
        "by_governorate": by_governorate,
        "by_project_type": by_project_type,
        "by_category": by_category,
        "by_category_section": by_category_section,
        "uncategorized_projects": uncategorized_projects,
        "uncategorized_expenditure": uncategorized_expenditure,
        "low_completion_projects": low_completion,
        "overdue_projects": overdue_projects,
    }
