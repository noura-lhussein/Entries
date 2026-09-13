from __future__ import annotations

from django.conf import settings
from django.db import models


class DailyReport(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    report_date = models.DateField(unique=True, db_index=True)
    reference_hour = models.TimeField(null=True, blank=True)
    peak_generation_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    notes_ar = models.TextField(blank=True)
    notes_en = models.TextField(blank=True)
    maintenance_groups_ar = models.TextField(blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='electricity_reports',
    )

    class Meta:
        ordering = ['-report_date']

    def __str__(self) -> str:
        return f'Electricity report {self.report_date}'


class DailyMetric(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='metrics')
    metric_key = models.CharField(max_length=64, db_index=True)
    dimension = models.CharField(max_length=32, blank=True, default='')
    value = models.DecimalField(max_digits=16, decimal_places=4)
    unit = models.CharField(max_length=24, blank=True)

    class Meta:
        ordering = ['metric_key', 'dimension']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'metric_key', 'dimension'],
                name='electricity_unique_metric_per_report',
            ),
        ]
        indexes = [
            models.Index(fields=['metric_key', 'report']),
        ]

    def __str__(self) -> str:
        dim = f'[{self.dimension}]' if self.dimension else ''
        return f'{self.metric_key}{dim}={self.value}'


class GovernorateLoad(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='governorate_loads')
    governorate_code = models.CharField(max_length=32, db_index=True)
    consumed_mw = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    allocated_mw = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['governorate_code']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'governorate_code'],
                name='electricity_unique_gov_load_per_report',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.governorate_code} @ {self.report.report_date}'


class HydroDamReading(models.Model):
    class DamCode(models.TextChoices):
        THAWRA = 'thawra', 'Thawra (Revolution)'
        EUPHRATES = 'euphrates', 'Euphrates (Thawra)'
        TISHREEN = 'tishreen', 'Tishreen'

    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='hydro_readings')
    dam_code = models.CharField(max_length=32, choices=DamCode.choices)
    front_level_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    back_level_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    generation_mwh = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    outflow_m3s = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    inflow_m3s = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_m3s = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['dam_code']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'dam_code'],
                name='electricity_unique_hydro_per_report',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.dam_code} @ {self.report.report_date}'


class GenerationIncident(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='generation_incidents')
    event_time = models.CharField(max_length=64, blank=True)
    description_ar = models.TextField()
    description_en = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return f'Gen incident @ {self.report.report_date}'


class GridLineIncident(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='grid_incidents')
    line_name = models.CharField(max_length=255)
    voltage_kv = models.PositiveSmallIntegerField(null=True, blank=True)
    action_ar = models.TextField()
    action_en = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return f'{self.line_name} @ {self.report.report_date}'


class FuelTankReading(models.Model):
    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='fuel_tank_readings')
    station_code = models.CharField(max_length=32, db_index=True)
    current_tons = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_capacity_tons = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['station_code']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'station_code'],
                name='electricity_unique_fuel_tank_per_report',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.station_code} @ {self.report.report_date}'


class GenerationUnitReading(models.Model):
    class UnitStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        MAINTENANCE = 'maintenance', 'Maintenance'
        OUTAGE = 'outage', 'Outage'
        STANDBY = 'standby', 'Standby'

    report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name='generation_unit_readings')
    plant_code = models.CharField(max_length=32, db_index=True)
    unit_code = models.CharField(max_length=32, blank=True, default='')
    nominal_mw = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_mw = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    generation_mwh_24h = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=16, choices=UnitStatus.choices, default=UnitStatus.ACTIVE)

    class Meta:
        ordering = ['plant_code', 'unit_code']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'plant_code', 'unit_code'],
                name='electricity_unique_generation_unit_per_report',
            ),
        ]

    def __str__(self) -> str:
        label = self.unit_code or 'plant'
        return f'{self.plant_code}/{label} @ {self.report.report_date}'


from .operational_models import (  # noqa: E402, F401
    Alert,
    DailyDemand,
    DailyGeneration,
    DataSource,
    FuelTankStation,
    GridOutage,
    HydroDam,
    KpiDailySnapshot,
    LoadGovernorate,
    OperationalTarget,
    PowerPlant,
    Substation,
    TransmissionLine,
)
