"""Sector permission classes for the portal endpoints.

The rules themselves live on the user model (`can_access_water(write=...)` and
friends); these classes only adapt them to DRF. Ninja read the caller from
`request.auth`, DRF reads it from `request.user` — that is the whole difference,
and putting it in one place keeps it from being re-derived at every view.

Write access is inferred from the HTTP method rather than declared per view, so a
POST cannot silently pass a read-only check.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class SectorPermission(BasePermission):
    """Base for the four sector gates. Subclasses name the model method."""

    #: Name of the `can_access_*` method on the user model.
    access_method: str = ""

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_active:
            return False
        check = getattr(user, self.access_method, None)
        if check is None:
            return False
        return bool(check(write=request.method not in SAFE_METHODS))


class CanAccessOilGas(SectorPermission):
    access_method = "can_access_oil_gas"
    message = "Petroleum permission required."


class CanAccessElectricity(SectorPermission):
    access_method = "can_access_electricity"
    message = "Electricity permission required."


class CanAccessWater(SectorPermission):
    access_method = "can_access_water"
    message = "Water permission required."


class CanAccessMineral(SectorPermission):
    access_method = "can_access_mineral"
    message = "Geology & mineral resources permission required."


class CanManageControlPanel(BasePermission):
    """Portal control panel: institutions, catalogues and other shared lookups."""

    message = "Control panel permission required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_active:
            return False
        return bool(user.is_portal_admin or user.can_manage_control_panel)


class CanManageDatasets(BasePermission):
    """Dataset administration. Reads are open to any signed-in portal user."""

    message = "Dataset management permission required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_active:
            return False
        if request.method in SAFE_METHODS:
            return True
        return bool(user.is_portal_admin or user.can_manage_datasets)


class CanManageProjects(BasePermission):
    """Development-projects section of the portal — read and write both need the
    flag (`projects` is a manage-only portal sector, no view/write split)."""

    message = "Projects permission required."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or not user.is_active:
            return False
        return bool(user.is_portal_admin or user.can_manage_projects)
