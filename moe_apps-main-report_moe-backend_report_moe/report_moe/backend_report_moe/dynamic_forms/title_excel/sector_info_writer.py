"""Attribute-driven Info writer for Form Builder Excel import.

Columns/fields always come from ``importable_attributes`` — never from hardcoded
metric lists. Callers supply ``RowGroup.values`` keyed by ``Attribute.key``.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from ..duplicate_date import check_submit_duplicate_date
from ..entity_registry import is_entity_attribute
from ..form_schema import attribute_display_label
from ..location_resolution import build_info_records_from_row
from ..models import Info, Title
from .exceptions import ImportRowError
from .schema import importable_attributes, validate_cell_value

MSG_DATE_EXISTS = "يوجد تقرير غير مؤكد لهذا التاريخ — سيُستبدل."
MSG_DATE_CONFIRMED = "هذا التقرير موجود ومؤكد مسبقاً لهذا التاريخ."


@dataclass
class RowGroup:
    title_code: str
    entity_type: str  # "" for national / incidents / notes
    entity_id: int | None
    row_key: uuid.UUID
    values: dict[str, str]  # Attribute.key -> raw string value


def _empty_contract(
    *,
    imported_rows: int = 0,
    skipped_rows: int = 0,
    errors: list[dict] | None = None,
    issues: list[dict] | None = None,
    blocking: bool = False,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "imported_rows": imported_rows,
        "skipped_rows": skipped_rows,
        "errors": errors or [],
        "validation": {
            "blocking": blocking,
            "expected_columns": [],
            "found_columns": [],
            "missing_columns": [],
            "unknown_columns": [],
            "issues": issues or [],
        },
    }
    if dry_run is not None:
        payload["dry_run"] = dry_run
    return payload


def _archive_row_key(row_key: uuid.UUID | str, *, reason: str) -> None:
    """Archive a logical row and free its ``row_key`` for a deterministic re-import."""
    now = timezone.now()
    retired = uuid.uuid4()
    Info.objects.filter(row_key=row_key, archived=False).update(
        archived=True,
        archived_at=now,
        archive_reason=reason,
        row_key=retired,
    )


def _archive_incident_rows_for_date(
    *,
    title: Title,
    sub_main_id: int,
    report_date: str,
) -> None:
    """Titles without is_report_date uniqueness still carry a report_date value."""
    date_attr_ids = list(
        title.attributes.filter(key="report_date").values_list("id", flat=True)
    )
    if not date_attr_ids:
        return
    prior_keys = list(
        Info.objects.filter(
            attribute_id__in=date_attr_ids,
            sub_main_id=sub_main_id,
            archived=False,
            confirmed__in=(
                Info.ConfirmStatus.WAITING,
                Info.ConfirmStatus.ACCEPT,
            ),
            value=report_date,
        )
        .exclude(row_key__isnull=True)
        .values_list("row_key", flat=True)
        .distinct()
    )
    for rk in prior_keys:
        _archive_row_key(rk, reason="replaced by re-import")


def write_sector_info(
    *,
    groups: list[RowGroup],
    user,
    sub_main,
    dry_run: bool,
    extra_issues: list[dict] | None = None,
) -> dict[str, Any]:
    """Validate and optionally persist RowGroups; return the frontend contract dict."""
    issues: list[dict] = list(extra_issues or [])
    errors: list[dict] = []
    blocking = False
    skipped_rows = 0
    prepared: list[tuple[RowGroup, Title,
                         list[tuple[int, str]], uuid.UUID | None]] = []
    # (group, title, row_attrs, existing_row_key_to_archive)

    titles_by_code: dict[str, Title] = {}
    for code in {g.title_code for g in groups}:
        try:
            titles_by_code[code] = Title.objects.get(code=code)
        except Title.DoesNotExist:
            issues.append(
                {
                    "kind": "wrong_workbook_shape",
                    "column": code,
                    "message": f"عنوان غير موجود في النظام: {code}",
                }
            )
            blocking = True

    if blocking:
        for issue in issues:
            if issue.get("kind") == "wrong_workbook_shape":
                errors.append({"row": 1, "message": issue["message"]})
        return _empty_contract(
            errors=errors,
            issues=issues,
            blocking=True,
            dry_run=True if dry_run else None,
        )

    for group in groups:
        title = titles_by_code[group.title_code]
        attrs = importable_attributes(title.id)
        attrs_by_key = {a.key: a for a in attrs if a.key}

        unknown = [k for k in group.values if k and k not in attrs_by_key]
        for k in unknown:
            issues.append(
                {
                    "kind": "unknown_column",
                    "column": k,
                    "message": f"مؤشر غير معروف في هذا القالب: {k}",
                }
            )

        # Inject entity PK into the entity-typed attribute when provided.
        values = dict(group.values)
        if group.entity_id is not None:
            for attr in attrs:
                if is_entity_attribute(attr.type):
                    values[attr.key] = str(group.entity_id)
                    break

        row_attrs: list[tuple[int, str]] = []
        incomplete = False
        row_no = 1
        try:
            for attr in attrs:
                key = (attr.key or "").strip()
                if not key:
                    continue
                raw = values.get(key, "")
                if attr.required and not str(raw).strip():
                    display = attribute_display_label(attr)
                    issues.append(
                        {
                            "kind": "entity_row_incomplete",
                            "column": group.title_code,
                            "message": f"صف ناقص للحقل المطلوب: {display}",
                        }
                    )
                    incomplete = True
                    break
                if not str(raw).strip():
                    continue
                validated = validate_cell_value(attr, str(raw), row_no)
                row_attrs.append((attr.id, validated))
        except ImportRowError as exc:
            issues.append(
                {
                    "kind": "entity_row_incomplete",
                    "column": group.title_code,
                    "message": exc.message,
                }
            )
            incomplete = True

        if incomplete:
            skipped_rows += 1
            continue

        if not row_attrs:
            skipped_rows += 1
            continue

        has_report_date_flag = any(a.is_report_date for a in attrs)
        existing_key: uuid.UUID | None = None

        if has_report_date_flag:
            items = [{"id": aid, "value": v} for aid, v in row_attrs]
            conflict = check_submit_duplicate_date(
                title_id=title.id,
                sub_main_id=sub_main.id,
                items=items,
            )
            if conflict and conflict.get("confirmed") == Info.ConfirmStatus.ACCEPT:
                issues.append(
                    {
                        "kind": "report_date_confirmed",
                        "column": group.title_code,
                        "message": MSG_DATE_CONFIRMED,
                    }
                )
                blocking = True
                continue
            if conflict and conflict.get("confirmed") == Info.ConfirmStatus.WAITING:
                issues.append(
                    {
                        "kind": "report_date_exists",
                        "column": group.title_code,
                        "message": MSG_DATE_EXISTS,
                    }
                )
                rk = conflict.get("existing_row_key")
                if rk:
                    existing_key = uuid.UUID(str(rk))

        prepared.append((group, title, row_attrs, existing_key))

    if blocking:
        for issue in issues:
            if issue.get("kind") in (
                "report_date_confirmed",
                "wrong_workbook_shape",
                "sheet_unreadable",
            ):
                errors.append({"row": 1, "message": issue["message"]})
        return _empty_contract(
            imported_rows=0,
            skipped_rows=skipped_rows,
            errors=errors,
            issues=issues,
            blocking=True,
            dry_run=True if dry_run else None,
        )

    imported_rows = len(prepared)

    if dry_run:
        return _empty_contract(
            imported_rows=imported_rows,
            skipped_rows=skipped_rows,
            errors=errors,
            issues=issues,
            blocking=False,
            dry_run=True,
        )

    with transaction.atomic():
        all_records: list[Info] = []
        for group, title, row_attrs, existing_key in prepared:
            attrs = importable_attributes(title.id)
            attrs_by_id = {a.id: a for a in attrs}
            has_report_date_flag = any(a.is_report_date for a in attrs)

            if existing_key is not None:
                _archive_row_key(existing_key, reason="replaced by re-import")
            elif not has_report_date_flag:
                report_date = (group.values.get("report_date") or "").strip()
                if report_date:
                    _archive_incident_rows_for_date(
                        title=title,
                        sub_main_id=sub_main.id,
                        report_date=report_date,
                    )

            # Target row_key must be free: unique is (attribute_id, row_key) globally.
            if Info.objects.filter(
                row_key=group.row_key,
                archived=False,
                confirmed=Info.ConfirmStatus.WAITING,
            ).exists():
                _archive_row_key(group.row_key, reason="replaced by re-import")

            all_records.extend(
                build_info_records_from_row(
                    row_attrs,
                    attrs_by_id,
                    sub_main=sub_main,
                    user=user,
                    row_key=group.row_key,
                )
            )
        if all_records:
            Info.objects.bulk_create(all_records)

    return _empty_contract(
        imported_rows=imported_rows,
        skipped_rows=skipped_rows,
        errors=errors,
        issues=issues,
        blocking=False,
    )
