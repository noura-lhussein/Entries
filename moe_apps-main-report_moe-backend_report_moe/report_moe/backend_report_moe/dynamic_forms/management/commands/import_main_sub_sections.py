"""Import docs/main-sub-sections.json into MainSection and SubMainSection."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from locations.models import District as LocationDistrict

from dynamic_forms.models import MainSection, SubMainSection


class Command(BaseCommand):
    help = (
        "Import main-sub-sections.json (hierarchy of MainSection + SubMainSection) "
        "into the database. Not linked to Title."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to JSON (default: <repo>/docs/main-sub-sections.json)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report only; no database writes.",
        )

    def handle(self, *args, **options):
        path = options["file"]
        if path:
            json_path = Path(path).resolve()
        else:
            json_path = (
                Path(settings.BASE_DIR).resolve().parent
                / "docs"
                / "schema"
                / "main-sub-sections.json"
            )
        if not json_path.is_file():
            raise CommandError(f"JSON file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        hierarchy = data.get("hierarchy")
        if not isinstance(hierarchy, list):
            raise CommandError("JSON must contain a 'hierarchy' array.")

        dry = options["dry_run"]
        stats = {
            "main_sections_created": 0,
            "main_sections_existing": 0,
            "sub_main_sections_created": 0,
            "sub_main_sections_existing": 0,
            "warnings": 0,
        }

        def run_import() -> None:
            for i, block in enumerate(hierarchy, start=1):
                if not isinstance(block, dict):
                    self.stderr.write(
                        self.style.WARNING(
                            f"Block {i}: skipped (not an object).")
                    )
                    stats["warnings"] += 1
                    continue
                m = block.get("main_section") or {}
                main_name = (m.get("name") or "").strip()
                if not main_name:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Block {i}: missing main_section.name, skipped.")
                    )
                    stats["warnings"] += 1
                    continue

                ms, ms_created = MainSection.objects.get_or_create(
                    name=main_name)
                if ms_created:
                    stats["main_sections_created"] += 1
                else:
                    stats["main_sections_existing"] += 1

                subs = block.get("sub_main_sections")
                if not isinstance(subs, list):
                    continue
                for j, s in enumerate(subs, start=1):
                    if not isinstance(s, dict):
                        stats["warnings"] += 1
                        continue
                    sub_name = (s.get("name") or "").strip()
                    if not sub_name:
                        stats["warnings"] += 1
                        continue
                    location_district_id = s.get("location_district_id") or s.get(
                        "district_id"
                    )
                    location_district = None
                    if location_district_id is not None:
                        location_district = LocationDistrict.objects.filter(
                            pk=location_district_id
                        ).first()
                        if location_district is None:
                            self.stderr.write(
                                self.style.WARNING(
                                    f"Block {i} sub {j}: location_district_id="
                                    f"{location_district_id!r} not found, using null."
                                )
                            )
                            stats["warnings"] += 1
                    sub_obj, sub_created = SubMainSection.objects.get_or_create(
                        main_section=ms,
                        name=sub_name,
                        defaults={"location_district": location_district},
                    )
                    if sub_created:
                        stats["sub_main_sections_created"] += 1
                    else:
                        stats["sub_main_sections_existing"] += 1
                        if (
                            location_district
                            and sub_obj.location_district_id != location_district.id
                        ):
                            sub_obj.location_district = location_district
                            sub_obj.save(update_fields=["location_district"])

        if dry:
            self.stdout.write(
                self.style.NOTICE(
                    f"[dry-run] Would read {len(hierarchy)} main blocks from {json_path}"
                )
            )
            return

        with transaction.atomic():
            run_import()

        self.stdout.write(self.style.SUCCESS(f"Imported from {json_path}"))
        for k, v in stats.items():
            self.stdout.write(f"  {k}: {v}")
