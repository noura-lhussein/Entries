from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count

from project_budget.category_tree_import import (
    build_category_tree_rows,
    filter_investment_assistant_roots,
    parse_category_tree_xlsx,
)
from project_budget.models import Milestone, ProjectCategory


class Command(BaseCommand):
    help = "Import project categories from docs/badjet/TREE.xlsx (hierarchical budget tree)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="",
            help="Path to TREE.xlsx (default: docs/badjet/TREE.xlsx under repo root)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report counts without writing to the database",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Soft-delete existing categories without milestones before import",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Hard-delete all categories (blocked if any milestone uses a category)",
        )
        parser.add_argument(
            "--investment-only",
            action="store_true",
            help=(
                "Import only under النفقات الاستثمارية (section 3); "
                "311/312/313/... are top-level parents with their children"
            ),
        )

    def handle(self, *args, **options):
        file_path = self._resolve_file(options["file"])
        if not file_path.is_file():
            raise CommandError(f"File not found: {file_path}")

        parsed = parse_category_tree_xlsx(file_path)
        tree_rows = build_category_tree_rows(parsed)
        if options["investment_only"]:
            tree_rows = filter_investment_assistant_roots(tree_rows)

        roots = sum(1 for _, parent in tree_rows if parent is None)
        mode = "investment (311+ as roots)" if options["investment_only"] else "full tree"
        self.stdout.write(
            f"Parsed {len(parsed)} rows -> {len(tree_rows)} categories ({roots} roots) [{mode}]"
        )

        if options["dry_run"]:
            self.stdout.write(self.style.WARNING(
                "Dry run - no database changes."))
            return

        with transaction.atomic():
            if options["purge"]:
                self._purge_all_categories()

            if options["replace"] and not options["purge"]:
                blocked = ProjectCategory.objects.filter(
                    deleted=False, milestones__deleted=False
                ).distinct()
                if blocked.exists():
                    raise CommandError(
                        "Cannot --replace: some categories are linked to milestones. "
                        "Use --purge only when safe, or remove milestone links first."
                    )
                for category in ProjectCategory.objects.filter(deleted=False):
                    if category.deletion_blockers():
                        category.deleted = True
                        category.save(update_fields=["deleted", "updated_at"])

            created = 0
            by_code: dict[str, ProjectCategory] = {}

            for item, parent_code in tree_rows:
                parent = by_code.get(parent_code) if parent_code else None
                category = ProjectCategory.objects.create(
                    parent=parent,
                    name_ar=item.name_ar,
                    name_en="",
                    code=item.code,
                )
                created += 1
                by_code[item.code] = category

        self.stdout.write(
            self.style.SUCCESS(f"Import complete: {created} created.")
        )

    def _purge_all_categories(self) -> None:
        if Milestone.objects.exclude(category__isnull=True).exists():
            raise CommandError(
                "Cannot --purge: milestones are linked to categories. "
                "Clear milestone categories first."
            )

        deleted_total = 0
        while ProjectCategory.objects.exists():
            leaves = ProjectCategory.objects.annotate(
                child_count=Count("children")
            ).filter(child_count=0)
            if not leaves.exists():
                raise CommandError(
                    "Cannot --purge: broken category tree (cycle?).")
            count, _ = leaves.delete()
            deleted_total += count

        self.stdout.write(f"Purged {deleted_total} category row(s).")

    def _resolve_file(self, file_option: str) -> Path:
        if file_option:
            return Path(file_option).expanduser().resolve()
        base_dir = Path(settings.BASE_DIR).resolve()
        return (base_dir.parent / "docs" / "badjet" / "TREE.xlsx").resolve()
