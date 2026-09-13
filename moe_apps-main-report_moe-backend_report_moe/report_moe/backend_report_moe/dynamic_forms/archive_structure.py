"""Soft-delete structure (Title / sections) and archive related Info rows.

Deletion is blocked when active (non-archived) Info rows are linked.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Info, MainSection, SubMainSection, Title

REASON_TITLE = "title_deleted"
REASON_SUB = "sub_main_deleted"
REASON_MAIN = "main_section_deleted"


class StructureHasRelatedData(ValidationError):
    """Raised when soft-delete is refused because linked Info exists."""

    default_detail = (
        "لا يمكن الحذف لوجود بيانات مدخلة مرتبطة. "
        "انقل أو احذف البيانات أولاً، أو أبقِ العنصر كما هو."
    )


def _mark_soft_deleted(instance, user) -> None:
    if getattr(instance, "deleted", False):
        return
    instance.deleted = True
    instance.deleted_at = timezone.now()
    instance.deleted_by = user if getattr(user, "is_authenticated", False) else None
    instance.save(update_fields=["deleted", "deleted_at", "deleted_by"])


def _archive_infos(qs, reason: str) -> int:
    now = timezone.now()
    return qs.filter(archived=False).update(
        archived=True,
        archived_at=now,
        archive_reason=reason,
    )


def _descendant_sub_main_ids(root: SubMainSection) -> list[int]:
    """BFS over children (includes root)."""
    ids = [root.id]
    frontier = [root.id]
    while frontier:
        child_ids = list(
            SubMainSection.objects.filter(parent_id__in=frontier).values_list(
                "id", flat=True
            )
        )
        new_ids = [i for i in child_ids if i not in ids]
        if not new_ids:
            break
        ids.extend(new_ids)
        frontier = new_ids
    return ids


def _raise_if_related(count: int, label: str) -> None:
    if count <= 0:
        return
    raise StructureHasRelatedData(
        {
            "detail": (
                f"لا يمكن الحذف: يوجد {count} سجل بيانات مرتبط بـ{label}. "
                "يجب إزالة أو نقل البيانات أولاً."
            ),
            "related_infos": count,
        }
    )


def assert_title_deletable(title: Title) -> None:
    count = Info.objects.filter(
        attribute__title_id=title.id, archived=False
    ).count()
    _raise_if_related(count, "هذا المسمّى")


def assert_sub_main_deletable(sub: SubMainSection) -> None:
    sub_ids = _descendant_sub_main_ids(sub)
    count = Info.objects.filter(sub_main_id__in=sub_ids, archived=False).count()
    _raise_if_related(count, "هذا القسم الفرعي (أو أقسامه الفرعية)")


def assert_main_section_deletable(main: MainSection) -> None:
    count = Info.objects.filter(
        sub_main__main_section_id=main.id, archived=False
    ).count()
    _raise_if_related(count, "هذا القسم الرئيسي")


@transaction.atomic
def soft_delete_title(title: Title, user) -> dict:
    assert_title_deletable(title)
    _mark_soft_deleted(title, user)
    archived = _archive_infos(
        Info.objects.filter(attribute__title_id=title.id),
        REASON_TITLE,
    )
    return {"title_id": title.id, "archived_infos": archived}


@transaction.atomic
def soft_delete_sub_main(sub: SubMainSection, user) -> dict:
    assert_sub_main_deletable(sub)
    sub_ids = _descendant_sub_main_ids(sub)
    now = timezone.now()
    SubMainSection.objects.filter(id__in=sub_ids, deleted=False).update(
        deleted=True,
        deleted_at=now,
        deleted_by=user if getattr(user, "is_authenticated", False) else None,
    )
    archived = _archive_infos(
        Info.objects.filter(sub_main_id__in=sub_ids),
        REASON_SUB,
    )
    return {"sub_main_ids": sub_ids, "archived_infos": archived}


@transaction.atomic
def soft_delete_main_section(main: MainSection, user) -> dict:
    assert_main_section_deletable(main)
    _mark_soft_deleted(main, user)
    sub_ids = list(
        SubMainSection.objects.filter(main_section_id=main.id).values_list(
            "id", flat=True
        )
    )
    now = timezone.now()
    if sub_ids:
        SubMainSection.objects.filter(id__in=sub_ids, deleted=False).update(
            deleted=True,
            deleted_at=now,
            deleted_by=user if getattr(user, "is_authenticated", False) else None,
        )
    archived = _archive_infos(
        Info.objects.filter(
            Q(sub_main_id__in=sub_ids) | Q(sub_main__main_section_id=main.id)
        ),
        REASON_MAIN,
    )
    return {
        "main_section_id": main.id,
        "sub_main_ids": sub_ids,
        "archived_infos": archived,
    }
