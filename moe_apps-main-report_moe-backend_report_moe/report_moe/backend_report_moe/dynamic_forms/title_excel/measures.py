"""Long-format ("measures") Excel template: one row per indicator.

Mirrors the layout moeds exports its daily reports in — sheet `ملخص` for report
metadata, sheet `المؤشرات` with المؤشر / Metric / القيمة / الوحدة — so a filled
template reads like the report it feeds. The wide layout in `dynamic.py` stays
the default; this one suits `single_record` titles, where each attribute holds
exactly one value per report.

English labels and units come from the measure catalog on Attribute
(`label_en`, `unit_ar`, `unit_en`); run `backfill_measure_catalog` to populate
them from moeds' MetricSpec lists.
"""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from ..excel_utils import norm_text
from ..form_schema import attribute_display_label
from ..models import Title
from .constants import COL_REGION
from .schema import importable_attributes

# Templates are exported in this layout unless the caller asks for another one.
DEFAULT_TEMPLATE_LAYOUT = "measures"

SHEET_SUMMARY = "ملخص"
SHEET_METRICS = "المؤشرات"

# Visible columns match the moeds export exactly. `key` rides along in a hidden
# column so import can match on the stable id rather than a renameable label.
COL_LABEL_AR = "المؤشر"
COL_LABEL_EN = "Metric"
COL_VALUE = "القيمة"
COL_UNIT = "الوحدة"
COL_KEY = "المفتاح"

METRIC_COLUMNS = (COL_LABEL_AR, COL_LABEL_EN, COL_VALUE, COL_UNIT, COL_KEY)

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="7C6B3E")


def _write_header(ws, columns: tuple[str, ...]) -> None:
    for idx, label in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=idx, value=label)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL


def _measure_sort_key(attr):
    return (attr.measure_order or 0, attr.order or 0, attr.id)


class LayoutNotSupported(ValueError):
    """The title cannot be represented in the long layout."""


def _build_measures_workbook(
    title: Title,
    *,
    sub_main=None,
    values_by_key: dict[str, str] | None = None,
) -> Workbook:
    """Build a measures workbook from current Attribute rows (DB SSOT).

    ``values_by_key`` fills the القيمة column when exporting existing data.
    Columns/rows always come from ``importable_attributes`` — never hardcoded metrics.
    """
    if title.entry_mode == "multi_record":
        raise LayoutNotSupported(
            "هذا القالب يقبل عدة سجلات، ولا يمكن تصديره بشكل المؤشرات "
            "(صف واحد لكل مؤشر). استخدم القالب العادي."
        )
    attrs = sorted(importable_attributes(title.id), key=_measure_sort_key)
    filled = values_by_key or {}

    wb = Workbook()

    summary = wb.active
    summary.title = SHEET_SUMMARY
    summary.sheet_view.rightToLeft = True
    # Context, not data: anything the title actually stores — the report date
    # included — is an attribute and belongs in the metrics sheet, listed once.
    # Region is the exception: it resolves the sub-section rather than being stored.
    rows = [
        ("القالب / Title", title.name),
        ("القسم الفرعي / Sub-section", sub_main.name if sub_main else ""),
        (f"{COL_REGION} / Region", ""),
        ("ملاحظات (ع)", ""),
        ("Notes (en)", ""),
    ]
    for r, (label, value) in enumerate(rows, start=1):
        summary.cell(row=r, column=1, value=label).font = Font(bold=True)
        summary.cell(row=r, column=2, value=value)
    summary.column_dimensions["A"].width = 32
    summary.column_dimensions["B"].width = 46

    metrics = wb.create_sheet(SHEET_METRICS)
    metrics.sheet_view.rightToLeft = True
    _write_header(metrics, METRIC_COLUMNS)

    for r, attr in enumerate(attrs, start=2):
        metrics.cell(row=r, column=1, value=attribute_display_label(attr))
        metrics.cell(row=r, column=2, value=attr.label_en or "")
        key = (attr.key or "").strip()
        if key and key in filled:
            metrics.cell(row=r, column=3, value=filled[key])
        metrics.cell(row=r, column=4, value=attr.unit_ar or attr.unit_en or "")
        metrics.cell(row=r, column=5, value=attr.key or "")
        if attr.required:
            metrics.cell(row=r, column=1).font = Font(bold=True)

    for col, width in ((1, 46), (2, 38), (3, 14), (4, 14), (5, 30)):
        metrics.column_dimensions[get_column_letter(col)].width = width
    metrics.column_dimensions[get_column_letter(5)].hidden = True
    metrics.cell(row=1, column=3).alignment = Alignment(horizontal="center")
    metrics.freeze_panes = "A2"
    return wb


def build_measures_template_bytes(
    title: Title, *, sub_main=None
) -> bytes:
    """Blank long-format template for one title (Attribute-driven)."""
    wb = _build_measures_workbook(title, sub_main=sub_main)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_measures_export_bytes(
    title: Title,
    *,
    values_by_key: dict[str, str],
    sub_main=None,
) -> bytes:
    """Filled long-format export from accepted Info values keyed by Attribute.key."""
    wb = _build_measures_workbook(
        title, sub_main=sub_main, values_by_key=values_by_key
    )
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def is_measures_workbook(wb) -> bool:
    """A workbook is in the long layout when it carries the metrics sheet."""
    return SHEET_METRICS in wb.sheetnames


def read_measures_rows(wb, attrs: list) -> tuple[dict[str, str], list[dict]]:
    """Flatten a long-layout workbook into the value dict the wide path expects.

    Returns (values, issues). Values are keyed by attribute label so that
    ``validate_and_collect_attribute_values`` can consume them unchanged.
    Matching prefers the hidden key column and falls back to the Arabic label,
    because the key column is lost when a user re-saves the file as CSV.
    """
    ws = wb[SHEET_METRICS]
    by_key = {a.key: a for a in attrs if a.key}
    by_label = {}
    for a in attrs:
        by_label.setdefault(norm_text(a.label), a)
        by_label.setdefault(norm_text(attribute_display_label(a)), a)

    values: dict[str, str] = {}
    issues: list[dict] = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        cells = list(row) + [None] * (len(METRIC_COLUMNS) - len(row))
        label_ar, _label_en, raw_value, _unit, key = cells[:5]
        attr = by_key.get(str(key).strip()) if key else None
        if attr is None and label_ar:
            attr = by_label.get(norm_text(str(label_ar)))
        if attr is None:
            if label_ar or raw_value not in (None, ""):
                issues.append({
                    "kind": "unknown_column",
                    "column": str(label_ar or key or f"row {idx}"),
                    "message": (
                        "مؤشر غير معروف في هذا القالب: "
                        f"{label_ar or key}"
                    ),
                })
            continue
        if raw_value in (None, ""):
            continue
        values[attr.label] = str(raw_value)

    # The summary sheet carries the region used to resolve the sub-section.
    if SHEET_SUMMARY in wb.sheetnames:
        for row in wb[SHEET_SUMMARY].iter_rows(values_only=True):
            cells = list(row) + [None, None]
            label, value = cells[0], cells[1]
            if label and COL_REGION in str(label) and value:
                values[COL_REGION] = str(value).strip()
                break
    return values, issues
