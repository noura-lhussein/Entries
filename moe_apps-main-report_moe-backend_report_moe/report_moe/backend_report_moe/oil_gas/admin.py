from __future__ import annotations

from django.contrib import admin, messages

from .alert_engine import evaluate_alerts
from .models import (
    Alert,
    DailyMetric,
    DailyProduction,
    DailyReport,
    Export,
    FuelInventory,
    KpiDailySnapshot,
    OperationalTarget,
    PowerGasRequirement,
    PowerGasSupply,
    ProductionLoss,
    RefineryDailyOutput,
)
from .snapshot_builder import build_kpi_snapshot


def rebuild_snapshots(modeladmin, request, queryset):
    rebuilt = 0
    for obj in queryset:
        snapshot_date = getattr(obj, 'snapshot_date', None) or getattr(obj, 'production_date', None)
        if not snapshot_date:
            continue
        snapshot = build_kpi_snapshot(snapshot_date)
        evaluate_alerts(snapshot_date, snapshot)
        rebuilt += 1
    modeladmin.message_user(request, f'Rebuilt {rebuilt} KPI snapshot(s).', messages.SUCCESS)


rebuild_snapshots.short_description = 'Rebuild KPI snapshot + alerts for selected date(s)'


class DailyMetricInline(admin.TabularInline):
    model = DailyMetric
    extra = 0
    fields = ['metric_key', 'dimension', 'value', 'unit']


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'status', 'updated_at', 'created_by']
    list_filter = ['status']
    search_fields = ['notes_ar', 'notes_en']
    date_hierarchy = 'report_date'
    inlines = [DailyMetricInline]
    actions = [rebuild_snapshots]


@admin.register(DailyProduction)
class DailyProductionAdmin(admin.ModelAdmin):
    list_display = ['field', 'production_date', 'crude_oil_bbl', 'natural_gas_mmscf', 'condensate_bbl']
    list_filter = ['production_date', 'field__field_type']
    search_fields = ['field__code', 'field__name_en', 'field__name_ar']
    date_hierarchy = 'production_date'
    actions = [rebuild_snapshots]


@admin.register(ProductionLoss)
class ProductionLossAdmin(admin.ModelAdmin):
    list_display = ['field', 'loss_date', 'loss_type', 'estimated_loss_bbl', 'severity']
    list_filter = ['severity', 'loss_type']
    search_fields = ['field__code', 'reason']
    date_hierarchy = 'loss_date'


@admin.register(RefineryDailyOutput)
class RefineryDailyOutputAdmin(admin.ModelAdmin):
    list_display = ['refinery', 'production_date', 'gasoline_ton', 'diesel_ton', 'fuel_oil_ton']
    date_hierarchy = 'production_date'
    actions = [rebuild_snapshots]


@admin.register(FuelInventory)
class FuelInventoryAdmin(admin.ModelAdmin):
    list_display = ['facility', 'inventory_date', 'fuel_type', 'current_volume', 'max_capacity']
    list_filter = ['fuel_type']
    date_hierarchy = 'inventory_date'
    actions = [rebuild_snapshots]


@admin.register(OperationalTarget)
class OperationalTargetAdmin(admin.ModelAdmin):
    list_display = [
        'metric_key',
        'scope_type',
        'scope_code',
        'period_type',
        'period_start',
        'target_value',
        'unit',
    ]
    list_filter = ['metric_key', 'scope_type', 'period_type']
    search_fields = ['scope_code', 'label_en', 'label_ar', 'notes']
    date_hierarchy = 'period_start'


@admin.register(PowerGasSupply)
class PowerGasSupplyAdmin(admin.ModelAdmin):
    list_display = ['supply_date', 'facility', 'supplied_mmscf']
    date_hierarchy = 'supply_date'


@admin.register(PowerGasRequirement)
class PowerGasRequirementAdmin(admin.ModelAdmin):
    list_display = ['requirement_date', 'facility', 'required_mmscf']
    date_hierarchy = 'requirement_date'


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    list_display = ['export_date', 'destination_country', 'crude_bbl', 'revenue_usd']
    date_hierarchy = 'export_date'
    actions = [rebuild_snapshots]


@admin.register(KpiDailySnapshot)
class KpiDailySnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'snapshot_date',
        'total_oil_production_bpd',
        'total_gas_production_mmscf',
        'total_export_bbl',
        'export_revenue_usd',
        'active_alerts_count',
        'source',
        'built_at',
    ]
    date_hierarchy = 'snapshot_date'
    actions = [rebuild_snapshots]
    readonly_fields = [
        'snapshot_date',
        'total_oil_production_bpd',
        'total_gas_production_mmscf',
        'refinery_utilization_percent',
        'gasoline_stock_days',
        'diesel_stock_days',
        'gas_supply_to_power_percent',
        'total_export_bbl',
        'export_revenue_usd',
        'total_losses_bbl',
        'target_total_oil_production_bpd',
        'target_total_gas_production_mmscf',
        'target_total_export_bbl',
        'target_export_revenue_usd',
        'target_gasoline_stock_days',
        'target_gas_supply_to_power_percent',
        'active_alerts_count',
        'source',
        'built_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['alert_time', 'severity', 'alert_type', 'title_en', 'snapshot_date', 'is_resolved']
    list_filter = ['severity', 'is_resolved', 'alert_type', 'source_module']
    search_fields = ['title_en', 'title_ar', 'description']
    list_editable = ['is_resolved']
    date_hierarchy = 'alert_time'
