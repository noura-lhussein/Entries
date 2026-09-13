"""Export database fixture as UTF-8 JSON (avoids Windows cp1252 errors with Arabic text)."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Same as dumpdata but always writes UTF-8. "
        "Use when dumpdata -o fails with charmap/codec errors on Windows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "-o",
            "--output",
            default="sqlite_export.json",
            help="Output JSON path (default: sqlite_export.json)",
        )
        parser.add_argument(
            "--exclude",
            "-e",
            action="append",
            default=[],
            help="App or model to exclude (repeatable). Defaults: contenttypes, auth.Permission",
        )

    def handle(self, *args, **options):
        output = Path(options["output"]).resolve()
        excludes = options["exclude"] or ["contenttypes", "auth.Permission"]

        buffer = io.StringIO()
        call_command(
            "dumpdata",
            natural_foreign=True,
            natural_primary=True,
            indent=2,
            exclude=excludes,
            stdout=buffer,
            verbosity=0,
        )
        output.write_text(buffer.getvalue(), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"Wrote {output} ({output.stat().st_size} bytes)"))
