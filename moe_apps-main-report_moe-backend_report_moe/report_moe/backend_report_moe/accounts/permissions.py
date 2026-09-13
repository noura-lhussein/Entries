"""Portal RBAC predicates.

These take a request and raise, which suits the places that still call them
directly. New views should prefer the DRF classes in `drf_permissions.py`, which
wrap the same rules and let DRF handle the response.
"""

from __future__ import annotations

from rest_framework.exceptions import NotAuthenticated, PermissionDenied

SECTOR_OIL_GAS = 'oil-gas'
SECTOR_ELECTRICITY = 'electricity'
SECTOR_WATER = 'water-resources'
SECTOR_MINERAL = 'mineral-resources'


def require_user(request):
    user = getattr(request, 'auth', None)
    if user is None or not getattr(user, 'is_active', False):
        raise NotAuthenticated('Authentication required.')
    return user


def require_oil_gas(request, *, write: bool = False):
    user = require_user(request)
    if not user.can_access_oil_gas(write=write):
        raise PermissionDenied('Petroleum permission required.')
    return user


def require_electricity(request, *, write: bool = False):
    user = require_user(request)
    if not user.can_access_electricity(write=write):
        raise PermissionDenied('Electricity permission required.')
    return user


def require_water(request, *, write: bool = False):
    user = require_user(request)
    if not user.can_access_water(write=write):
        raise PermissionDenied('Water permission required.')
    return user


def require_mineral(request, *, write: bool = False):
    user = require_user(request)
    if not user.can_access_mineral(write=write):
        raise PermissionDenied('Geology & mineral resources permission required.')
    return user


def user_can_view_sector(user, sector: str) -> bool:
    if getattr(user, 'is_portal_admin', False):
        return True
    if sector == SECTOR_OIL_GAS:
        return user.can_access_oil_gas()
    if sector == SECTOR_ELECTRICITY:
        return user.can_access_electricity()
    if sector == SECTOR_WATER:
        return user.can_access_water()
    if sector == SECTOR_MINERAL:
        return user.can_access_mineral()
    # Shared / other sectors: admins only (already returned True above).
    return False


def require_sector_view(request, sector: str):
    """Require view access for a portal sector slug."""
    user = require_user(request)
    if not user_can_view_sector(user, sector):
        raise PermissionDenied('Sector permission required.')
    return user


def allowed_view_sectors(user) -> list[str]:
    if getattr(user, 'is_portal_admin', False):
        return [SECTOR_OIL_GAS, SECTOR_ELECTRICITY, SECTOR_WATER, SECTOR_MINERAL]
    sectors: list[str] = []
    if user.can_access_oil_gas():
        sectors.append(SECTOR_OIL_GAS)
    if user.can_access_electricity():
        sectors.append(SECTOR_ELECTRICITY)
    if user.can_access_water():
        sectors.append(SECTOR_WATER)
    if user.can_access_mineral():
        sectors.append(SECTOR_MINERAL)
    return sectors


def require_manage_datasets(request, *, write: bool = False):
    user = require_user(request)
    if write and not (user.is_portal_admin or user.can_manage_datasets):
        raise PermissionDenied('Dataset management permission required.')
    return user


def require_control_panel(request):
    user = require_user(request)
    if not (user.is_portal_admin or user.can_manage_control_panel):
        raise PermissionDenied('Control panel permission required.')
    return user
