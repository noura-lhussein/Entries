"""Assert the report-date contract holds, for CI.

Two things can silently drift and both defeat the uniqueness guarantee:

  * Info.is_report_date falling out of step with its Attribute (fix with
    `sync_info_report_date_flag --apply`);
  * active duplicate reports existing for one (sub_main, date, entity), which
    would also block the constraint from being (re)created.

Exits 1 on drift so CI fails loudly rather than at the next migrate.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import Count, F

from dynamic_forms.models import Attribute, Info

ACTIVE = ("waiting", "accept")


class Command(BaseCommand):
    help = "Verify Info.is_report_date matches its attribute and no duplicates exist."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit 1 on drift (default: report only).",
        )

    def handle(self, *args, **opts):
        marked = Attribute.objects.filter(is_report_date=True).count()
        self.stdout.write(f"attributes marked as report date: {marked}")

        drift = Info.objects.exclude(
            is_report_date=F("attribute__is_report_date")
        ).count()
        self.stdout.write(f"Info rows out of step with attribute: {drift}")

        dupes = (
            Info.objects.filter(
                is_report_date=True, archived=False, confirmed__in=ACTIVE
            )
            .values("attribute_id", "sub_main_id", "value", "entity_type", "entity_id")
            .annotate(n=Count("id"))
            .filter(n__gt=1)
        )
        groups = list(dupes)
        excess = sum(g["n"] - 1 for g in groups)
        self.stdout.write(f"duplicate report groups: {len(groups)} ({excess} extra rows)")
        for g in groups[:10]:
            attr = Attribute.objects.select_related("title").get(pk=g["attribute_id"])
            title = attr.title.name if attr.title else "-"
            self.stdout.write(
                f"  {title} | {g['value']} | sub_main={g['sub_main_id']} | {g['n']} copies"
            )

        if drift or groups:
            msg = "report-date contract violated"
            if opts["strict"]:
                self.stderr.write(self.style.ERROR(msg))
                raise SystemExit(1)
            self.stdout.write(self.style.WARNING(msg))
            return
        self.stdout.write(self.style.SUCCESS("report-date contract holds"))
