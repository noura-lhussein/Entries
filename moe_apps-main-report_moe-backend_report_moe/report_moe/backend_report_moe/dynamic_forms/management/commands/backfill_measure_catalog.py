"""Backfill the measure catalog on Attribute from moeds' hand-written MetricSpec lists.

moeds keeps English labels, units and KPI ordering in `*/metric_catalog.py` as
frozen dataclasses. The same information belongs on Attribute (see the "Measure
catalog" block in dynamic_forms/models.py) so a dashboard measure can be added
without touching moeds code. This command moves it across, matching on `key`.

Only blank fields are written: a unit typed by a human here always wins over the
one in moeds' list. Nothing is written at all without --apply.

    python manage.py backfill_measure_catalog                 # preview
    python manage.py backfill_measure_catalog --apply
"""

from __future__ import annotations

import ast
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from dynamic_forms.models import Attribute

# MetricSpec(key, label_en, label_ar, unit, category, kpi_order, kpi_status_rule)
_SPEC_FIELDS = (
    "key",
    "label_en",
    "label_ar",
    "unit",
    "category",
    "kpi_order",
    "kpi_status_rule",
)

# Attribute field <- MetricSpec field. label_ar/category are deliberately absent:
# the Arabic label is owned here, and category has no counterpart.
# unit_ar is rendered next to the input in the Arabic data-entry screen, so it
# must stay Arabic; moeds' symbols (MWh, t/d) belong in unit_en. Only unit_en is
# ever overwritten -- form_schema.UNIT_AR_FALLBACK is the source for Arabic units.
_UNIT_FIELDS = frozenset({"unit_en"})
_INT_FIELDS = frozenset({"measure_order"})

_FIELD_MAP = {
    "label_en": "label_en",
    "unit_en": "unit",
    "measure_order": "kpi_order",
    "measure_status_rule": "kpi_status_rule",
}

DEFAULT_MOEDS_PATH = Path("../../moeds/moe-backend")


def _parse_specs(path: Path) -> dict[str, dict]:
    """Read MetricSpec(...) calls out of a catalog module without importing it.

    moeds is a separate project and is not installed here, so the file is parsed
    with `ast` rather than executed.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    specs: dict[str, dict] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name != "MetricSpec":
            continue
        spec: dict = {}
        for idx, arg in enumerate(node.args):
            if idx < len(_SPEC_FIELDS) and isinstance(arg, ast.Constant):
                spec[_SPEC_FIELDS[idx]] = arg.value
        for kw in node.keywords:
            if kw.arg in _SPEC_FIELDS and isinstance(kw.value, ast.Constant):
                spec[kw.arg] = kw.value.value
        key = spec.get("key")
        if key:
            specs[key] = spec
    return specs


class Command(BaseCommand):
    help = "Copy English labels/units from moeds metric catalogs onto Attribute."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write the changes. Without it the command only reports.",
        )
        parser.add_argument(
            "--moeds-path",
            default=str(DEFAULT_MOEDS_PATH),
            help=f"Path to moeds/moe-backend (default: {DEFAULT_MOEDS_PATH}).",
        )
        parser.add_argument(
            "--set-measure",
            action="store_true",
            help=(
                "Also set is_measure=True on matched attributes. Off by default: "
                "it makes moeds render the value as a dashboard KPI."
            ),
        )
        parser.add_argument(
            "--overwrite-units",
            action="store_true",
            help=(
                "Let moeds' symbols replace the English unit already stored. "
                "unit_ar is never written -- it is what the Arabic UI displays."
            ),
        )

    def handle(self, *args, **opts):
        root = Path(opts["moeds_path"])
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
        catalogs = sorted(root.glob("*/metric_catalog.py"))
        if not catalogs:
            raise CommandError(
                f"No */metric_catalog.py under {root}. Pass --moeds-path."
            )

        specs: dict[str, dict] = {}
        for path in catalogs:
            found = _parse_specs(path)
            specs.update(found)
            self.stdout.write(f"  {path.parent.name}/metric_catalog.py: {len(found)} specs")
        self.stdout.write(f"catalog keys: {len(specs)}\n")

        attrs = list(Attribute.objects.exclude(key="").filter(key__in=specs.keys()))
        if not attrs:
            self.stdout.write(self.style.WARNING("No attribute keys matched."))
            return

        overwrite_units = opts["overwrite_units"]
        planned: list[tuple[Attribute, dict]] = []
        replaced: list[tuple[str, str, str]] = []
        skipped_kept = 0
        for attr in attrs:
            spec = specs[attr.key]
            changes: dict[str, object] = {}
            for attr_field, spec_field in _FIELD_MAP.items():
                new = spec.get(spec_field)
                current = getattr(attr, attr_field)
                if attr_field in _INT_FIELDS:
                    if not isinstance(new, int):
                        continue
                    # measure_order ships as 1 for every attribute, so "1" reads
                    # as unset rather than as a deliberate first position.
                    if current not in (None, 0, 1) and current != new:
                        skipped_kept += 1
                        continue
                else:
                    new = (new or "").strip()
                    current = (current or "").strip()
                    if not new or current == new:
                        continue
                    if current:
                        if not (overwrite_units and attr_field in _UNIT_FIELDS):
                            skipped_kept += 1
                            continue
                        replaced.append((attr.key, current, new))
                if current == new:
                    continue
                changes[attr_field] = new
            if opts["set_measure"] and not attr.is_measure:
                changes["is_measure"] = True
            if changes:
                planned.append((attr, changes))

        for attr, changes in planned:
            summary = ", ".join(f"{f}={v!r}" for f, v in changes.items())
            self.stdout.write(f"  [{attr.key}] {attr.label[:34]} -> {summary}")

        self.stdout.write("")
        self.stdout.write(f"matched attributes : {len(attrs)}")
        self.stdout.write(f"would change       : {len(planned)}")
        self.stdout.write(f"kept (already set) : {skipped_kept}")
        if replaced:
            self.stdout.write(f"units replaced     : {len(replaced)}")
            for key, old, new in replaced[:15]:
                self.stdout.write(f"    {key}: {old!r} -> {new!r}")

        if not opts["apply"]:
            self.stdout.write(self.style.WARNING("\nPreview only — re-run with --apply to write."))
            return

        fields = sorted({f for _, ch in planned for f in ch})
        with transaction.atomic():
            for attr, changes in planned:
                for field, value in changes.items():
                    setattr(attr, field, value)
            Attribute.objects.bulk_update(
                [a for a, _ in planned], fields, batch_size=200
            )
        self.stdout.write(self.style.SUCCESS(f"\nUpdated {len(planned)} attributes."))
