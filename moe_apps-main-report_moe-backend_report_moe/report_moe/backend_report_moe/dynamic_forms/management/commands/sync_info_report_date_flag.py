"""Realign Info.is_report_date with Attribute.is_report_date.

Info carries a copy of the flag because the uniqueness constraint cannot join to
the attribute table. Toggling the flag on an Attribute therefore leaves existing
Info rows stale; this repairs them. Run it after changing the flag, and whenever
`check_report_date_flags` reports drift.

    python manage.py sync_info_report_date_flag            # report only
    python manage.py sync_info_report_date_flag --apply
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db.models import F

from dynamic_forms.models import Info


class Command(BaseCommand):
    help = "Copy Attribute.is_report_date onto its Info rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the changes. Without it the command only reports.",
        )

    def handle(self, *args, **opts):
        stale = Info.objects.exclude(
            is_report_date=F("attribute__is_report_date")
        )
        to_set = stale.filter(attribute__is_report_date=True).count()
        to_clear = stale.filter(attribute__is_report_date=False).count()

        self.stdout.write(f"rows to set   : {to_set}")
        self.stdout.write(f"rows to clear : {to_clear}")

        if not opts["apply"]:
            if to_set or to_clear:
                self.stdout.write(
                    self.style.WARNING("\nPreview only — re-run with --apply.")
                )
            else:
                self.stdout.write(self.style.SUCCESS("Already in sync."))
            return

        # Two passes rather than one F() update: the constraint is partial, and
        # clearing before setting avoids transient duplicate keys.
        cleared = stale.filter(attribute__is_report_date=False).update(
            is_report_date=False
        )
        was_set = Info.objects.exclude(
            is_report_date=F("attribute__is_report_date")
        ).filter(attribute__is_report_date=True).update(is_report_date=True)
        self.stdout.write(
            self.style.SUCCESS(f"\nCleared {cleared}, set {was_set}.")
        )
