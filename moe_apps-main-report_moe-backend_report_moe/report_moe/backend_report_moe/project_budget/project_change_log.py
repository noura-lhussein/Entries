"""Project field-level change logging."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from .models import Project, ProjectChangeLog

TRACKED_FIELDS: dict[str, str] = {
    "percentage_completion": "نسبة الإنجاز",
    "completion_is_manual": "تحديد الإنجاز يدوياً",
    "budget_expenditure": "الصرف من الموازنة",
    "proposed_budget": "الموازنة المقترحة",
    "approved_budget": "الموازنة المعتمدة",
    "latitude": "خط العرض",
    "longitude": "خط الطول",
    "community": "التجمّع (الموقع)",
    "status": "الحالة",
    "name_ar": "الاسم العربي",
    "name_en": "الاسم الإنجليزي",
    "description": "الوصف",
    "start_date": "تاريخ البداية",
    "end_date": "تاريخ النهاية",
    "annual_budget": "الموازنة السنوية",
    "foundation": "الشركة",
    "previous_project": "المشروع السابق",
    "is_round": "جولة",
    "target": "الهدف",
    "policy": "السياسة",
    "quantitative_target_value": "الهدف الكمي",
    "quantitative_target_unit": "وحدة القياس",
}

STATUS_LABELS = {
    "draft": "مسودة",
    "active": "نشط",
    "on_hold": "معلق",
    "completed": "مكتمل",
    "cancelled": "ملغى",
}


def extract_change_meta(initial_data: Any) -> dict[str, Any]:
    if not isinstance(initial_data, dict):
        return {}
    raw = initial_data.get("_change_meta")
    if not isinstance(raw, dict):
        return {}
    meta: dict[str, Any] = {}
    for key in ("client_latitude", "client_longitude"):
        value = raw.get(key)
        if value in (None, ""):
            continue
        try:
            meta[key] = Decimal(str(value))
        except Exception:
            continue
    return meta


def request_ip(request) -> str | None:
    if request is None:
        return None
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR")


def request_user_agent(request) -> str:
    if request is None:
        return ""
    return str(request.META.get("HTTP_USER_AGENT", ""))[:512]


def snapshot_project(project: Project) -> dict[str, str]:
    return {field: _field_display(project, field) for field in TRACKED_FIELDS}


def log_project_changes(
    project: Project,
    old_snapshot: dict[str, str],
    new_snapshot: dict[str, str],
    *,
    request,
    change_meta: dict[str, Any] | None = None,
    action: str = ProjectChangeLog.Action.UPDATE,
) -> list[ProjectChangeLog]:
    user = request.user if request and request.user.is_authenticated else None
    meta = change_meta or {}
    batch_id = uuid.uuid4()
    rows: list[ProjectChangeLog] = []

    for field_name, field_label in TRACKED_FIELDS.items():
        old_value = old_snapshot.get(field_name, "")
        new_value = new_snapshot.get(field_name, "")
        if old_value == new_value:
            continue
        if action == ProjectChangeLog.Action.CREATE and not new_value:
            continue
        rows.append(
            ProjectChangeLog(
                project=project,
                batch_id=batch_id,
                action=action,
                field_name=field_name,
                field_label=field_label,
                old_value=old_value,
                new_value=new_value,
                changed_by=user,
                ip_address=request_ip(request),
                client_latitude=meta.get("client_latitude"),
                client_longitude=meta.get("client_longitude"),
                user_agent=request_user_agent(request),
            )
        )

    if rows:
        ProjectChangeLog.objects.bulk_create(rows)
    return rows


def log_project_created(project: Project, *, request, change_meta: dict[str, Any] | None = None) -> None:
    new_snapshot = snapshot_project(project)
    old_snapshot = {field: "" for field in TRACKED_FIELDS}
    log_project_changes(
        project,
        old_snapshot,
        new_snapshot,
        request=request,
        change_meta=change_meta,
        action=ProjectChangeLog.Action.CREATE,
    )


def log_project_deleted(project: Project, *, request) -> None:
    user = request.user if request and request.user.is_authenticated else None
    ProjectChangeLog.objects.create(
        project=project,
        batch_id=uuid.uuid4(),
        action=ProjectChangeLog.Action.DELETE,
        field_name="__delete__",
        field_label="حذف المشروع",
        old_value=project.name_ar or project.code or str(project.pk),
        new_value="",
        changed_by=user,
        ip_address=request_ip(request),
        user_agent=request_user_agent(request),
    )


def refresh_project_for_snapshot(project: Project) -> Project:
    return (
        Project.objects.select_related(
            "annual_budget",
            "foundation",
            "community",
            "previous_project",
            "target",
            "policy",
            "quantitative_target_unit",
        )
        .get(pk=project.pk)
    )


def _field_display(project: Project, field_name: str) -> str:
    if field_name == "annual_budget":
        if not project.annual_budget_id:
            return ""
        budget = project.annual_budget
        code = getattr(budget, "code", "") or ""
        year = getattr(budget, "year", "")
        return f"{code} ({year})".strip()

    if field_name == "foundation":
        return project.foundation.name_ar if project.foundation_id else ""

    if field_name == "community":
        return project.community.name_ar if project.community_id else ""

    if field_name == "previous_project":
        if not project.previous_project_id:
            return ""
        prev = project.previous_project
        return prev.code or prev.name_ar or str(prev.pk)

    if field_name == "target":
        return project.target.name_ar if getattr(project, "target_id", None) else ""

    if field_name == "policy":
        return project.policy.name_ar if getattr(project, "policy_id", None) else ""

    if field_name == "quantitative_target_unit":
        unit = project.quantitative_target_unit
        if not unit:
            return ""
        symbol = getattr(unit, "symbol", "") or ""
        name = unit.name_ar or ""
        return f"{name} ({symbol})".strip(" ()") if symbol else name

    if field_name == "status":
        raw = getattr(project, "status", "") or ""
        return STATUS_LABELS.get(raw, raw)

    if field_name in {"completion_is_manual", "is_round"}:
        return _format_bool(getattr(project, field_name, False))

    if field_name in {"start_date", "end_date"}:
        value = getattr(project, field_name, None)
        return str(value) if value else ""

    if field_name == "description":
        return (getattr(project, field_name, "") or "").strip()

    value = getattr(project, field_name, None)
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if value is None:
        return ""
    return str(value).strip()


def _format_bool(value: Any) -> str:
    return "نعم" if bool(value) else "لا"


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return ""
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"
