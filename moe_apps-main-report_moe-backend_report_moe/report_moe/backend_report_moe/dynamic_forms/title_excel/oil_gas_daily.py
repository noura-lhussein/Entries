"""Form Builder Excel for ``oil_gas.national`` — official multi-sheet workbook.

Template/export match ``EXPORT_SHEET_ORDER`` (same shape as
``scripts/oil_gas_daily_report_*.xlsx``). Import uses ``extract_xlsx`` then
writes ``Info`` via attribute keys from the DB (fan-out to pack member titles).
"""

from __future__ import annotations

import tempfile
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Callable

from rest_framework.exceptions import ValidationError

from oil_gas.operational_models import Field, Refinery
from oil_gas.report_export import build_oil_gas_report_sheets
from oil_gas.report_template import (
    EXPORT_SHEET_ORDER,
    build_oil_gas_blank_template_sheets,
)
from oil_gas.xlsx_extract import extract_xlsx, is_official_oil_gas_workbook
from water.template_generator import multisheet_xlsx_response

from ..models import Title
from .exceptions import ImportRowError
from .schema import importable_attributes
from .sector_info_writer import RowGroup, write_sector_info
from .submain import resolve_sub_main_for_import


def _s(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _blocking_result(kind: str, message: str, *, dry_run: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "imported_rows": 0,
        "skipped_rows": 0,
        "errors": [{"row": 1, "message": message}],
        "validation": {
            "blocking": True,
            "expected_columns": [],
            "found_columns": [],
            "missing_columns": [],
            "unknown_columns": [],
            "issues": [{"kind": kind, "column": "", "message": message}],
        },
    }
    if dry_run:
        payload["dry_run"] = True
    return payload


def _norm(value: Any) -> str:
    return " ".join(_s(value).lower().split())


def _field_lookup() -> dict[str, int]:
    by_label: dict[str, int] = {}
    for f in Field.objects.all():
        for label in (f.name_ar, getattr(f, "name_en", "") or "", f.code):
            key = _norm(label)
            if key:
                by_label[key] = f.id
    return by_label


def _refinery_lookup() -> dict[str, int]:
    by_label: dict[str, int] = {}
    for r in Refinery.objects.all():
        for label in (
            r.name_ar,
            r.refinery_name,
            getattr(r, "name_en", "") or "",
            getattr(r, "label_ar", "") or "",
        ):
            key = _norm(label)
            if key:
                by_label[key] = r.id
    return by_label


def _build_groups_from_extract(
    row: dict[str, Any], *, sub_main_id: int
) -> tuple[list[RowGroup], list[dict]]:
    issues: list[dict] = []
    groups: list[RowGroup] = []
    report_date = str(row.get("report_date") or "").strip()
    if not report_date:
        raise ValueError("تعذّر قراءة تاريخ التقرير من الملف.")

    metrics = dict(row.get("metrics") or {})
    metrics["report_date"] = report_date
    national_title = Title.objects.filter(code="oil_gas.national").first()
    allowed_keys = {
        a.key
        for a in (
            importable_attributes(national_title.id) if national_title else []
        )
        if a.key
    }
    national_values = {
        k: _s(v)
        for k, v in metrics.items()
        if _s(v) and (not allowed_keys or k in allowed_keys)
    }
    # Include sub_main_id: (attribute_id, row_key) is globally unique.
    groups.append(
        RowGroup(
            title_code="oil_gas.national",
            entity_type="",
            entity_id=None,
            row_key=uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"og-national-{sub_main_id}-{report_date}",
            ),
            values=national_values,
        )
    )

    field_by = _field_lookup()
    for item in row.get("fields") or []:
        name_ar = _s(item.get("name_ar"))
        name_en = _s(item.get("name_en"))
        field_id = field_by.get(_norm(name_ar)) or field_by.get(_norm(name_en))
        if field_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "oil_gas.field_entity",
                    "message": f"حقل غير معروف في البيانات المرجعية: {name_ar or name_en}",
                }
            )
            continue
        values = {
            "production_date": report_date,
            "crude_oil_bbl": _s(item.get("crude_oil_bbl")),
            "natural_gas_mmscf": _s(item.get("natural_gas_mmscf")),
            "condensate_bbl": _s(item.get("condensate_bbl")),
        }
        if not any(v for k, v in values.items() if k != "production_date"):
            continue
        groups.append(
            RowGroup(
                title_code="oil_gas.field_entity",
                entity_type="oil_field",
                entity_id=field_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"og-field-{sub_main_id}-{report_date}-{field_id}",
                ),
                values=values,
            )
        )

    refinery_by = _refinery_lookup()
    for item in row.get("refineries") or []:
        name_ar = _s(item.get("name_ar"))
        name_en = _s(item.get("name_en"))
        refinery_id = refinery_by.get(
            _norm(name_ar)) or refinery_by.get(_norm(name_en))
        if refinery_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "oil_gas.refinery_entity",
                    "message": f"مصفاة غير معروفة في البيانات المرجعية: {name_ar or name_en}",
                }
            )
            continue
        values = {
            "production_date": report_date,
            "gasoline_ton": _s(item.get("gasoline_ton")),
            "diesel_ton": _s(item.get("diesel_ton")),
            "fuel_oil_ton": _s(item.get("fuel_oil_ton")),
            "lpg_ton": _s(item.get("lpg_ton")),
        }
        if not any(v for k, v in values.items() if k != "production_date"):
            continue
        groups.append(
            RowGroup(
                title_code="oil_gas.refinery_entity",
                entity_type="oil_refinery",
                entity_id=refinery_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"og-refinery-{sub_main_id}-{report_date}-{refinery_id}",
                ),
                values=values,
            )
        )

    return groups, issues


