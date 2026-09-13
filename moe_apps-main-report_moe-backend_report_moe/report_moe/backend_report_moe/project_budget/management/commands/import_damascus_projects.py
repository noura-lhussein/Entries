from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from locations.models import Community

from project_budget.budget_excel_import import parse_budget_workbook
from project_budget.models import AnnualBudget, Foundation
from project_budget.project_merge_import import (
    DEFAULT_COMPANY,
    DamascusProjectImporter,
    build_import_plans,
)
from project_budget.water_projects_import import parse_water_projects_workbook


class Command(BaseCommand):
    help = (
        "Import Damascus 2026 projects from budget + water Excel files: "
        "project metadata (target/policy/quantitative) and milestones with categories."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--budget-file",
            type=str,
            default="",
            help="Path to مشروع الموازنة الاستثمارية...xlsx",
        )
        parser.add_argument(
            "--water-file",
            type=str,
            default="",
            help="Path to إجمالي مشاريع شركات المياه...xlsx",
        )
        parser.add_argument(
            "--company",
            type=str,
            default=DEFAULT_COMPANY,
            help="Filter water workbook to this company name",
        )
        parser.add_argument(
            "--annual-budget-id",
            type=int,
            required=False,
            help="AnnualBudget id for imported projects (default: latest 2026 budget)",
        )
        parser.add_argument(
            "--foundation-id",
            type=int,
            required=False,
            help="Foundation id (default: first active foundation)",
        )
        parser.add_argument(
            "--community-id",
            type=int,
            required=False,
            help="Community id (default: first active community)",
        )
        parser.add_argument(
            "--start-date",
            type=str,
            default="2026-01-01",
            help="Default project start date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--end-date",
            type=str,
            default="2026-12-31",
            help="Default project end date (YYYY-MM-DD)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and print import plan without writing to the database",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Soft-delete previously imported projects (tagged) before import",
        )
        parser.add_argument(
            "--include-budget-groups",
            action="store_true",
            help="Also import unmatched budget project groups as standalone projects",
        )

    def handle(self, *args, **options):
        budget_path = self._resolve_budget_file(options["budget_file"])
        water_path = self._resolve_water_file(options["water_file"])
        if not budget_path.is_file():
            raise CommandError(f"Budget file not found: {budget_path}")
        if not water_path.is_file():
            raise CommandError(f"Water file not found: {water_path}")

        water_projects = parse_water_projects_workbook(
            water_path,
            company_filter=options["company"] or None,
        )
        budget_milestones, budget_groups = parse_budget_workbook(budget_path)
        plans = build_import_plans(
            water_projects,
            budget_milestones,
            budget_groups,
            include_budget_groups=options["include_budget_groups"],
        )

        self.stdout.write(
            f"Parsed water projects: {len(water_projects)} | "
            f"budget milestones: {len(budget_milestones)} | "
            f"budget groups: {len(budget_groups)} | "
            f"import plans: {len(plans)}"
        )

        if options["dry_run"]:
            self._print_dry_run(plans)
            return

        annual_budget = self._resolve_annual_budget(
            options["annual_budget_id"])
        foundation = self._resolve_foundation(options["foundation_id"])
        community = self._resolve_community(options["community_id"])
        start_date = date.fromisoformat(options["start_date"])
        end_date = date.fromisoformat(options["end_date"])

        importer = DamascusProjectImporter(
            annual_budget=annual_budget,
            foundation=foundation,
            community=community,
            start_date=start_date,
            end_date=end_date,
        )
        summary = importer.import_plans(
            plans, replace_existing=options["replace"])

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete: "
                f"projects +{summary.projects_created} ~{summary.projects_updated}, "
                f"milestones {summary.milestones_created}, "
                f"targets {summary.targets_created}, "
                f"policies {summary.policies_created}, "
                f"units {summary.units_created}"
            )
        )
        if summary.missing_categories:
            self.stdout.write(
                self.style.WARNING(
                    "Missing category codes: "
                    + ", ".join(summary.missing_categories[:20])
                )
            )

    def _print_dry_run(self, plans):
        for index, plan in enumerate(plans, start=1):
            self.stdout.write(
                f"\n[{index}] {plan.name_ar} "
                f"(budget={plan.approved_budget}, section={plan.section or '-'}, "
                f"milestones={len(plan.milestones)}, source={plan.source})"
            )
            if plan.target:
                self.stdout.write(f"  target: {plan.target[:90]}")
            if plan.policy:
                self.stdout.write(f"  policy: {plan.policy[:90]}")
            if plan.quantitative_value is not None:
                self.stdout.write(
                    f"  quantitative: {plan.quantitative_value} {plan.quantitative_unit or ''}"
                )
            for milestone in plan.milestones[:8]:
                self.stdout.write(
                    f"  - [{milestone.category_code or '-'}] {milestone.name_ar[:90]}"
                )
            if len(plan.milestones) > 8:
                self.stdout.write(
                    f"  ... +{len(plan.milestones) - 8} more milestones")

    def _repo_root(self) -> Path:
        return Path(settings.BASE_DIR).parent

    def _resolve_budget_file(self, override: str) -> Path:
        if override:
            return Path(override)
        return (
            self._repo_root()
            / "docs"
            / "badjet"
            / "مشروع الموازنة الاستثمارية لعام 2026 ليرة جديدة.xlsx"
        )

    def _resolve_water_file(self, override: str) -> Path:
        if override:
            return Path(override)
        return (
            self._repo_root()
            / "docs"
            / "badjet"
            / "إجمالي مشاريع شركات المياه والصرف الصحي وفق أهداف وسياسات وزارة الطاقة.xlsx"
        )

    def _resolve_annual_budget(self, budget_id: int | None) -> AnnualBudget:
        if budget_id:
            return AnnualBudget.objects.get(pk=budget_id)
        budget = (
            AnnualBudget.objects.filter(year=2026)
            .annotate(project_count=Count("projects"))
            .order_by("-id")
            .first()
        )
        if budget is None:
            raise CommandError(
                "No 2026 AnnualBudget found; pass --annual-budget-id")
        return budget

    def _resolve_foundation(self, foundation_id: int | None) -> Foundation:
        if foundation_id:
            return Foundation.objects.get(pk=foundation_id, deleted=False)
        foundation = Foundation.objects.filter(
            deleted=False).order_by("id").first()
        if foundation is None:
            raise CommandError("No foundation found; pass --foundation-id")
        return foundation

    def _resolve_community(self, community_id: int | None) -> Community:
        if community_id:
            return Community.objects.get(pk=community_id, deleted=False)
        community = Community.objects.filter(
            deleted=False).order_by("id").first()
        if community is None:
            raise CommandError("No community found; pass --community-id")
        return community
