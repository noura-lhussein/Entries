"""Sector permission helpers for master-data APIs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated

from .registry import Sector

if TYPE_CHECKING:
    from django.contrib.auth.base_user import AbstractBaseUser


def _is_full_admin(user: AbstractBaseUser) -> bool:
    # Single source of truth: User.is_portal_admin (is_admin OR staff OR superuser).
    return bool(getattr(user, 'is_portal_admin', False))


def user_can_access_sector(user: AbstractBaseUser, sector: Sector, *, write: bool = False) -> bool:
    """Master-data reference tables are admin-only, exclusively — no sector
    write/view flag grants access here, unlike the operational data these
    catalogs feed into."""
    if not getattr(user, 'is_authenticated', False):
        return False
    return _is_full_admin(user)


def user_allowed_sectors(user: AbstractBaseUser, *, write: bool = False) -> set[Sector]:
    sectors: set[Sector] = set()
    for sector in ('oil_gas', 'electricity', 'water', 'mineral', 'portal', 'projects'):
        if user_can_access_sector(user, sector, write=write):  # type: ignore[arg-type]
            sectors.add(sector)  # type: ignore[arg-type]
    return sectors


def user_can_access_master_data(user: AbstractBaseUser) -> bool:
    """Nav / page access: admin only, exclusively."""
    if not getattr(user, 'is_authenticated', False):
        return False
    return _is_full_admin(user)


def require_sector(user: AbstractBaseUser, sector: Sector, *, write: bool = False) -> None:
    if not user_can_access_sector(user, sector, write=write):
        raise PermissionDenied('ليس لديك صلاحية على هذا القطاع.')


class CanAccessMasterData(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and user_can_access_master_data(request.user))


class IsAuthenticatedMasterData(IsAuthenticated):
    """Authenticated users who can open the master-data module."""

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        return user_can_access_master_data(request.user)
