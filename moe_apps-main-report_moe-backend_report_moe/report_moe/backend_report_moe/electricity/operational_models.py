from __future__ import annotations

from django.conf import settings
from django.db import models


class DataSource(models.TextChoices):
    MANUAL = 'manual', 'Manual'
    API = 'api', 'API'
    IMPORT = 'import', 'Import'
    SEED = 'seed', 'Seed'


class AuditedModel(models.Model):
    source = models.CharField(max_length=16, choices=DataSource.choices, default=DataSource.MANUAL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updates',
    )

    class Meta:
        abstract = True


class FuelTankStation(models.Model):
    """Static fuel-tank station catalog (names/capacity stay out of Info)."""

    code = models.CharField(max_length=32, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    max_capacity_tons = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['name_ar', 'id']

    def __str__(self) -> str:
        return self.name_ar or self.code


class HydroDam(models.Model):
    """Static hydro dam catalog for daily dam readings (names stay out of Info)."""

    code = models.CharField(max_length=32, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)

    class Meta:
        ordering = ['name_ar', 'id']

    def __str__(self) -> str:
        return self.name_ar or self.code


class LoadGovernorate(models.Model):
    """Static governorate catalog for daily load rows (names stay out of Info)."""

    code = models.CharField(max_length=32, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)

    class Meta:
        ordering = ['name_ar', 'id']

    def __str__(self) -> str:
        return self.name_ar or self.code


class PowerPlant(models.Model):
    class PlantType(models.TextChoices):
        THERMAL = 'thermal', 'Thermal'
        HYDRO = 'hydro', 'Hydro'
        SOLAR = 'solar', 'Solar'
        WIND = 'wind', 'Wind'

    class FuelType(models.TextChoices):
        GAS = 'gas', 'Natural gas'
        HFO = 'hfo', 'Heavy fuel oil'
        DUAL = 'dual', 'Dual fuel'
        NONE = 'none', 'None'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        MAINTENANCE = 'maintenance', 'Maintenance'
        SHUTDOWN = 'shutdown', 'Shutdown'

    code = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    plant_type = models.CharField(max_length=20, choices=PlantType.choices)
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices, default=FuelType.NONE)
    governorate = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    operator_company = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    installed_capacity_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en


class Substation(models.Model):
    class Role(models.TextChoices):
        TRANSMISSION = 'transmission', 'Transmission'
        DISTRIBUTION = 'distribution', 'Distribution'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        MAINTENANCE = 'maintenance', 'Maintenance'
        SHUTDOWN = 'shutdown', 'Shutdown'

    code = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TRANSMISSION)
    voltage_kv = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    governorate = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en


class TransmissionLine(models.Model):
    class Status(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        DEGRADED = 'degraded', 'Degraded'
        SHUTDOWN = 'shutdown', 'Shutdown'

    name = models.CharField(max_length=200)
    source_location = models.CharField(max_length=200, blank=True)
    destination_location = models.CharField(max_length=200, blank=True)
    length_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    source_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    source_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    dest_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    dest_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    capacity_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    voltage_kv = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NORMAL)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class DailyGeneration(AuditedModel):
    plant = models.ForeignKey(PowerPlant, on_delete=models.CASCADE, related_name='daily_generation')
    report_date = models.DateField(db_index=True)
    gross_generation_mwh = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    peak_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    available_capacity_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    forced_outage_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['plant', 'report_date'],
                name='electricity_unique_plant_generation_date',
            ),
        ]
        ordering = ['-report_date']


class DailyDemand(AuditedModel):
    report_date = models.DateField(unique=True, db_index=True)
    peak_demand_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    energy_consumed_mwh = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ['-report_date']


class GridOutage(AuditedModel):
    report_date = models.DateField(db_index=True)
    governorate = models.CharField(max_length=100, blank=True)
    outage_type = models.CharField(max_length=50, default='distribution')
    duration_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customers_affected = models.PositiveIntegerField(default=0)
    severity = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-report_date']

class OperationalTarget(models.Model):
    class ScopeType(models.TextChoices):
        NATIONAL = 'national', 'National'
        PLANT = 'plant', 'Plant'
        GOVERNORATE = 'governorate', 'Governorate'

    class PeriodType(models.TextChoices):
        DAILY = 'daily', 'Daily'
        MONTHLY = 'monthly', 'Monthly'

    metric_key = models.CharField(max_length=64, db_index=True)
    scope_type = models.CharField(max_length=20, choices=ScopeType.choices, default=ScopeType.NATIONAL)
    scope_code = models.CharField(max_length=100, blank=True, default='')
    period_type = models.CharField(max_length=20, choices=PeriodType.choices, default=PeriodType.DAILY)
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(null=True, blank=True)
    target_value = models.DecimalField(max_digits=18, decimal_places=4)
    unit = models.CharField(max_length=24, blank=True)
    label_ar = models.CharField(max_length=200, blank=True)
    label_en = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_start', 'metric_key']
        constraints = [
            models.UniqueConstraint(
                fields=['metric_key', 'scope_type', 'scope_code', 'period_type', 'period_start'],
                name='electricity_unique_operational_target',
            ),
        ]


class Alert(models.Model):
    class Severity(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        WARNING = 'warning', 'Warning'
        INFO = 'info', 'Info'

    alert_time = models.DateTimeField(db_index=True)
    alert_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    source_module = models.CharField(max_length=100, blank=True)
    title_ar = models.CharField(max_length=500)
    title_en = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    snapshot_date = models.DateField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['-alert_time']

    def __str__(self) -> str:
        return self.title_en


class KpiDailySnapshot(models.Model):
    snapshot_date = models.DateField(primary_key=True)
    total_generation_mwh = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    peak_demand_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    supply_demand_gap_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    plant_availability_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    capacity_factor_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    renewable_share_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_installed_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    active_plants_count = models.PositiveIntegerField(default=0)
    target_total_generation_mwh = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_peak_demand_mw = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_plant_availability_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    active_alerts_count = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=20, default='computed')
    built_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self) -> str:
        return str(self.snapshot_date)
