"""Import docs/attribute-labels.json into Attribute and Option (existing Title only)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dynamic_forms.models import Attribute, Option, Title

VALID_ATTR_TYPES = {c[0] for c in Attribute.TYPE_CHOICES}


def _coerce_required(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)


def _option_label(entry: object) -> str:
    if isinstance(entry, str):
        return entry.strip()[:255]
    if isinstance(entry, dict):
        return (
            (entry.get("label") or entry.get("attribute-label") or "")
            .strip()[:255]
        )
    return ""


def _norm_title_name(s: str) -> str:
    s = s.strip().rstrip(":").rstrip(".")
    s = re.sub(r"\s+", " ", s)
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return s


class Command(BaseCommand):
    help = (
        "Import attribute-labels.json into Attribute and Option only. "
        "Title rows must already exist: match by title_id (preferred) or by exact / "
        "normalized name. Use --create-titles only if you intentionally want new titles."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=None,
            help="Path to JSON (default: <repo>/docs/attribute-labels.json)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse and report only; no database writes.",
        )
        parser.add_argument(
            "--create-titles",
            action="store_true",
            help="Allow creating missing Title rows (default: off; only attach to existing).",
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
                / "attribute-labels.json"
            )
        if not json_path.is_file():
            raise CommandError(f"JSON file not found: {json_path}")

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        dry = options["dry_run"]
        allow_create_titles = options["create_titles"]

        stats = {
            "title_blocks_matched": 0,
            "titles_created": 0,
            "titles_missing": 0,
            "attributes_created": 0,
            "attributes_existing": 0,
            "options_created": 0,
            "warnings": 0,
        }

        titles_by_norm: dict[str, Title] = {}
        for t in Title.objects.all():
            key = _norm_title_name(t.name)
            if key in titles_by_norm:
                stats["warnings"] += 1
                self.stderr.write(
                    self.style.WARNING(
                        f"Duplicate normalized title name {key!r} in DB "
                        f"(ids {titles_by_norm[key].pk} and {t.pk}); using first match."
                    )
                )
            else:
                titles_by_norm[key] = t

        def resolve_title(block: dict, bi: int) -> Title | None:
            tid = block.get("title_id")
            if tid is not None:
                try:
                    pk = int(tid)
                except (TypeError, ValueError):
                    self.stderr.write(
                        self.style.WARNING(
                            f"titles[{bi}]: invalid title_id {tid!r}, skipped block."
                        )
                    )
                    stats["titles_missing"] += 1
                    return None
                t = Title.objects.filter(pk=pk).first()
                if t is None:
                    self.stderr.write(
                        self.style.WARNING(
                            f"titles[{bi}]: no Title with id={pk}, skipped block."
                        )
                    )
                    stats["titles_missing"] += 1
                    return None
                stats["title_blocks_matched"] += 1
                return t

            title_name = (block.get("title") or "").strip()
            if not title_name:
                self.stderr.write(
                    self.style.WARNING(
                        f"titles[{bi}]: missing title and title_id, skipped.")
                )
                stats["titles_missing"] += 1
                return None

            t = Title.objects.filter(name=title_name).first()
            if t is not None:
                stats["title_blocks_matched"] += 1
                return t

            nkey = _norm_title_name(title_name)
            t = titles_by_norm.get(nkey)
            if t is not None:
                stats["title_blocks_matched"] += 1
                return t

            if allow_create_titles:
                t, created = Title.objects.get_or_create(name=title_name)
                stats["titles_created"] += int(created)
                stats["title_blocks_matched"] += 1
                titles_by_norm.setdefault(_norm_title_name(t.name), t)
                return t

            self.stderr.write(
                self.style.WARNING(
                    f"titles[{bi}]: no existing Title for {title_name!r} "
                    f"(add matching title_id or fix name; or use --create-titles). "
                    f"Block skipped."
                )
            )
            stats["titles_missing"] += 1
            return None

        def import_one_attribute(
            title_obj: Title,
            attr: dict,
            row_ref: str,
        ) -> None:
            label = (
                (attr.get("attribute-label") or attr.get("label") or "")
                .strip()[:255]
            )
            if not label:
                self.stderr.write(
                    self.style.WARNING(
                        f"{row_ref}: empty attribute-label, skipped."
                    )
                )
                stats["warnings"] += 1
                return

            typ = (attr.get("type") or "text").strip()
            if typ not in VALID_ATTR_TYPES:
                self.stderr.write(
                    self.style.WARNING(
                        f"{row_ref}: invalid type {typ!r}, using 'text'."
                    )
                )
                typ = "text"
                stats["warnings"] += 1

            required = _coerce_required(attr.get("required", False))

            attr_row, a_created = Attribute.objects.get_or_create(
                title=title_obj,
                label=label,
                defaults={"type": typ, "required": required},
            )
            if a_created:
                stats["attributes_created"] += 1
            else:
                stats["attributes_existing"] += 1
                if attr_row.type != typ or attr_row.required != required:
                    attr_row.type = typ
                    attr_row.required = required
                    attr_row.save(update_fields=["type", "required"])

            opts = attr.get("options")
            if isinstance(opts, list) and opts and typ == "select":
                for o in opts:
                    ol = _option_label(o)
                    if not ol:
                        continue
                    _, o_created = Option.objects.get_or_create(
                        attribute=attr_row,
                        label=ol,
                    )
                    if o_created:
                        stats["options_created"] += 1

        def run_import() -> None:
            titles_blocks = data.get("titles")
            if isinstance(titles_blocks, list) and titles_blocks:
                for bi, block in enumerate(titles_blocks, start=1):
                    if not isinstance(block, dict):
                        stats["warnings"] += 1
                        continue
                    title_obj = resolve_title(block, bi)
                    if title_obj is None:
                        continue
                    attrs = block.get("attributes")
                    if not isinstance(attrs, list):
                        continue
                    for j, attr in enumerate(attrs, start=1):
                        if not isinstance(attr, dict):
                            stats["warnings"] += 1
                            continue
                        import_one_attribute(
                            title_obj,
                            attr,
                            f"titles[{bi}].attributes[{j}]",
                        )
                return

            entries = data.get("entries")
            if not isinstance(entries, list):
                raise CommandError(
                    'JSON must contain a "titles" array or legacy "entries" array.'
                )
            for i, row in enumerate(entries, start=1):
                if not isinstance(row, dict):
                    stats["warnings"] += 1
                    continue
                tid = row.get("title_id")
                title_obj: Title | None = None
                if tid is not None:
                    try:
                        title_obj = Title.objects.filter(pk=int(tid)).first()
                    except (TypeError, ValueError):
                        title_obj = None
                if title_obj is None:
                    t = row.get("title") or {}
                    title_name = (t.get("name") or "").strip()
                    if not title_name:
                        self.stderr.write(
                            self.style.WARNING(
                                f"entries[{i}]: missing title, skipped."
                            )
                        )
                        stats["warnings"] += 1
                        continue
                    title_obj = Title.objects.filter(name=title_name).first()
                    if title_obj is None:
                        title_obj = titles_by_norm.get(
                            _norm_title_name(title_name))
                    if title_obj is None and allow_create_titles:
                        title_obj, _ = Title.objects.get_or_create(
                            name=title_name)
                        stats["titles_created"] += 1
                    if title_obj is None:
                        self.stderr.write(
                            self.style.WARNING(
                                f"entries[{i}]: no Title for {title_name!r}, skipped."
                            )
                        )
                        stats["titles_missing"] += 1
                        continue
                attr_blob = row.get("attribute") or {}
                merged = {
                    "attribute-label": attr_blob.get("label"),
                    "type": attr_blob.get("type"),
                    "required": attr_blob.get("required", False),
                    "options": row.get("options") or [],
                }
                import_one_attribute(title_obj, merged, f"entries[{i}]")

        if dry:
            n = 0
            if isinstance(data.get("titles"), list):
                for b in data["titles"]:
                    if isinstance(b, dict) and isinstance(b.get("attributes"), list):
                        n += len(b["attributes"])
            elif isinstance(data.get("entries"), list):
                n = len(data["entries"])
            self.stdout.write(
                self.style.NOTICE(
                    f"[dry-run] JSON defines {n} attribute row(s) in {json_path.name}"
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    "[dry-run] A real import would create/update Attribute and Option "
                    "only for Title rows that already exist (title_id or matching name), "
                    "unless --create-titles is passed."
                )
            )
            self.stdout.write(
                self.style.NOTICE(
                    f"[dry-run] create_titles={allow_create_titles} (no DB writes)."
                )
            )
            return

        with transaction.atomic():
            run_import()

        self.stdout.write(self.style.SUCCESS(f"Imported from {json_path}"))
        for k, v in stats.items():
            self.stdout.write(f"  {k}: {v}")
