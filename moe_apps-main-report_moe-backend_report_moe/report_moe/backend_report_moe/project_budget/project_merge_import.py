"""Merge water-project metadata with budget milestones and import into the database."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from difflib import SequenceMatcher

from django.db import transaction
from locations.models import Community

from .budget_excel_import import (
    ParsedBudgetMilestone,
    ParsedBudgetProjectGroup,
    normalize_name,
)
from .models import (
    AnnualBudget,
    Foundation,
    MeasureUnit,
    Milestone,
    Policy,
    Project,
    ProjectCategory,
    Target,
)
from .water_projects_import import ParsedWaterProject

DEFAULT_COMPANY = "الشركة العامة لمياه الشرب والصرف الصحي في محافظة دمشق"
IMPORT_TAG = "[import-damascus-2026]"


@dataclass
class ImportMilestonePlan:
    name_ar: str
    category_code: str | None
    amount: Decimal | None
    source_sheet: str
    source_row: int


@dataclass
class ImportProjectPlan:
    name_ar: str
    section: str
    approved_budget: Decimal
    target: str
    policy: str
    quantitative_value: Decimal | None
    quantitative_unit: str | None
    water_row: int | None
    milestones: list[ImportMilestonePlan] = field(default_factory=list)
    source: str = "merged"


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()


def extract_focus_phrase(project_name: str) -> str | None:
    matches = re.findall(r"\(([^)]+)\)", project_name)
    if matches:
        return matches[-1].strip()
    if "منطقة" in project_name:
        segment = project_name.split("منطقة", 1)[1].strip()
        if segment:
            return f"منطقة {segment.split('(')[0].strip()}"
    if "/" in project_name:
        tail = project_name.split("/")[-1].strip(" /")
        if len(tail) >= 4:
            return tail
    return None


def milestone_matches_project(project_name: str, milestone: ParsedBudgetMilestone) -> float:
    """Return similarity score; 0 means no match."""
    focus = extract_focus_phrase(project_name)
    name_norm = normalize_name(milestone.name_ar)

    if focus:
        focus_norm = normalize_name(focus)
        if focus_norm and (focus_norm in name_norm or name_norm in focus_norm):
            return 0.98
        focus_score = similarity(focus, milestone.name_ar)
        if focus_score >= 0.78:
            return focus_score
        return 0.0

    project_norm = normalize_name(project_name)
    group_norm = normalize_name(milestone.project_group or "")

    if project_norm == name_norm:
        return 1.0
    if project_norm == group_norm:
        return 0.95
    if project_norm in name_norm or name_norm in project_norm:
        return 0.92
    if group_norm and (project_norm in group_norm or group_norm in project_norm):
        return 0.88

    name_score = similarity(project_name, milestone.name_ar)
    group_score = (
        similarity(project_name, milestone.project_group or "")
        if milestone.project_group
        else 0.0
    )
    return max(name_score, group_score)


def milestone_row_key(milestone: ParsedBudgetMilestone) -> tuple[str, int]:
    return milestone.sheet, milestone.row


def assign_milestones_to_projects(
    water_projects: list[ParsedWaterProject],
    milestones: list[ParsedBudgetMilestone],
    *,
    threshold: float = 0.78,
) -> dict[int, list[ParsedBudgetMilestone]]:
    assignments: dict[int, list[ParsedBudgetMilestone]] = {
        water.row: [] for water in water_projects
    }
    used_rows: set[tuple[str, int]] = set()

    candidates: list[tuple[float, int, ParsedBudgetMilestone]] = []
    for water in water_projects:
        for milestone in milestones:
            score = milestone_matches_project(water.name_ar, milestone)
            if score >= threshold:
                candidates.append((score, water.row, milestone))

    candidates.sort(
        key=lambda item: (-item[0], item[1], item[2].sheet, item[2].row))
    for score, water_row, milestone in candidates:
        key = milestone_row_key(milestone)
        if key in used_rows:
            continue
        assignments[water_row].append(milestone)
        used_rows.add(key)

    for water_row in assignments:
        assignments[water_row].sort(key=lambda item: (item.sheet, item.row))
    return assignments


def collect_milestones_for_project(
    project_name: str,
    milestones: list[ParsedBudgetMilestone],
) -> list[ParsedBudgetMilestone]:
    matched = [
        item
        for item in milestones
        if milestone_matches_project(project_name, item) >= 0.78
    ]
    matched.sort(key=lambda item: (item.sheet, item.row))
    return matched


def build_import_plans(
    water_projects: list[ParsedWaterProject],
    budget_milestones: list[ParsedBudgetMilestone],
    budget_groups: list[ParsedBudgetProjectGroup],
    *,
    include_budget_groups: bool = False,
) -> list[ImportProjectPlan]:
    used_milestone_rows: set[tuple[str, int]] = set()
    plans: list[ImportProjectPlan] = []
    milestone_assignments = assign_milestones_to_projects(
        water_projects,
        budget_milestones,
    )

    for water in water_projects:
        matched = milestone_assignments.get(water.row, [])
        for item in matched:
            used_milestone_rows.add(milestone_row_key(item))

        milestone_plans = [
            ImportMilestonePlan(
                name_ar=item.name_ar,
                category_code=item.category_code,
                amount=item.amount,
                source_sheet=item.sheet,
                source_row=item.row,
            )
            for item in matched
        ]

        if not milestone_plans:
            milestone_plans.append(
                ImportMilestonePlan(
                    name_ar=water.name_ar,
                    category_code=None,
                    amount=water.approved_budget,
                    source_sheet="water",
                    source_row=water.row,
                )
            )

        section = matched[0].section if matched else ""
        approved = water.approved_budget or Decimal("0")
        if approved <= 0:
            approved = sum(
                (item.amount or Decimal("0")) for item in milestone_plans
            )

        plans.append(
            ImportProjectPlan(
                name_ar=water.name_ar,
                section=section,
                approved_budget=approved,
                target=water.target,
                policy=water.policy,
                quantitative_value=water.quantitative_value,
                quantitative_unit=water.quantitative_unit,
                water_row=water.row,
                milestones=milestone_plans,
                source="water+budget",
            )
        )

    if not include_budget_groups:
        return plans

    for group in budget_groups:
        if any(similarity(group.name_ar, plan.name_ar) >= 0.78 for plan in plans):
            continue

        remaining = [
            item for item in group.milestones if milestone_row_key(item) not in used_milestone_rows
        ]
        if not remaining:
            continue

        plans.append(
            ImportProjectPlan(
                name_ar=group.name_ar,
                section=group.section,
                approved_budget=group.total_amount,
                target="",
                policy="",
                quantitative_value=None,
                quantitative_unit=None,
                water_row=None,
                milestones=[
                    ImportMilestonePlan(
                        name_ar=item.name_ar,
                        category_code=item.category_code,
                        amount=item.amount,
                        source_sheet=item.sheet,
                        source_row=item.row,
                    )
                    for item in remaining
                ],
                source="budget-group",
            )
        )

    return plans


@dataclass
class ImportSummary:
    projects_created: int = 0
    projects_updated: int = 0
    milestones_created: int = 0
    targets_created: int = 0
    policies_created: int = 0
    units_created: int = 0
    missing_categories: list[str] = field(default_factory=list)


class DamascusProjectImporter:
    def __init__(
        self,
        *,
        annual_budget: AnnualBudget,
        foundation: Foundation,
        community: Community,
        start_date: date,
        end_date: date,
    ):
        self.annual_budget = annual_budget
        self.foundation = foundation
        self.community = community
        self.start_date = start_date
        self.end_date = end_date
        self._target_cache: dict[str, Target] = {}
        self._policy_cache: dict[str, Policy] = {}
        self._unit_cache: dict[str, MeasureUnit] = {}
        self._category_cache: dict[str, ProjectCategory | None] = {}

    def _get_target(self, name: str) -> tuple[Target | None, bool]:
        if not name:
            return None, False
        if name in self._target_cache:
            return self._target_cache[name], False
        target, created = Target.objects.get_or_create(
            name_ar=name,
            defaults={"name_en": "", "description": IMPORT_TAG},
        )
        self._target_cache[name] = target
        return target, created

    def _get_policy(self, name: str) -> tuple[Policy | None, bool]:
        if not name:
            return None, False
        if name in self._policy_cache:
            return self._policy_cache[name], False
        policy, created = Policy.objects.get_or_create(
            name_ar=name,
            defaults={"name_en": "", "description": IMPORT_TAG},
        )
        self._policy_cache[name] = policy
        return policy, created

    def _get_unit(self, name: str | None) -> tuple[MeasureUnit | None, bool]:
        if not name:
            return None, False
        if name in self._unit_cache:
            return self._unit_cache[name], False
        unit, created = MeasureUnit.objects.get_or_create(
            name_ar=name,
            defaults={"name_en": "", "symbol": ""},
        )
        self._unit_cache[name] = unit
        return unit, created

    def _get_category(self, code: str | None) -> ProjectCategory | None:
        if not code:
            return None
        if code in self._category_cache:
            return self._category_cache[code]
        category = ProjectCategory.objects.filter(
            code=code, deleted=False).first()
        self._category_cache[code] = category
        return category

    def import_plans(
        self,
        plans: list[ImportProjectPlan],
        *,
        replace_existing: bool = False,
    ) -> ImportSummary:
        summary = ImportSummary()

        with transaction.atomic():
            if replace_existing:
                existing = Project.objects.filter(
                    annual_budget=self.annual_budget,
                    foundation=self.foundation,
                    deleted=False,
                    description__contains=IMPORT_TAG,
                )
                for project in existing:
                    project.milestones.filter(
                        deleted=False).update(deleted=True)
                    project.deleted = True
                    project.save(update_fields=["deleted"])

            for plan in plans:
                target, target_created = self._get_target(plan.target)
                policy, policy_created = self._get_policy(plan.policy)
                unit, unit_created = self._get_unit(plan.quantitative_unit)

                if target_created:
                    summary.targets_created += 1
                if policy_created:
                    summary.policies_created += 1
                if unit_created:
                    summary.units_created += 1

                project = Project.objects.filter(
                    annual_budget=self.annual_budget,
                    foundation=self.foundation,
                    deleted=False,
                    name_ar=plan.name_ar,
                ).first()

                description = (
                    f"{IMPORT_TAG} section={plan.section or '-'} source={plan.source}"
                )
                if project:
                    project.approved_budget = plan.approved_budget
                    project.proposed_budget = plan.approved_budget
                    project.target = target
                    project.policy = policy
                    project.quantitative_target_value = plan.quantitative_value
                    project.quantitative_target_unit = unit
                    project.description = description
                    project.community = self.community
                    project.start_date = self.start_date
                    project.end_date = self.end_date
                    project.save()
                    project.milestones.filter(
                        deleted=False).update(deleted=True)
                    summary.projects_updated += 1
                else:
                    project = Project.objects.create(
                        annual_budget=self.annual_budget,
                        foundation=self.foundation,
                        community=self.community,
                        name_ar=plan.name_ar,
                        approved_budget=plan.approved_budget,
                        proposed_budget=plan.approved_budget,
                        target=target,
                        policy=policy,
                        quantitative_target_value=plan.quantitative_value,
                        quantitative_target_unit=unit,
                        description=description,
                        start_date=self.start_date,
                        end_date=self.end_date,
                        status=Project.Status.DRAFT,
                    )
                    summary.projects_created += 1

                for order, milestone_plan in enumerate(plan.milestones, start=1):
                    category = self._get_category(milestone_plan.category_code)
                    if milestone_plan.category_code and category is None:
                        if milestone_plan.category_code not in summary.missing_categories:
                            summary.missing_categories.append(
                                milestone_plan.category_code)

                    Milestone.objects.create(
                        project=project,
                        category=category,
                        name_ar=milestone_plan.name_ar,
                        order=order,
                        status=Milestone.Status.DRAFT,
                    )
                    summary.milestones_created += 1

        return summary