class OilGasDailyExcelHandler:
    """Official multi-sheet oil/gas workbook ↔ Info (attribute keys from DB)."""

    def build_template_bytes(
        self,
        title: Title,
        *,
        sub_main_id: int | None = None,
        layout: str = "measures",
    ) -> bytes:
        sheets = build_oil_gas_blank_template_sheets()
        ordered = {name: sheets[name]
                   for name in EXPORT_SHEET_ORDER if name in sheets}
        return multisheet_xlsx_response(
            "oil_gas_daily_report_template.xlsx", ordered
        ).content

    def build_export_bytes(
        self,
        title: Title,
        *,
        report_date: str,
        sub_main_id: int | None = None,
    ) -> bytes:
        try:
            d = date.fromisoformat(report_date.strip())
        except ValueError as exc:
            raise ValidationError({"report_date": "تاريخ غير صالح."}) from exc
        sheets = build_oil_gas_report_sheets(d)
        if not sheets:
            raise ValidationError(
                {"report_date": "لا توجد بيانات معتمدة لهذا التاريخ."}
            )
        ordered = {name: sheets[name]
                   for name in EXPORT_SHEET_ORDER if name in sheets}
        # Older exports may only have ملخص+المؤشرات — keep whatever is present.
        if not ordered:
            ordered = sheets
        return multisheet_xlsx_response(
            f"oil_gas_daily_report_{report_date}.xlsx", ordered
        ).content

    def import_workbook(
        self,
        *,
        title: Title,
        user,
        file_obj,
        dry_run: bool = False,
        log_action: Callable | None = None,
        sub_main_id: int | None = None,
    ) -> dict[str, Any]:
        suffix = Path(getattr(file_obj, "name", "")
                      or "upload.xlsx").suffix.lower()
        if suffix not in (".xlsx", ".xlsm", ""):
            suffix = ".xlsx"

        with tempfile.NamedTemporaryFile(suffix=suffix or ".xlsx", delete=False) as tmp:
            if hasattr(file_obj, "chunks"):
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
            else:
                data = file_obj.read() if hasattr(file_obj, "read") else file_obj
                if isinstance(data, str):
                    data = data.encode("utf-8")
                tmp.write(data)
            tmp_path = Path(tmp.name)

        try:
            if not is_official_oil_gas_workbook(tmp_path):
                from .dynamic import DynamicTitleExcelHandler

                with tmp_path.open("rb") as fh:
                    return DynamicTitleExcelHandler().import_workbook(
                        title=title,
                        user=user,
                        file_obj=fh,
                        dry_run=dry_run,
                        log_action=log_action,
                        sub_main_id=sub_main_id,
                    )

            try:
                row = extract_xlsx(tmp_path)
            except ValueError as exc:
                return _blocking_result(
                    "wrong_workbook_shape",
                    "هذا العنوان يقبل ملف التقرير اليومي الرسمي للنفط والغاز "
                    f"(ملخص / المؤشرات). ({exc})",
                    dry_run=dry_run,
                )

            try:
                sub_main = resolve_sub_main_for_import(
                    {}, user, 1, sub_main_id=sub_main_id
                )
            except ImportRowError as exc:
                return _blocking_result(
                    "sheet_unreadable",
                    exc.message or "اختر القسم الفرعي.",
                    dry_run=dry_run,
                )

            try:
                groups, extra_issues = _build_groups_from_extract(
                    row, sub_main_id=sub_main.id
                )
            except ValueError as exc:
                return _blocking_result(
                    "sheet_unreadable", str(exc), dry_run=dry_run
                )

            result = write_sector_info(
                groups=groups,
                user=user,
                sub_main=sub_main,
                dry_run=dry_run,
                extra_issues=extra_issues,
            )
            if (
                not dry_run
                and result.get("imported_rows")
                and log_action
                and not result.get("validation", {}).get("blocking")
            ):
                log_action(
                    details={
                        "title_id": title.id,
                        "title_name": title.name,
                        "imported_rows": result["imported_rows"],
                        "layout": "oil_gas_master",
                        "report_date": row.get("report_date"),
                    }
                )
            return result
        finally:
            tmp_path.unlink(missing_ok=True)
