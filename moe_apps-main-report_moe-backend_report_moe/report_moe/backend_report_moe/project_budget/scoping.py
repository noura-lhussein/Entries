"""Foundation and project scoping helpers for project-budget querysets."""

from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


def is_budget_admin(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (
            user.is_staff
            or user.is_superuser
            or getattr(user, "can_manage_budget", False)
        )
    )


def is_system_admin(user) -> bool:
    """Django staff / superuser — full app admin including reference data."""
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def user_is_foundation_budget_manager(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (
            is_system_admin(user)
            or getattr(user, "can_manage_budget", False)
            or getattr(user, "can_manage_budget_users", False)
        )
    )


def user_can_manage_responsibles(user) -> bool:
    return user_can_manage_reference_data(user) or bool(
        getattr(user, "can_manage_budget", False)
    )


def user_can_manage_reference_data(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if is_system_admin(user):
        return True
    if not getattr(user, "can_manage_reference_data", False):
        return False
    return is_budget_module_user(user)


def get_user_foundation_id(user) -> int | None:
    if not user or not user.is_authenticated:
        return None
    scope = getattr(user, "budget_scope", None)
    if scope is None:
        return None
    return scope.foundation_id


def is_budget_module_user(user) -> bool:
    return get_user_foundation_id(user) is not None


def _has_any_budget_flag(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and (
            is_budget_admin(user)
            or getattr(user, "can_view_budget", False)
            or getattr(user, "can_write_budget", False)
            or getattr(user, "can_manage_budget_users", False)
            or getattr(user, "can_manage_reference_data", False)
        )
    )


def user_can_read_budget(user) -> bool:
    if not _has_any_budget_flag(user):
        return False
    if is_system_admin(user):
        return True
    return is_budget_module_user(user)


def user_can_write_budget(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if not (is_budget_admin(user) or getattr(user, "can_write_budget", False)):
        return False
    if is_system_admin(user):
        return True
    return is_budget_module_user(user)


def user_can_manage_budget_users(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if not (is_budget_admin(user) or getattr(user, "can_manage_budget_users", False)):
        return False
    if is_system_admin(user):
        return True
    return is_budget_module_user(user)


def user_skips_project_filter(user) -> bool:
    """Foundation managers and system admins see all projects in their foundation."""
    return is_system_admin(user) or user_is_foundation_budget_manager(user)


def get_assigned_project_ids(user) -> set[int]:
    from .models import ProjectUserAssignment

    return set(
        ProjectUserAssignment.objects.filter(user=user).values_list(
            "project_id", flat=True
        )
    )


def filter_queryset_by_foundation(qs, user, field_path: str = "foundation_id"):
    """Restrict queryset to the user's foundation unless system admin."""
    if is_system_admin(user):
        return qs
    foundation_id = get_user_foundation_id(user)
    if foundation_id is None:
        return qs.none()
    return qs.filter(**{field_path: foundation_id})


def filter_queryset_by_user_foundation(qs, user, field_path: str = "foundation_id"):
    """Restrict to user's foundation unless system admin (staff)."""
    return filter_queryset_by_foundation(qs, user, field_path)


def filter_queryset_by_project_scope(
    qs,
    user,
    foundation_path: str = "foundation_id",
    project_path: str = "pk",
):
    """Foundation boundary + assigned projects for regular budget users."""
    if is_system_admin(user):
        return qs
    foundation_id = get_user_foundation_id(user)
    if foundation_id is None:
        return qs.none()
    qs = qs.filter(**{foundation_path: foundation_id})
    if user_skips_project_filter(user):
        return qs
    assigned = get_assigned_project_ids(user)
    if not assigned:
        return qs.none()
    return qs.filter(**{f"{project_path}__in": assigned})


def assert_foundation_accessible(user, foundation_id: int) -> None:
    if is_system_admin(user):
        return
    user_foundation_id = get_user_foundation_id(user)
    if user_foundation_id is None or user_foundation_id != foundation_id:
        raise PermissionDenied("لا يمكنك الوصول لبيانات خارج مؤسستك.")


def assert_project_accessible(user, project) -> None:
    if is_system_admin(user):
        return
    foundation_id = get_user_foundation_id(user)
    if foundation_id is None or project.foundation_id != foundation_id:
        raise PermissionDenied("لا يمكنك الوصول لهذا المشروع.")
    if user_skips_project_filter(user):
        return
    assigned = get_assigned_project_ids(user)
    if project.pk not in assigned:
        raise PermissionDenied("لا يمكنك الوصول لهذا المشروع.")
