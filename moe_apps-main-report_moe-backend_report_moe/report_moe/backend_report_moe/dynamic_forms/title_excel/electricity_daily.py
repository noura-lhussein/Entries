"""Form Builder Excel for ``electricity.national`` — official 10-sheet workbook.

Template/export match ``EXPORT_SHEET_ORDER`` (same shape as
``docs/electricity_daily_report_*.xlsx``). Import uses ``extract_xlsx`` then
writes ``Info`` via attribute keys from the DB (fan-out to pack member titles).
"""

from __future__ import annotations

import tempfile
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Callable

from openpyxl import load_workbook
from rest_framework.exceptions import ValidationError

from electricity.report_template import EXPORT_SHEET_ORDER, SHEET_REPORT_INFO, national_scalar_metrics
from electricity.report_template_import import build_electricity_blank_template_sheets
from electricity.report_export import build_electricity_report_sheets_from_source
from electricity.xlsx_extract import extract_xlsx
from master_data.models import (
    FuelTankStation,
    HydroDam,
    LoadGovernorate,
    PowerPlant,
)
from water.template_generator import multisheet_xlsx_response

from ..models import Title
from .exceptions import ImportRowError
from .sector_info_writer import RowGroup, write_sector_info
from .sector_packs import ELECTRICITY_DAILY_PACK
from .submain import resolve_sub_main_for_import


def _s(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


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


def _is_official_workbook(path: Path) -> bool:
    wb = load_workbook(path, read_only=True, data_only=True)
    names = set(wb.sheetnames)
    wb.close()
    return SHEET_REPORT_INFO in names or "وضع مجموعات التوليد" in names


def _build_groups_from_extract(row: dict[str, Any]) -> tuple[list[RowGroup], list[dict]]:
    """Map extract_xlsx dict → RowGroups; unknown entities → non-blocking issues."""
    issues: list[dict] = []
    groups: list[RowGroup] = []
    report_date = str(row.get("report_date") or "").strip()
    if not report_date:
        raise ValueError("تعذّر قراءة تاريخ التقرير من الملف.")

    plant_by_code = {p.code: p.id for p in PowerPlant.objects.all()}
    dam_by_code = {d.code: d.id for d in HydroDam.objects.all()}
    gov_by_code = {g.code: g.id for g in LoadGovernorate.objects.all()}
    tank_by_code = {t.code: t.id for t in FuelTankStation.objects.all()}

    # ── national ──────────────────────────────────────────────────────────
    national_vals: dict[str, str] = {"report_date": report_date}
    for key, value in national_scalar_metrics(row).items():
        if value is not None:
            national_vals[key] = _s(value)
    groups.append(
        RowGroup(
            title_code="electricity.national",
            entity_type="",
            entity_id=None,
            row_key=uuid.uuid5(uuid.NAMESPACE_URL,
                               f"el-national-{report_date}"),
            values=national_vals,
        )
    )

    # ── governorate loads ─────────────────────────────────────────────────
    for item in row.get("governorate_loads") or []:
        code = item.get("governorate_code") or ""
        gov_id = gov_by_code.get(code)
        if gov_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "electricity.governorate_load_entity",
                    "message": f"محافظة غير معروفة في البيانات المرجعية: {code}",
                }
            )
            continue
        groups.append(
            RowGroup(
                title_code="electricity.governorate_load_entity",
                entity_type="load_governorate",
                entity_id=gov_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-gov-{report_date}-{code}"
                ),
                values={
                    "governorate": str(gov_id),
                    "report_date": report_date,
                    "consumed_mw": _s(item.get("consumed_mw")),
                    "allocated_mw": _s(item.get("allocated_mw")),
                },
            )
        )

    # ── hydro dams ────────────────────────────────────────────────────────
    for item in row.get("hydro_readings") or []:
        code = item.get("dam_code") or ""
        dam_id = dam_by_code.get(code)
        if dam_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "electricity.hydro_dam_entity",
                    "message": f"سد غير معروف في البيانات المرجعية: {code}",
                }
            )
            continue
        groups.append(
            RowGroup(
                title_code="electricity.hydro_dam_entity",
                entity_type="hydro_dam",
                entity_id=dam_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-hydro-{report_date}-{code}"
                ),
                values={
                    "dam": str(dam_id),
                    "report_date": report_date,
                    "front_level_m": _s(item.get("front_level_m")),
                    "back_level_m": _s(item.get("back_level_m")),
                    "generation_mwh": _s(item.get("generation_mwh")),
                    "outflow_m3s": _s(item.get("outflow_m3s")),
                    "inflow_m3s": _s(item.get("inflow_m3s")),
                    "expected_m3s": _s(item.get("expected_m3s")),
                },
            )
        )

    # ── generation units ──────────────────────────────────────────────────
    for item in row.get("generation_unit_readings") or []:
        code = item.get("plant_code") or ""
        plant_id = plant_by_code.get(code)
        if plant_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "electricity.unit_entity",
                    "message": f"محطة غير معروفة في البيانات المرجعية: {code}",
                }
            )
            continue
        unit_code = item.get("unit_code") or ""
        groups.append(
            RowGroup(
                title_code="electricity.unit_entity",
                entity_type="power_plant",
                entity_id=plant_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"el-unit-{report_date}-{code}-{unit_code}",
                ),
                values={
                    "plant": str(plant_id),
                    "report_date": report_date,
                    "unit_code": _s(unit_code),
                    "available_mw": _s(item.get("available_mw")),
                    "generation_mwh": _s(item.get("generation_mwh_24h")),
                    "status": _s(item.get("status")),
                },
            )
        )

    # ── fuel tanks ────────────────────────────────────────────────────────
    for item in row.get("fuel_tank_readings") or []:
        code = item.get("station_code") or item.get("tank_code") or ""
        tank_id = tank_by_code.get(code)
        if tank_id is None:
            issues.append(
                {
                    "kind": "entity_unmatched",
                    "column": "electricity.fuel_tank_entity",
                    "message": f"خزان غير معروف في البيانات المرجعية: {code}",
                }
            )
            continue
        groups.append(
            RowGroup(
                title_code="electricity.fuel_tank_entity",
                entity_type="fuel_tank_station",
                entity_id=tank_id,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-fuel-{report_date}-{code}"
                ),
                values={
                    "station": str(tank_id),
                    "reading_date": report_date,
                    "current_stock_tons": _s(
                        item.get("current_tons") or item.get(
                            "current_stock_tons")
                    ),
                },
            )
        )

    # ── generation incidents ──────────────────────────────────────────────
    for i, item in enumerate(row.get("generation_incidents") or []):
        desc = (item.get("description_ar") or "").strip()
        if not desc:
            continue
        groups.append(
            RowGroup(
                title_code="electricity.generation_incident",
                entity_type="",
                entity_id=None,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-incg-{report_date}-{i}"
                ),
                values={
                    "report_date": report_date,
                    "event_time": _s(item.get("event_time")),
                    "description_ar": desc,
                    "description_en": _s(item.get("description_en")),
                },
            )
        )

    # ── grid incidents ────────────────────────────────────────────────────
    for i, item in enumerate(row.get("grid_incidents") or []):
        line = (item.get("line_name") or "").strip()
        action = (item.get("action_ar") or "").strip()
        if not line and not action:
            continue
        groups.append(
            RowGroup(
                title_code="electricity.grid_incident",
                entity_type="",
                entity_id=None,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-incl-{report_date}-{i}"
                ),
                values={
                    "report_date": report_date,
                    "line_name": line or action,
                    "action_ar": action or line,
                    "action_en": _s(item.get("action_en")),
                    "voltage_kv": _s(item.get("voltage_kv")),
                },
            )
        )

    # ── daily notes ───────────────────────────────────────────────────────
    notes_vals = {
        "report_date": report_date,
        "maintenance_groups": _s(row.get("maintenance_groups_ar")),
        "notes_ar": _s(row.get("notes_ar")),
        "notes_en": _s(row.get("notes_en")),
        "peak_generation_time": _s(row.get("peak_generation_time")),
        "reference_hour": _s(row.get("reference_hour")),
    }
    if any(v for k, v in notes_vals.items() if k != "report_date"):
        groups.append(
            RowGroup(
                title_code="electricity.daily_notes",
                entity_type="",
                entity_id=None,
                row_key=uuid.uuid5(
                    uuid.NAMESPACE_URL, f"el-notes-{report_date}"
                ),
                values=notes_vals,
            )
        )

    return groups, issues


