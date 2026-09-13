"""
Migrate legacy moeds reading rows into dynamic_forms.Info (EAV).

Pilot sources (Form Builder titles must already be seeded):
  - daily_production → «تحديث إنتاج الحقول النفطية»
  - dam_storage      → «تحديث تخزين السدود» (requires --dam-id and --year)

Usage:
  # Oil pilot (dry-run then apply)
  python manage.py migrate_legacy_readings_to_info --source daily_production --user 1 --sub-main-id 13
  python manage.py migrate_legacy_readings_to_info --source daily_production --user 1 --sub-main-id 13 --apply

  # Dam sample (one dam + year) or all dams for a year (omit --dam-id)
  python manage.py migrate_legacy_readings_to_info --source dam_storage --dam-id 120 --year 2024 --user 1 --sub-main-id 20
  python manage.py migrate_legacy_readings_to_info --source dam_storage --year 2024 --user 1 --sub-main-id 20 --apply
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from oil_gas.operational_models import DailyProduction
from water.models import DamStorageReading

from dynamic_forms.info_confirmation import ACCEPT
from dynamic_forms.models import Attribute, Info, SubMainSection, Title

TITLE_DAILY_PRODUCTION = "تحديث إنتاج الحقول النفطية"
TITLE_DAM_STORAGE = "تحديث تخزين السدود"

MIGRATION_NOTE_PREFIX = "[legacy-migration]"


@dataclass(frozen=True, slots=True)
class SourceSpec:
    key: str
    title_name: str
    entity_type: str
    entity_attr_type: str
    date_attr_type: str = "date"
    number_attr_type: str = "number"
    notes_attr_type: str = "textarea"


SOURCES: dict[str, SourceSpec] = {
    "daily_production": SourceSpec(
        key="daily_production",
        title_name=TITLE_DAILY_PRODUCTION,
        entity_type="oil_field",
        entity_attr_type="oil_field",
    ),
    "dam_storage": SourceSpec(
        key="dam_storage",
        title_name=TITLE_DAM_STORAGE,
        entity_type="dam",
        entity_attr_type="dam",
    ),
}


@dataclass(frozen=True, slots=True)
class LegacyRow:
    entity_id: int
    reading_date: date
    number_value: str
    notes: str


@dataclass(frozen=True, slots=True)
class TitleAttrs:
    title: Title
    entity: Attribute
    date: Attribute
    number: Attribute
    notes: Attribute | None


class Command(BaseCommand):
    help = (
        "Migrate legacy moeds readings into Info rows "
        "(daily_production | dam_storage). Default is dry-run; pass --apply to write."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            choices=sorted(SOURCES.keys()),
            help="Legacy source table mapping.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist Info rows. Without this flag the command is dry-run only.",
        )
        parser.add_argument(
            "--user",
            type=int,
            required=True,
            help="User id stamped on migrated Info rows.",
        )
        parser.add_argument(
            "--sub-main-id",
            type=int,
            required=True,
            help="Leaf SubMainSection id for migrated rows.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Logical rows per commit batch (default 500).",
        )
        parser.add_argument(
            "--dam-id",
            type=int,
            default=None,
            help="Optional for dam_storage: single Dam master id (omit = all dams).",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Required for dam_storage: calendar year filter.",
        )

    def handle(self, *args, **options):
        source_key: str = options["source"]
        apply: bool = bool(options["apply"])
        user_id: int = options["user"]
        sub_main_id: int = options["sub_main_id"]
        batch_size: int = max(1, int(options["batch_size"]))
        dam_id = options["dam_id"]
        year = options["year"]

        spec = SOURCES[source_key]
        user = self._resolve_user(user_id)
        sub_main = self._resolve_leaf_sub_main(sub_main_id)
        attrs = self._resolve_title_attrs(spec)

        if source_key == "dam_storage":
            if year is None:
                raise CommandError("dam_storage requires --year (optional --dam-id).")
            legacy_rows = self._load_dam_storage(dam_id=dam_id, year=year)
        else:
            legacy_rows = self._load_daily_production()

        self.stdout.write(
            f"Source={source_key} title={attrs.title.id!r} "
            f"legacy_rows={len(legacy_rows)} mode={'APPLY' if apply else 'DRY-RUN'}"
        )

        created = 0
        skipped = 0
        errors: list[str] = []
        pending: list[LegacyRow] = []

        existing_keys = self._existing_keys(
            entity_type=spec.entity_type,
            title_id=attrs.title.id,
            date_attr_id=attrs.date.id,
        )

        for row in legacy_rows:
            key = (int(row.entity_id), row.reading_date.isoformat())
            if key in existing_keys:
                skipped += 1
                continue
            pending.append(row)
            if len(pending) >= batch_size:
                c, e = self._flush_batch(
                    pending,
                    spec=spec,
                    attrs=attrs,
                    user=user,
                    sub_main=sub_main,
                    apply=apply,
                    existing_keys=existing_keys,
                )
                created += c
                errors.extend(e)
                pending.clear()

        if pending:
            c, e = self._flush_batch(
                pending,
                spec=spec,
                attrs=attrs,
                user=user,
                sub_main=sub_main,
                apply=apply,
                existing_keys=existing_keys,
            )
            created += c
            errors.extend(e)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. created_logical_rows={created} skipped={skipped} errors={len(errors)}"
            )
        )
        for msg in errors[:20]:
            self.stdout.write(self.style.ERROR(f"  {msg}"))
        if len(errors) > 20:
            self.stdout.write(self.style.ERROR(f"  ... and {len(errors) - 20} more"))

    def _resolve_user(self, user_id: int):
        User = get_user_model()
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            raise CommandError(f"User id={user_id} not found.")
        return user

    def _resolve_leaf_sub_main(self, sub_main_id: int) -> SubMainSection:
        sub = SubMainSection.objects.filter(pk=sub_main_id).first()
        if sub is None:
            raise CommandError(f"SubMainSection id={sub_main_id} not found.")
        if SubMainSection.objects.filter(parent=sub).exists():
            raise CommandError(
                f"SubMainSection id={sub_main_id} is not a leaf (has children)."
            )
        return sub

    def _resolve_title_attrs(self, spec: SourceSpec) -> TitleAttrs:
        title = Title.objects.filter(name=spec.title_name).first()
        if title is None:
            raise CommandError(
                f"Title not found: {spec.title_name!r}. Run the seed_*_pilot_forms command first."
            )
        by_type: dict[str, list[Attribute]] = {}
        for attr in Attribute.objects.filter(title=title):
            by_type.setdefault(attr.type, []).append(attr)

        def one(attr_type: str) -> Attribute:
            rows = by_type.get(attr_type) or []
            if not rows:
                raise CommandError(
                    f"Title {spec.title_name!r} missing attribute type={attr_type!r}."
                )
            if len(rows) > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"Multiple attributes type={attr_type!r}; using id={rows[0].id}."
                    )
                )
            return rows[0]

        notes_rows = by_type.get(spec.notes_attr_type) or []
        return TitleAttrs(
            title=title,
            entity=one(spec.entity_attr_type),
            date=one(spec.date_attr_type),
            number=one(spec.number_attr_type),
            notes=notes_rows[0] if notes_rows else None,
        )

    def _load_daily_production(self) -> list[LegacyRow]:
        qs = (
            DailyProduction.objects
            .order_by("production_date", "id")
            .iterator(chunk_size=500)
        )
        out: list[LegacyRow] = []
        for row in qs:
            out.append(
                LegacyRow(
                    entity_id=int(row.field_id),
                    reading_date=row.production_date,
                    number_value=self._decimal_str(row.crude_oil_bbl),
                    notes=f"{MIGRATION_NOTE_PREFIX} daily_production",
                )
            )
        return out

    def _load_dam_storage(self, *, dam_id: int | None, year: int) -> list[LegacyRow]:
        qs = DamStorageReading.objects.filter(
            reading_date__year=year
        )
        if dam_id is not None:
            qs = qs.filter(dam_id=dam_id)
        qs = qs.order_by("dam_id", "reading_date", "id").iterator(chunk_size=500)
        out: list[LegacyRow] = []
        for row in qs:
            notes = (row.notes or "").strip()
            if not notes:
                notes = f"{MIGRATION_NOTE_PREFIX} dam_storage"
            out.append(
                LegacyRow(
                    entity_id=int(row.dam_id),
                    reading_date=row.reading_date,
                    number_value=self._decimal_str(row.storage_mcm),
                    notes=notes,
                )
            )
        return out

    def _decimal_str(self, value: Any) -> str:
        if value is None:
            return "0"
        if isinstance(value, Decimal):
            text = format(value, "f")
        else:
            text = str(value).strip()
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text or "0"

    def _existing_keys(
        self,
        *,
        entity_type: str,
        title_id: int,
        date_attr_id: int,
    ) -> set[tuple[int, str]]:
        """
        Keys already present as accepted Info for this title:
        (entity_id, date_iso).
        """
        date_infos = (
            Info.objects.filter(
                attribute_id=date_attr_id,
                attribute__title_id=title_id,
                confirmed=ACCEPT,
                entity_type=entity_type,
                entity_id__isnull=False,
            )
            .exclude(value="")
            .values_list("entity_id", "value")
        )
        keys: set[tuple[int, str]] = set()
        for entity_id, value in date_infos.iterator(chunk_size=2000):
            if entity_id is None:
                continue
            keys.add((int(entity_id), str(value).strip()[:10]))
        return keys

    def _flush_batch(
        self,
        rows: Iterable[LegacyRow],
        *,
        spec: SourceSpec,
        attrs: TitleAttrs,
        user,
        sub_main: SubMainSection,
        apply: bool,
        existing_keys: set[tuple[int, str]],
    ) -> tuple[int, list[str]]:
        errors: list[str] = []
        pending_objs: list[Info] = []
        row_count = 0
        for row in rows:
            key = (int(row.entity_id), row.reading_date.isoformat())
            if key in existing_keys:
                continue
            try:
                pending_objs.extend(
                    self._build_info_objects(row, spec=spec, attrs=attrs, user=user, sub_main=sub_main)
                )
                existing_keys.add(key)
                row_count += 1
            except Exception as exc:  # noqa: BLE001 — collect per-row failures
                errors.append(
                    f"entity_id={row.entity_id} date={row.reading_date}: {exc}"
                )

        if apply and pending_objs:
            # One INSERT per batch instead of one per Info row — the batch's
            # own transaction.atomic() already gives it all-or-nothing
            # semantics, same as the previous per-row-transaction version.
            # ignore_conflicts relies on the (attribute, row_key) unique
            # constraint for idempotency instead of relying purely on the
            # in-memory `existing_keys` pre-check.
            with transaction.atomic():
                Info.objects.bulk_create(pending_objs, batch_size=2000, ignore_conflicts=True)

        return row_count, errors

    def _build_info_objects(
        self,
        row: LegacyRow,
        *,
        spec: SourceSpec,
        attrs: TitleAttrs,
        user,
        sub_main: SubMainSection,
    ) -> list[Info]:
        row_key = uuid.uuid4()
        date_value = row.reading_date.isoformat()
        cells: list[tuple[Attribute, str]] = [
            (attrs.entity, str(row.entity_id)),
            (attrs.date, date_value),
            (attrs.number, row.number_value),
        ]
        if attrs.notes is not None and row.notes:
            cells.append((attrs.notes, row.notes))

        return [
            Info(
                row_key=row_key,
                attribute=attribute,
                sub_main=sub_main,
                user=user,
                value=value,
                is_report_date=attribute.is_report_date,
                confirmed=ACCEPT,
                entity_type=spec.entity_type,
                entity_id=row.entity_id,
                confirm_note=MIGRATION_NOTE_PREFIX,
            )
            for attribute, value in cells
        ]
