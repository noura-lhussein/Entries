"""Shared authorization checks for user-assigned sub-sections and titles."""

from rest_framework.exceptions import PermissionDenied, ValidationError


def is_admin(user) -> bool:
    return bool(user.is_staff or user.is_superuser)


def assert_sub_main_assigned(user, sub_main) -> None:
    """Block writes to a sub-section the user is not assigned to (admins exempt)."""
    if is_admin(user):
        return
    if not user.user_sub_mains.filter(sub_main_id=sub_main.id).exists():
        raise PermissionDenied("ليس لديك صلاحية على هذا القسم الفرعي.")


def assert_sub_main_is_leaf(sub_main) -> None:
    """Info entry and UserSubMain assignment are leaf-only in phase 1."""
    if sub_main.children.filter(deleted=False).exists():
        raise ValidationError(
            {"sub_main":
                "الإدخال والصلاحيات مسموحة فقط على الأوراق (أقسام بدون أبناء)."}
        )


def allowed_title_ids(user) -> set[int] | None:
    """Title ids the user may write to; None means no restriction (admin).

    Prefer explicit ``UserTitle`` rows when present (subset of assigned categories).
    Otherwise every Title in the user's ``UserTitleCategory`` assignments.
    Soft-deleted titles are never included.
    """
    from .models import Title

    if is_admin(user):
        return None
    category_ids = list(
        user.user_title_categories.values_list("category_id", flat=True))
    explicit = set(user.user_titles.values_list("title_id", flat=True))
    if explicit:
        qs = Title.objects.filter(deleted=False, id__in=explicit)
        if category_ids:
            qs = qs.filter(category_id__in=category_ids)
        return set(qs.values_list("id", flat=True))
    if not category_ids:
        return set()
    return set(
        Title.objects.filter(
            deleted=False, category_id__in=category_ids
        ).values_list("id", flat=True)
    )


def allowed_title_category_ids(user) -> set[int] | None:
    """Category ids assigned to the user; None means no restriction (admin)."""
    if is_admin(user):
        return None
    return set(user.user_title_categories.values_list("category_id", flat=True))


def assert_attribute_title_assigned(user, attribute) -> None:
    """Block writes to attributes whose title is not assigned to the user."""
    allowed = allowed_title_ids(user)
    if allowed is None:
        return
    title_id = attribute.title_id
    if title_id is None or title_id not in allowed:
        raise PermissionDenied("ليس لديك صلاحية على هذا العنوان.")
