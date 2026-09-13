"""Assign row_key to legacy Info rows using the same slot grouping as admin tables."""

import uuid

from django.core.management.base import BaseCommand
from django.db import transaction

from dynamic_forms.models import Attribute, Info, Title
from dynamic_forms.row_grouping import group_table_rows, split_table_textarea_attrs


class Command(BaseCommand):
    help = "Backfill Info.row_key for existing data (per title/sub_main/user logical row)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report counts without writing.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated_infos = 0
        ambiguous = 0

        title_ids = Title.objects.values_list("id", flat=True)
        for title_id in title_ids:
            attrs = list(Attribute.objects.filter(title_id=title_id))
            table_attrs, _ = split_table_textarea_attrs(attrs)
            if not table_attrs:
                continue

            sub_ids = (
                Info.objects.filter(attribute__title_id=title_id)
                .values_list("sub_main_id", flat=True)
                .distinct()
            )
            for sub_main_id in sub_ids:
                if not sub_main_id:
                    continue
                infos = list(
                    Info.objects.filter(
                        attribute__title_id=title_id,
                        sub_main_id=sub_main_id,
                    ).select_related("attribute", "user", "sub_main")
                )
                if not infos:
                    continue
                slots = group_table_rows(infos, table_attrs)
                for slot in slots:
                    ids = slot.get("_info_ids") or []
                    if not ids:
                        continue
                    existing = list(
                        Info.objects.filter(id__in=ids).values_list(
                            "row_key", flat=True
                        )
                    )
                    keys = {k for k in existing if k is not None}
                    if len(keys) > 1:
                        ambiguous += 1
                    row_key = keys.pop() if len(keys) == 1 else uuid.uuid4()
                    missing = sum(1 for k in existing if k is None)
                    if missing == 0 and len(keys) == 1:
                        continue
                    if dry_run:
                        updated_infos += missing if missing else len(ids)
                        continue
                    with transaction.atomic():
                        updated_infos += Info.objects.filter(id__in=ids).update(
                            row_key=row_key
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would update' if dry_run else 'Updated'} {updated_infos} Info rows; "
                f"ambiguous groups: {ambiguous}"
            )
        )
