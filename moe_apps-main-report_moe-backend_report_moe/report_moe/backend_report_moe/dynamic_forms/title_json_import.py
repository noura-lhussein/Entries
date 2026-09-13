"""Import docs/templates/*.json row payloads into Info (same rules as Excel import)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable

from django.db import transaction

from .excel_utils import norm_text
from .location_resolution import build_info_records_from_row
from .models import Info, Title
from .title_excel_constants import (
    COL_MAIN_SECTION,
    COL_REGION,
    COL_SUB_MAIN,
    REGION_HEADER_ALIASES,
)
from .title_excel_dynamic import _empty_result
from .title_excel_exceptions import ImportRowError
from .title_excel_schema import (
    importable_attributes,
    map_headers,
    validate_and_collect_attribute_values,
)
from .title_excel_submain import region_from_row_values, resolve_sub_main_for_import


def _norm_title_name(s: str) -> str:
    import re

    s = s.strip().rstrip(":").rstrip(".")
    s = re.sub(r"\s+", " ", s)
    return s.replace("\u2013", "-").replace("\u2014", "-")


def resolve_title_from_payload(
    data: dict[str, Any],
    *,
    title_id: int | None = None,
) -> Title | None:
    if title_id is not None:
        return Title.objects.filter(pk=title_id).first()

    title_name = (data.get("title") or "").strip()
    if not title_name:
        return None

    exact = Title.objects.filter(name=title_name).first()
    if exact:
        return exact

    nkey = _norm_title_name(title_name)
    for t in Title.objects.all():
        if _norm_title_name(t.name) == nkey:
            return t
    return None


def _row_keys(rows: list[dict[str, Any]]) -> list[str]:
    for row in rows:
        if isinstance(row, dict) and row:
            return list(row.keys())
    return []


def json_row_to_values(
    row: dict[str, Any],
    columns: list[str],
    row_keys: list[str],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for col_label, key in zip(columns, row_keys):
        raw = row.get(key, "") if key else ""
        if raw is None:
            raw = ""
        val = str(raw).strip()
        if col_label == COL_MAIN_SECTION:
            values[COL_MAIN_SECTION] = val
        elif col_label == COL_SUB_MAIN:
            values[COL_SUB_MAIN] = val
        elif col_label in REGION_HEADER_ALIASES:
            if val:
                values[COL_REGION] = val
        else:
            values[col_label] = val

    if COL_REGION not in values:
        reg = region_from_row_values(values)
        if reg:
            values[COL_REGION] = reg
    return values


def import_json_payload(
    *,
    title: Title,
    user,
    data: dict[str, Any],
    dry_run: bool = False,
    log_action: Callable | None = None,
) -> dict[str, Any]:
    """Import rows from a docs/templates JSON object."""
    columns = data.get("columns")
    rows = data.get("rows")
    if not isinstance(columns, list) or not columns:
        return _empty_result(
            errors=[
                {"row": 1, "message": 'JSON must contain a non-empty "columns" array.'}],
        )
    if not isinstance(rows, list):
        return _empty_result(
            errors=[{"row": 1, "message": 'JSON must contain a "rows" array.'}],
        )

    attrs = importable_attributes(title.id)
    if not attrs:
        return _empty_result(
            errors=[
                {
                    "row": 1,
                    "message": "لا توجد حقول قابلة للاستيراد لهذا العنوان",
                }
            ],
        )

    headers = [norm_text(c) for c in columns]
    col_map, validation = map_headers(headers, attrs, title.id)

    if validation["blocking"]:
        return _empty_result(
            errors=[
                {
                    "row": 1,
                    "message": issue["message"],
                }
                for issue in validation["issues"]
                if issue["kind"] == "missing_column"
            ],
            validation=validation,
            dry_run=dry_run,
        )

    row_keys = data.get("row_keys") or _row_keys(rows)
    if len(row_keys) < len(columns):
        return _empty_result(
            errors=[
                {
                    "row": 1,
                    "message": (
                        f"Row keys ({len(row_keys)}) fewer than columns ({len(columns)})."
                    ),
                }
            ],
            validation=validation,
            dry_run=dry_run,
        )

    errors: list[dict[str, Any]] = []
    imported = 0
    skipped = 0
    pending_infos: list[Info] = []
    attrs_by_id = {attr.id: attr for attr in attrs}

    for row_idx, row in enumerate(rows, start=2):
        if not isinstance(row, dict):
            errors.append(
                {"row": row_idx, "message": "صف غير صالح (ليس كائناً)."})
            continue

        values = json_row_to_values(row, columns, row_keys)
        if not any(v for v in values.values() if str(v).strip()):
            skipped += 1
            continue

        try:
            sub_main = resolve_sub_main_for_import(values, user, row_idx)
            row_attrs = validate_and_collect_attribute_values(
                values, attrs, col_map, row_idx
            )
            if not dry_run:
                row_key = uuid.uuid4()
                pending_infos.extend(
                    build_info_records_from_row(
                        row_attrs,
                        attrs_by_id,
                        sub_main=sub_main,
                        user=user,
                        row_key=row_key,
                    )
                )
            imported += 1
        except ImportRowError as exc:
            errors.append({"row": exc.row, "message": exc.message})
        except Exception as exc:
            errors.append({"row": row_idx, "message": str(exc)})

    if dry_run:
        return {
            "imported_rows": imported,
            "skipped_rows": skipped,
            "errors": errors,
            "dry_run": True,
            "validation": validation,
        }

    if errors and imported == 0:
        return {
            "imported_rows": 0,
            "skipped_rows": skipped,
            "errors": errors,
            "validation": validation,
        }

    with transaction.atomic():
        if pending_infos:
            Info.objects.bulk_create(pending_infos)
            if log_action:
                log_action(
                    details={
                        "title_id": title.id,
                        "title_name": title.name,
                        "imported_rows": imported,
                        "info_count": len(pending_infos),
                        "source": "json_template",
                    },
                )

    return {
        "imported_rows": imported,
        "skipped_rows": skipped,
        "errors": errors,
        "validation": validation,
    }


def load_json_file(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def import_json_file(
    *,
    path: Path,
    user,
    title_id: int | None = None,
    dry_run: bool = False,
    log_action: Callable | None = None,
) -> tuple[Title | None, dict[str, Any]]:
    data = load_json_file(path)
    title = resolve_title_from_payload(data, title_id=title_id)
    if title is None:
        name = (data.get("title") or "").strip() or "?"
        return None, _empty_result(
            errors=[
                {
                    "row": 1,
                    "message": f"لم يُعثر على Title مطابق: {name!r}",
                }
            ],
            dry_run=dry_run,
        )
    result = import_json_payload(
        title=title,
        user=user,
        data=data,
        dry_run=dry_run,
        log_action=log_action,
    )
    return title, result
