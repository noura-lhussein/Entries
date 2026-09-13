"""Remove duplicate Info rows, keeping the earliest of each identical group.

A duplicate group = same (attribute, sub_main, user, value, confirmed).
Safe by default: prints what would be deleted. Pass --apply to delete.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Min

from dynamic_forms.models import Info

GROUP_FIELDS = ("attribute_id", "sub_main_id", "user_id", "value", "confirmed")


class Command(BaseCommand):
    help = "Delete duplicate Info rows, keeping the earliest per identical group."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually delete duplicates (default is a dry run).",
        )

    def handle(self, *args, **options):
        apply = options["apply"]

        groups = (
            Info.objects.values(*GROUP_FIELDS)
            .annotate(n=Count("id"), keep_id=Min("id"))
            .filter(n__gt=1)
        )

        group_count = groups.count()
        ids_to_delete: list[int] = []
        for g in groups:
            filters = {f: g[f] for f in GROUP_FIELDS}
            extra_ids = list(
                Info.objects.filter(**filters)
                .exclude(id=g["keep_id"])
                .values_list("id", flat=True)
            )
            ids_to_delete.extend(extra_ids)

        total = Info.objects.count()
        self.stdout.write(f"Total Info rows: {total}")
        self.stdout.write(f"Duplicate groups: {group_count}")
        self.stdout.write(
            f"Rows to remove (keeping earliest): {len(ids_to_delete)}")

        if not ids_to_delete:
            self.stdout.write("Nothing to clean.")
            return

        if not apply:
            self.stdout.write(
                "Dry run only. Re-run with --apply to delete the rows above."
            )
            return

        with transaction.atomic():
            deleted, _ = Info.objects.filter(id__in=ids_to_delete).delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {deleted} duplicate rows."))
