"""Import docs/titles/*/rows.json row data into Info (same validation as Excel import)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from dynamic_forms.audit_log import log_action
from dynamic_forms.title_json_import import import_json_file

User = get_user_model()

DEFAULT_TEMPLATE_GLOB = "rows.json"


class Command(BaseCommand):
    help = (
        "Import row data from docs/titles/*/rows.json into Info records. "
        "Uses the same validation as Excel import. Title is matched from JSON "
        '"title" field (or --title-id). Requires attributes to exist first '
        "(run import_attribute_labels)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to one JSON file (default: all docs/titles/*/rows.json with data)",
        )
        parser.add_argument(
            "--title-id",
            type=int,
            default=None,
            help="Force Title id (overrides JSON title name)",
        )
        parser.add_argument(
            "--email",
            "--username",
            dest="email",
            type=str,
            default=None,
            help="User email for Info.user (default: first active superuser). "
                 "--username is accepted as a legacy alias.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate only; no database writes.",
        )

    def handle(self, *args, **options):
        user = self._resolve_user(options["email"])
        dry_run = options["dry_run"]
        title_id = options["title_id"]

        paths = self._resolve_paths(options["file"])
        if not paths:
            raise CommandError("No JSON files to import.")

        total_imported = 0
        total_skipped = 0
        total_errors = 0
        had_failure = False

        for path in paths:
            self.stdout.write(self.style.NOTICE(f"Processing {path.name} ..."))
            title, result = import_json_file(
                path=path,
                user=user,
                title_id=title_id,
                dry_run=dry_run,
                log_action=None if dry_run else self._audit_logger(user),
            )
            if title is None:
                had_failure = True
                for err in result.get("errors", []):
                    self.stderr.write(
                        self.style.ERROR(
                            f"  row {err.get('row')}: {err.get('message')}")
                    )
                continue

            imported = result.get("imported_rows", 0)
            skipped = result.get("skipped_rows", 0)
            errors = result.get("errors", [])
            total_imported += imported
            total_skipped += skipped
            total_errors += len(errors)

            prefix = "[dry-run] " if dry_run else ""
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {prefix}Title: {title.name} (id={title.id}) — "
                    f"imported={imported}, skipped={skipped}, errors={len(errors)}"
                )
            )
            for err in errors[:20]:
                self.stderr.write(
                    self.style.WARNING(
                        f"    row {err.get('row')}: {err.get('message')}")
                )
            if len(errors) > 20:
                self.stderr.write(
                    self.style.WARNING(
                        f"    ... and {len(errors) - 20} more errors")
                )
            if errors and imported == 0:
                had_failure = True

        self.stdout.write(
            self.style.NOTICE(
                f"Done — imported={total_imported}, skipped={total_skipped}, "
                f"errors={total_errors}, files={len(paths)}"
            )
        )
        if had_failure and not dry_run and total_imported == 0:
            raise CommandError(
                "Import finished with blocking errors (see messages above).")

    def _resolve_user(self, email: str | None):
        if email:
            user = User.objects.filter(email__iexact=email.strip()).first()
            if user is None:
                raise CommandError(f"User not found: {email!r}")
            return user
        user = User.objects.filter(
            is_superuser=True, is_active=True).order_by("id").first()
        if user is None:
            raise CommandError("No active superuser found; pass --email.")
        return user

    def _resolve_paths(self, file_arg: str | None) -> list[Path]:
        if file_arg:
            path = Path(file_arg).resolve()
            if not path.is_file():
                raise CommandError(f"File not found: {path}")
            return [path]

        titles_root = Path(settings.BASE_DIR).resolve(
        ).parent / "docs" / "titles"
        if not titles_root.is_dir():
            raise CommandError(f"Titles directory not found: {titles_root}")

        paths = sorted(titles_root.glob(f"*/{DEFAULT_TEMPLATE_GLOB}"))
        if not paths:
            raise CommandError(f"No rows.json files under {titles_root}")
        return paths

    def _audit_logger(self, user):
        req = SimpleNamespace(user=user, META={})

        def _log(*, details):
            log_action(req, "CREATE", "Info", details=details)

        return _log
