from rest_framework import permissions

from .scoping import (
    is_system_admin,
    user_can_manage_budget_users,
    user_can_manage_reference_data,
    user_can_manage_responsibles,
    user_can_read_budget,
    user_can_write_budget,
)


class IsBudgetAdminOrReadOnly(permissions.BasePermission):
    """Budget module: read with can_view_budget; write with can_write_budget or can_manage_budget."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_read_budget(user)
        return user_can_write_budget(user)


class IsReferenceDataAdminOrReadOnly(permissions.BasePermission):
    """Reference tables: read for budget users; write for system admin or can_manage_reference_data."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_read_budget(user)
        return user_can_manage_reference_data(user)


class IsAnnualBudgetAdminOrReadOnly(permissions.BasePermission):
    """Annual budgets: read for budget users; CRUD for system admin only."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_read_budget(user)
        return is_system_admin(user)


class CanManageResponsiblesOrReadOnly(permissions.BasePermission):
    """Responsibles: read for budget users; write for system admin or can_manage_budget."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return user_can_read_budget(user)
        return user_can_manage_responsibles(user)


class CanManageBudgetUsers(permissions.BasePermission):
    """Admin or users with can_manage_budget_users."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user_can_manage_budget_users(user)
