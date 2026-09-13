from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """View-only: `datasets_dataset` is owned by report_moe master_data."""

    list_display = ('title_en', 'organization', 'governorate', 'sector', 'status', 'updated_at')
    search_fields = ('title_en', 'title_ar', 'slug')
    list_filter = ('status', 'sector', 'is_active')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
