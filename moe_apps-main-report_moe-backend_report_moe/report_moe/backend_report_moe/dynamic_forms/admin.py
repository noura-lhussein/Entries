from django.contrib import admin

from .models import (
    Attribute,
    AuditLog,
    Info,
    MainSection,
    Option,
    ReqReport,
    ReqReportSubMain,
    ReqReportTitle,
    SubMainSection,
    Title,
    TitleCategory,
    UserSubMain,
    UserTitle,
    UserTitleCategory,
)

# User admin lives in accounts.admin.


# ── Structure ─────────────────────────────────────────────────────────────────

@admin.register(TitleCategory)
class TitleCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'name')
    list_editable = ('order',)
    ordering = ('order', 'id')
    search_fields = ('name',)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'name', 'category')
    list_editable = ('order',)
    list_filter = ('category',)
    ordering = ('order', 'id')
    search_fields = ('name',)


@admin.register(MainSection)
class MainSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(SubMainSection)
class SubMainSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'main_section', 'location_district')
    list_filter = ('main_section', 'location_district__governorate')
    search_fields = ('name',)
    raw_id_fields = ('location_district',)


# ── User Roles ────────────────────────────────────────────────────────────────

@admin.register(UserSubMain)
class UserSubMainAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'sub_main')
    list_filter = ('sub_main', 'sub_main__main_section')
    search_fields = ('user__email', 'user__full_name', 'sub_main__name')
    raw_id_fields = ('user',)


@admin.register(UserTitle)
class UserTitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title')
    list_filter = ('title',)
    search_fields = ('user__email', 'user__full_name', 'title__name')
    raw_id_fields = ('user',)


@admin.register(UserTitleCategory)
class UserTitleCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'category')
    list_filter = ('category',)
    search_fields = ('user__email', 'user__full_name', 'category__name')
    raw_id_fields = ('user',)


# ── Form Builder ──────────────────────────────────────────────────────────────

class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    fields = ('label',)


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'type', 'required', 'title')
    list_filter = ('type', 'required', 'title')
    search_fields = ('label',)
    inlines = [OptionInline]


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'label', 'attribute')
    list_filter = ('attribute__title',)
    search_fields = ('label', 'attribute__label')


# ── Report Requests ───────────────────────────────────────────────────────────

class ReqReportTitleInline(admin.TabularInline):
    model = ReqReportTitle
    extra = 0
    fields = ('title',)


class ReqReportInline(admin.TabularInline):
    model = ReqReport
    extra = 0
    fields = ('user', 'date_from', 'date_to')
    readonly_fields = ('user',)


@admin.register(ReqReportSubMain)
class ReqReportSubMainAdmin(admin.ModelAdmin):
    list_display = ('id', 'sub_main', 'title_list', 'report_count')
    list_filter = ('sub_main__main_section', 'sub_main')
    search_fields = ('sub_main__name',)
    inlines = [ReqReportInline]

    @admin.display(description='Titles')
    def title_list(self, obj):
        titles = set()
        for report in obj.reports.prefetch_related('report_titles__title').all():
            for rt in report.report_titles.all():
                titles.add(rt.title.name)
        return ', '.join(sorted(titles)) or '—'

    @admin.display(description='Report count')
    def report_count(self, obj):
        return obj.reports.count()


@admin.register(ReqReportTitle)
class ReqReportTitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'req_report', 'title')
    list_filter = ('title',)
    search_fields = ('title__name',)


@admin.register(ReqReport)
class ReqReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'req_report_sub_main',
                    'user', 'date_from', 'date_to')
    list_filter = ('req_report_sub_main__sub_main',)
    search_fields = ('user__email', 'user__full_name')
    raw_id_fields = ('user',)
    inlines = [ReqReportTitleInline]


@admin.register(Info)
class InfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'attribute', 'sub_main', 'value',
                    'confirmed', 'user', 'created_at')
    list_filter = ('confirmed', 'attribute__title', 'attribute', 'sub_main')
    search_fields = ('value', 'user__email', 'user__full_name',
                     'attribute__label', 'sub_main__name')
    list_editable = ('confirmed',)
    raw_id_fields = ('user', 'sub_main')


# ── Audit Log ─────────────────────────────────────────────────────────────────

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'timestamp', 'user', 'action',
                    'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name')
    search_fields = ('user__email', 'ip_address', 'model_name')
    readonly_fields = ('user', 'action', 'model_name',
                       'object_id', 'details', 'ip_address', 'timestamp')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