class ElectricityDailyExcelHandler:
    """Official multi-sheet electricity workbook ↔ Info (attribute keys from DB)."""

    def build_template_bytes(
        self,
        title: Title,
        *,
        sub_main_id: int | None = None,
        layout: str = "measures",
    ) -> bytes:
        sheets = build_electricity_blank_template_sheets()
        # Preserve EXPORT_SHEET_ORDER (blank builder already uses it via from_source).
        ordered = {name: sheets[name]
                   for name in EXPORT_SHEET_ORDER if name in sheets}
        return multisheet_xlsx_response(
            "electricity_daily_report_template.xlsx", ordered
        ).content

    def build_export_bytes(
        self,
        title: Title,
        *,
        report_date: str,
        sub_main_id: int | None = None,
    ) -> bytes:
        from electricity.info_dashboard import build_info_report_detail_payload

        try:
            d = date.fromisoformat(report_date.strip())
        except ValueError as exc:
            raise ValidationError({"report_date": "تاريخ غير صالح."}) from exc
        payload = build_info_report_detail_payload(d)
        if not payload:
            raise ValidationError(
                {"report_date": "لا توجد بيانات معتمدة لهذا التاريخ."}
            )
        sheets = build_electricity_report_sheets_from_source(payload)
        return multisheet_xlsx_response(
            f"electricity_daily_report_{report_date}.xlsx", sheets
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
        # Prefer official multi-sheet; fall back to measures layout for this title.
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
            if not _is_official_workbook(tmp_path):
                # Measures / other layouts — reuse dynamic handler behaviour.
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
                    "هذا العنوان يقبل ملف تقرير الكهرباء اليومي الرسمي فقط "
                    f"(بأوراقه العشر). ({exc})",
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
                groups, extra_issues = _build_groups_from_extract(row)
            except ValueError as exc:
                return _blocking_result(
                    "sheet_unreadable", str(exc), dry_run=dry_run
                )

            # Ensure pack root title code is used even if Title.code drifted.
            if title.code and title.code != ELECTRICITY_DAILY_PACK["root"]:
                pass

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
                        "layout": "electricity_master",
                        "report_date": row.get("report_date"),
                    }
                )
            return result
        finally:
            tmp_path.unlink(missing_ok=True)
