"""Header mapping and cell validation for dynamic title Excel."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from ..excel_utils import norm_text
from ..form_schema import attribute_display_label
from ..location_resolution import resolve_location_for_attribute
from ..models import Attribute
from .constants import (
    COL_MAIN_SECTION,
    COL_REGION,
    COL_SUB_MAIN,
    NON_EXCEL_ATTRIBUTE_TYPES,
    REGION_HEADER_ALIASES,
    SECTION_COLUMN_LABELS,
)
from .exceptions import ImportRowError
from .submain import region_from_row_values

TYPE_LABELS_AR = {
    "text": "نص",
    "textarea": "نص متعدد الأسطر",
    "number": "رقم",
    "date": "تاريخ",
    "boolean": "نعم/لا",
    "select": "قائمة",
    "city": "محافظة",
    "district": "منطقة",
    "sub_district": "ناحية",
    "community": "بلدة",
    "image": "صورة",
    "file": "ملف",
}


def importable_attributes(title_id: int) -> list[Attribute]:
    return list(
        Attribute.objects.filter(title_id=title_id)
        .exclude(type__in=NON_EXCEL_ATTRIBUTE_TYPES)
        .prefetch_related("options")
        .order_by("id")
    )


def skipped_attributes(title_id: int) -> list[Attribute]:
    return list(
        Attribute.objects.filter(
            title_id=title_id, type__in=NON_EXCEL_ATTRIBUTE_TYPES
        ).order_by("id")
    )


def _attr_header_aliases(attr: Attribute) -> set[str]:
    """Headers accepted for an attribute: Arabic display, DB label, and key."""
    aliases = {
        norm_text(attribute_display_label(attr)),
        norm_text(attr.label),
    }
    key = (attr.key or "").strip()
    if key:
        aliases.add(norm_text(key))
    return {a for a in aliases if a}


def template_column_labels(
    attrs: list[Attribute], *, include_section_columns: bool = True
) -> list[str]:
    """Build Excel header row.

    When ``include_section_columns`` is False (UI already chose main/sub),
    only the region column is kept from the fixed section headers.
    """
    if include_section_columns:
        labels = list(SECTION_COLUMN_LABELS)
    else:
        labels = [COL_REGION]
    seen = set(REGION_HEADER_ALIASES)
    for attr in attrs:
        label = norm_text(attribute_display_label(attr))
        if label in seen:
            continue
        labels.append(label)
        seen.add(label)
    return labels


def region_feeds_required_attribute(attrs: list[Attribute]) -> bool:
    """True when the region column supplies a required attribute's value.

    Attributes labelled with a region alias are not given their own column;
    ``validate_and_collect_attribute_values`` feeds them from the region column
    instead. When such an attribute is required the column stays mandatory even
    if the sub-section is already known.
    """
    for attr in attrs:
        if not attr.required:
            continue
        if (
            norm_text(attr.label) in REGION_HEADER_ALIASES
            or norm_text(attribute_display_label(attr)) in REGION_HEADER_ALIASES
        ):
            return True
    return False


def map_headers(
    headers: list[str],
    attrs: list[Attribute],
    title_id: int,
    *,
    require_section_columns: bool = True,
) -> tuple[dict[str, int], dict[str, Any]]:
    """
    Map header labels to column indices and build validation metadata.
    Returns (col_map, validation_payload).
    """
    col_map: dict[str, int] = {}
    attr_by_norm: dict[str, Attribute] = {}
    for a in attrs:
        for alias in _attr_header_aliases(a):
            attr_by_norm.setdefault(alias, a)
    unknown_columns: list[str] = []
    region_mapped = False
    mapped_attr_ids: set[int] = set()

    for idx, raw in enumerate(headers):
        h = norm_text(raw)
        if not h:
            continue
        if h == COL_MAIN_SECTION and COL_MAIN_SECTION not in col_map:
            col_map[COL_MAIN_SECTION] = idx
            continue
        if h == COL_SUB_MAIN and COL_SUB_MAIN not in col_map:
            col_map[COL_SUB_MAIN] = idx
            continue
        if h in REGION_HEADER_ALIASES:
            if not region_mapped:
                col_map[COL_REGION] = idx
                region_mapped = True
            continue
        attr = attr_by_norm.get(h)
        if attr:
            col_map[attr.label] = idx
            mapped_attr_ids.add(attr.id)
        else:
            # Legacy templates may still include section columns when not required.
            if h in (COL_MAIN_SECTION, COL_SUB_MAIN):
                continue
            unknown_columns.append(h)

    expected = template_column_labels(
        attrs, include_section_columns=require_section_columns
    )
    missing_columns: list[str] = []
    # The region column identifies the sub-section. Once the UI has picked one,
    # it is only still mandatory when a required attribute reads its value.
    region_required = require_section_columns or region_feeds_required_attribute(
        attrs
    )
    for label in expected:
        if label == COL_REGION:
            if region_required and COL_REGION not in col_map:
                missing_columns.append(label)
            continue
        if label in (COL_MAIN_SECTION, COL_SUB_MAIN):
            if require_section_columns and label not in col_map:
                missing_columns.append(label)
            continue
        attr = attr_by_norm.get(label)
        if attr and attr.required and attr.id not in mapped_attr_ids:
            missing_columns.append(label)

    skipped = [
        {
            "column": attribute_display_label(a),
            "kind": "skipped_attribute",
            "message": f"نوع الحقل ({TYPE_LABELS_AR.get(a.type, a.type)}) "
            "لا يُستورد عبر Excel",
        }
        for a in skipped_attributes(title_id)
    ]

    issues: list[dict[str, str]] = []
    for col in missing_columns:
        issues.append(
            {
                "kind": "missing_column",
                "column": col,
                "message": f"عمود مطلوب غير موجود في الملف: {col}",
            }
        )
    for col in unknown_columns:
        issues.append(
            {
                "kind": "unknown_column",
                "column": col,
                "message": f"عمود غير معروف (غير مرتبط بحقول العنوان): {col}",
            }
        )
    issues.extend(skipped)

    blocking = bool(missing_columns)
    validation = {
        "blocking": blocking,
        "expected_columns": expected,
        "found_columns": [norm_text(h) for h in headers if norm_text(h)],
        "missing_columns": missing_columns,
        "unknown_columns": unknown_columns,
        "issues": issues,
    }
    return col_map, validation


def row_values_from_cells(
    col_map: dict[str, int], row_cells, cell_value_fn
) -> dict[str, str]:
    values: dict[str, str] = {}
    for key, idx in col_map.items():
        values[key] = (
            cell_value_fn(row_cells[idx]) if idx < len(row_cells) else ""
        )
    if COL_REGION not in values:
        reg = region_from_row_values(values)
        if reg:
            values[COL_REGION] = reg
    return values


def validate_and_collect_attribute_values(
    values: dict[str, str],
    attrs: list[Attribute],
    col_map: dict[str, int],
    row: int,
) -> list[tuple[int, str]]:
    region = region_from_row_values(values)
    result: list[tuple[int, str]] = []

    for attr in attrs:
        label = attr.label
        display = attribute_display_label(attr)
        if norm_text(label) in REGION_HEADER_ALIASES or norm_text(display) in REGION_HEADER_ALIASES:
            raw = region
        else:
            raw = values.get(label, "")

        if attr.required and not raw:
            raise ImportRowError(row, f"الحقل مطلوب: {display}")

        if not raw:
            continue

        validated = validate_cell_value(attr, raw, row)
        result.append((attr.id, validated))

    if not result:
        raise ImportRowError(row, "لا توجد قيم للاستيراد في هذا الصف")

    return result


def validate_cell_value(attr: Attribute, raw: str, row: int) -> str:
    atype = attr.type
    display = attribute_display_label(attr)
    if atype == "number":
        try:
            float(str(raw).replace(",", ""))
        except ValueError:
            raise ImportRowError(
                row, f"{display}: يجب أن تكون القيمة رقماً")
        return str(raw).replace(",", "")

    if atype == "date":
        parsed = _parse_date(raw)
        if not parsed:
            raise ImportRowError(
                row, f"{display}: تاريخ غير صالح ({raw})"
            )
        return parsed

    if atype == "boolean":
        normalized = _normalize_boolean(raw)
        if normalized is None:
            raise ImportRowError(
                row,
                f"{display}: استخدم نعم/لا أو true/false",
            )
        return normalized

    if atype == "select":
        options = {norm_text(o.label): o.label for o in attr.options.all()}
        key = norm_text(raw)
        if key not in options:
            opts_preview = "، ".join(list(options.values())[:8])
            raise ImportRowError(
                row,
                f"{display}: قيمة غير موجودة في القائمة"
                + (f" ({opts_preview})" if opts_preview else ""),
            )
        return options[key]

    if atype in ("city", "district", "sub_district", "community"):
        display_loc, loc = resolve_location_for_attribute(atype, raw)
        fk_field = {
            "city": "loc_governorate_id",
            "district": "loc_district_id",
            "sub_district": "loc_subdistrict_id",
            "community": "loc_community_id",
        }[atype]
        if not loc.get(fk_field):
            raise ImportRowError(row, f"{display}: موقع غير معروف: {raw}")
        return display_loc

    return raw


_validate_cell_value = validate_cell_value


def _parse_date(raw: object) -> str | None:
    # A cell formatted as a date in Excel arrives as datetime, and stringifying it
    # yields "2026-08-25 00:00:00" -- which matches none of the formats below.
    # Take the date off the object before falling back to text parsing.
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    s = norm_text(raw)
    if not s:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        # Same value after it has already been flattened to text somewhere upstream.
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    if re.fullmatch(r"\d{5}(\.\d+)?", s):
        try:
            from openpyxl.utils.datetime import from_excel

            dt = from_excel(float(s))
            if isinstance(dt, datetime):
                return dt.date().isoformat()
            if isinstance(dt, date):
                return dt.isoformat()
        except (ValueError, TypeError):
            pass
    return None


def _normalize_boolean(raw: str) -> str | None:
    s = norm_text(raw).lower()
    if s in ("1", "true", "yes", "y", "نعم", "صح", "صحيح"):
        return "true"
    if s in ("0", "false", "no", "n", "لا", "خطأ"):
        return "false"
    return None
