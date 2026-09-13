from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ('email',)
    list_display = (
        'email',
        'full_name',
        'is_admin',
        'is_staff',
        'is_active',
        'deleted',
        'date_joined',
    )
    list_filter = (
        'is_admin',
        'is_staff',
        'is_active',
        'is_superuser',
        'deleted',
        'can_write_oil_gas',
        'can_write_electricity',
        'can_write_water',
        'can_write_mineral',
        'can_view_budget',
        'can_write_budget',
    )
    search_fields = ('email', 'full_name')
    # Derived cache — set via `portal_sectors` + can_view_info/can_write_info,
    # recomputed by apply_portal_sectors() (see save_model below).
    readonly_fields = (
        'can_view_oil_gas', 'can_write_oil_gas',
        'can_view_electricity', 'can_write_electricity',
        'can_view_water', 'can_write_water',
        'can_view_mineral', 'can_write_mineral',
        'can_manage_projects',
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('full_name', 'status', 'parent')}),
        (
            'Portal RBAC',
            {
                'description': (
                    'portal_sectors + the Reports/Budget "view/write info" flags '
                    'set the per-sector access below (recomputed on save).'
                ),
                'fields': (
                    'is_admin',
                    'portal_sectors',
                    'can_manage_datasets',
                    'can_manage_control_panel',
                    'can_view_oil_gas',
                    'can_write_oil_gas',
                    'can_view_electricity',
                    'can_write_electricity',
                    'can_view_water',
                    'can_write_water',
                    'can_view_mineral',
                    'can_write_mineral',
                    'can_manage_projects',
                ),
            },
        ),
        (
            'Reports / Budget RBAC',
            {
                'fields': (
                    'can_write_info',
                    'can_view_info',
                    'can_confirm_info',
                    'can_export_reports',
                    'can_add_user',
                    'can_view_budget',
                    'can_write_budget',
                    'can_manage_budget_users',
                    'can_manage_budget',
                    'can_manage_reference_data',
                    'deleted',
                ),
            },
        ),
        (
            'Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'full_name',
                    'password1',
                    'password2',
                    'is_admin',
                    'is_staff',
                    'is_active',
                ),
            },
        ),
    )
    filter_horizontal = ('groups', 'user_permissions')
    raw_id_fields = ('parent',)

    def save_model(self, request, obj, form, change):
        obj.apply_portal_sectors()
        super().save_model(request, obj, form, change)
