from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Report / budget user for report_moe (email login).

    moeds owns a separate user table with the same shape; the two were split
    apart deliberately and are no longer kept in sync. Fields here that read as
    portal sector RBAC are retained so the split could copy every row verbatim.
    """

    email = models.EmailField('email address', unique=True, db_index=True)
    full_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    # ── moeds portal (Ministry of Energy) access ─────────────────────────────
    # `portal_sectors` is the single input the admin edits. The per-sector
    # booleans below are a cache kept in sync by `apply_portal_sectors()` (called
    # from the user serializers) so the moeds portal — which reads
    # can_view_water / can_write_water / … from /auth/me/ — needs no change.
    #   view  = sector selected  AND (can_view_info OR can_write_info)
    #   write = sector selected  AND  can_write_info
    #   projects = 'projects' selected
    PORTAL_SECTORS = ('water', 'electricity', 'oil_gas', 'mineral', 'projects')

    is_admin = models.BooleanField(
        default=False,
        help_text='Full portal admin: all sectors, control panel, user management.',
    )
    portal_sectors = models.JSONField(
        default=list,
        blank=True,
        help_text="moeds portal sectors, subset of User.PORTAL_SECTORS.",
    )
    can_view_oil_gas = models.BooleanField(default=False)
    can_write_oil_gas = models.BooleanField(default=False)
    can_view_electricity = models.BooleanField(default=False)
    can_write_electricity = models.BooleanField(default=False)
    can_view_water = models.BooleanField(default=False)
    can_write_water = models.BooleanField(default=False)
    can_view_mineral = models.BooleanField(default=False)
    can_write_mineral = models.BooleanField(default=False)
    can_manage_projects = models.BooleanField(default=False)
    can_manage_datasets = models.BooleanField(default=False)
    can_manage_control_panel = models.BooleanField(default=False)

    # Report / budget RBAC. is_staff is Django admin only.
    status = models.CharField(max_length=50, blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
    )
    can_write_info = models.BooleanField(default=False)
    can_view_info = models.BooleanField(default=False)
    can_confirm_info = models.BooleanField(default=False)
    can_export_reports = models.BooleanField(default=False)
    can_add_user = models.BooleanField(default=False)
    can_view_budget = models.BooleanField(default=False)
    can_write_budget = models.BooleanField(default=False)
    can_manage_budget_users = models.BooleanField(default=False)
    can_manage_budget = models.BooleanField(
        default=False,
        help_text='Full budget-module admin (all foundations); not Django staff.',
    )
    can_manage_reference_data = models.BooleanField(
        default=False,
        help_text='CRUD on budget reference-data tabs (categories, companies, etc.).',
    )
    deleted = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self) -> str:
        return self.email

    @property
    def display_name(self) -> str:
        return self.full_name.strip() or self.email.split('@', 1)[0]

    @property
    def username(self) -> str:
        """Compatibility alias for code that still expects a username attribute."""
        return self.email

    def get_full_name(self) -> str:
        return self.full_name.strip()

    def get_short_name(self) -> str:
        return self.display_name

    def get_all_subordinates(self):
        result = []
        queue = list(self.subordinates.all())
        while queue:
            u = queue.pop()
            result.append(u)
            queue.extend(u.subordinates.all())
        return result

    @property
    def is_portal_admin(self) -> bool:
        """Full moeds-portal admin: the model flag OR any Django-admin superuser.
        The single 'is this a portal admin' check — used by every portal gate
        (can_access_*, has_admin_ui_access, the DRF Can* classes, UserSerializer)."""
        return bool(self.is_admin or self.is_staff or self.is_superuser)

    def has_admin_ui_access(self) -> bool:
        if self.is_portal_admin:
            return True
        return any(
            (
                self.can_write_oil_gas,
                self.can_write_electricity,
                self.can_write_water,
                self.can_write_mineral,
                self.can_manage_projects,
                self.can_manage_datasets,
                self.can_manage_control_panel,
            )
        )

    def can_access_oil_gas(self, *, write: bool = False) -> bool:
        if self.is_portal_admin:
            return True
        if write:
            return self.can_write_oil_gas
        return self.can_view_oil_gas or self.can_write_oil_gas

    def can_access_electricity(self, *, write: bool = False) -> bool:
        if self.is_portal_admin:
            return True
        if write:
            return self.can_write_electricity
        return self.can_view_electricity or self.can_write_electricity

    def can_access_water(self, *, write: bool = False) -> bool:
        if self.is_portal_admin:
            return True
        if write:
            return self.can_write_water
        return self.can_view_water or self.can_write_water

    def can_access_mineral(self, *, write: bool = False) -> bool:
        if self.is_portal_admin:
            return True
        if write:
            return self.can_write_mineral
        return self.can_view_mineral or self.can_write_mineral

    def apply_portal_sectors(self) -> None:
        """Recompute the per-sector portal booleans from `portal_sectors` and the
        view/write level (`can_view_info` / `can_write_info`). Call after setting
        `portal_sectors`; the serializers do this on create/update."""
        selected = {s for s in (self.portal_sectors or []) if s in self.PORTAL_SECTORS}
        self.portal_sectors = sorted(selected)
        level_view = bool(self.can_view_info or self.can_write_info)
        level_write = bool(self.can_write_info)
        for sector in ('water', 'electricity', 'oil_gas', 'mineral'):
            picked = sector in selected
            setattr(self, f'can_view_{sector}', picked and level_view)
            setattr(self, f'can_write_{sector}', picked and level_write)
        self.can_manage_projects = 'projects' in selected

    def grant_full_portal_access(self) -> None:
        """Grant all portal sector and management flags (demo / bootstrap)."""
        self.is_admin = True
        self.can_view_info = True
        self.can_write_info = True
        self.portal_sectors = list(self.PORTAL_SECTORS)
        self.apply_portal_sectors()
        self.can_manage_datasets = True
        self.can_manage_control_panel = True
