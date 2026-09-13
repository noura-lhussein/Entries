from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from .models import ProjectCategory, ProjectType


def category_prefix_for_project_type_name(name_ar: str) -> str | None:
    """Map budget project type label to investment category code prefix (31/32/33)."""
    name = (name_ar or "").strip()
    if not name:
        return None
    if "استبدال" in name or "تجديد" in name:
        return "33"
    if "مباشر" in name:
        return "32"
    if "جديد" in name:
        return "31"
    return None


def category_prefix_for_project_type(project_type: ProjectType) -> str | None:
    return category_prefix_for_project_type_name(project_type.name_ar)


def filter_categories_by_project_type(
    queryset: QuerySet[ProjectCategory],
    project_type_id: int | str | None,
) -> QuerySet[ProjectCategory]:
    if not project_type_id:
        return queryset

    from .models import ProjectType

    project_type = (
        ProjectType.objects.filter(pk=project_type_id, deleted=False)
        .only("name_ar")
        .first()
    )
    if project_type is None:
        return queryset.none()

    prefix = category_prefix_for_project_type(project_type)
    if not prefix:
        return queryset

    return queryset.filter(code__startswith=prefix)


def build_category_lookup(categories: list[ProjectCategory]) -> dict[int, ProjectCategory]:
    return {category.pk: category for category in categories}


def category_breadcrumb(
    category: ProjectCategory,
    by_id: dict[int, ProjectCategory],
) -> list[str]:
    parts: list[str] = []
    current: ProjectCategory | None = category
    seen: set[int] = set()

    while current is not None and current.pk not in seen:
        seen.add(current.pk)
        parts.append(current.name_ar or str(current.pk))
        parent_id = current.parent_id
        current = by_id.get(parent_id) if parent_id else None

    parts.reverse()
    return parts
