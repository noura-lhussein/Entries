from django.contrib import admin

from .models import (
    Alert,
    DailyMetric,
    DailyReport,
    DamStorageReading,
    EuphratesCascadeReading,
    KpiDailySnapshot,
    OperationalTarget,
    RainfallObservation,
)

# Master catalogs (Dam, RainfallBasin/Station, DrinkingWaterStation) owned by report_moe.
admin.site.register(RainfallObservation)
admin.site.register(DamStorageReading)
admin.site.register(EuphratesCascadeReading)
admin.site.register(DailyReport)
admin.site.register(DailyMetric)
admin.site.register(OperationalTarget)
admin.site.register(Alert)
admin.site.register(KpiDailySnapshot)
