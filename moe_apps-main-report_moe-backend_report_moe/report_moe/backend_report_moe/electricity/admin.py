from __future__ import annotations

from django.contrib import admin

from .models import (
    DailyMetric,
    DailyReport,
    FuelTankReading,
    GenerationIncident,
    GenerationUnitReading,
    GovernorateLoad,
    GridLineIncident,
    HydroDamReading,
)


class DailyMetricInline(admin.TabularInline):
    model = DailyMetric
    extra = 0
    fields = ['metric_key', 'dimension', 'value', 'unit']


class GovernorateLoadInline(admin.TabularInline):
    model = GovernorateLoad
    extra = 0
    fields = ['governorate_code', 'consumed_mw', 'allocated_mw']


class HydroDamReadingInline(admin.TabularInline):
    model = HydroDamReading
    extra = 0
    fields = ['dam_code', 'front_level_m', 'back_level_m', 'generation_mwh', 'outflow_m3s']


class GenerationIncidentInline(admin.TabularInline):
    model = GenerationIncident
    extra = 0
    fields = ['event_time', 'description_ar']


class GridLineIncidentInline(admin.TabularInline):
    model = GridLineIncident
    extra = 0
    fields = ['line_name', 'voltage_kv', 'action_ar']


class FuelTankReadingInline(admin.TabularInline):
    model = FuelTankReading
    extra = 0
    fields = ['station_code', 'current_tons', 'max_capacity_tons']


class GenerationUnitReadingInline(admin.TabularInline):
    model = GenerationUnitReading
    extra = 0
    fields = ['plant_code', 'unit_code', 'nominal_mw', 'available_mw', 'generation_mwh_24h', 'status']


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'status', 'source_file', 'updated_at']
    list_filter = ['status']
    search_fields = ['notes_ar', 'notes_en', 'source_file']
    date_hierarchy = 'report_date'
    inlines = [
        DailyMetricInline,
        GovernorateLoadInline,
        HydroDamReadingInline,
        FuelTankReadingInline,
        GenerationUnitReadingInline,
        GenerationIncidentInline,
        GridLineIncidentInline,
    ]
