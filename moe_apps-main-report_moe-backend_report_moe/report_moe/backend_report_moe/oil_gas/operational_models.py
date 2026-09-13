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


class Field(models.Model):
    class FieldType(models.TextChoices):
        OIL = 'oil', 'Oil'
        GAS = 'gas', 'Gas'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SHUTDOWN = 'shutdown', 'Shutdown'
        MAINTENANCE = 'maintenance', 'Maintenance'

    code = models.CharField(max_length=50, unique=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200)
    field_type = models.CharField(max_length=20, choices=FieldType.choices)
    governorate = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    operator_company = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    design_capacity_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en


class Well(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='wells')
    well_code = models.CharField(max_length=100)
    name_ar = models.CharField(max_length=200, blank=True)
    name_en = models.CharField(max_length=200, blank=True)
    well_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, blank=True)
    production_capacity_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['field', 'well_code'], name='oil_gas_unique_well_code'),
        ]
        ordering = ['well_code']

    def __str__(self) -> str:
        return self.well_code

    @property
    def label_ar(self) -> str:
        return self.name_ar or self.well_code

    @property
    def label_en(self) -> str:
        return self.name_en or self.well_code


class DailyProduction(AuditedModel):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='daily_production')
    production_date = models.DateField(db_index=True)
    crude_oil_bbl = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    natural_gas_mmscf = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    condensate_bbl = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    water_cut_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    operating_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['field', 'production_date'],
                name='oil_gas_unique_field_production_date',
            ),
        ]
        ordering = ['-production_date']

    def __str__(self) -> str:
        return f'{self.field.code} {self.production_date}'


class ProductionLoss(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='production_losses')
    loss_date = models.DateField(db_index=True)
    loss_type = models.CharField(max_length=100)
    estimated_loss_bbl = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reason = models.TextField(blank=True)
    severity = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-loss_date']


REFINERY_NAME_EN: dict[str, str] = {
    'Banias Refinery': 'Banias Refinery',
    'Homs Refinery': 'Homs Refinery',
    'مصفاة بانياس': 'Banias Refinery',
    'مصفاة حمص': 'Homs Refinery',
}


class Refinery(models.Model):
    class Status(models.TextChoices):
        OPERATING = 'operating', 'Operating'
        STOPPED = 'stopped', 'Stopped'
        MAINTENANCE = 'maintenance', 'Maintenance'

    refinery_name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    governorate = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPERATING)
    design_capacity_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'refineries'
        ordering = ['refinery_name']

    def __str__(self) -> str:
        return self.refinery_name

    @property
    def label_ar(self) -> str:
        if self.name_ar:
            return self.name_ar
        if self.refinery_name.startswith('مصفاة '):
            return self.refinery_name.removeprefix('مصفاة ')
        return self.refinery_name

    def alert_title_ar(self) -> str:
        if self.refinery_name.startswith('مصفاة '):
            return f'توقف {self.refinery_name}'
        return f'توقف مصفاة {self.label_ar}'


    def alert_title_en(self) -> str:
        label = REFINERY_NAME_EN.get(self.refinery_name, self.refinery_name)
        return f'Refinery outage: {label}'


class RefineryDailyOutput(AuditedModel):
    refinery = models.ForeignKey(Refinery, on_delete=models.CASCADE, related_name='daily_outputs')
    production_date = models.DateField(db_index=True)
    gasoline_ton = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    diesel_ton = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    fuel_oil_ton = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    lpg_ton = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['refinery', 'production_date'],
                name='oil_gas_unique_refinery_output_date',
            ),
        ]
        ordering = ['-production_date']


class Facility(models.Model):
    class Sector(models.TextChoices):
        OIL_GAS = 'oil-gas', 'Petroleum'
        ELECTRICITY = 'electricity', 'Electricity'

    class FacilityType(models.TextChoices):
        STORAGE_DEPOT = 'storage_depot', 'Storage depot'
        FUEL_STATION = 'fuel_station', 'Fuel station'
        POWER_PLANT = 'power_plant', 'Power plant'
        SUBSTATION = 'substation', 'Substation'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        MAINTENANCE = 'maintenance', 'Maintenance'

    code = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    facility_type = models.CharField(max_length=50, choices=FacilityType.choices)
    sector = models.CharField(max_length=20, choices=Sector.choices, default=Sector.OIL_GAS)
    location = models.CharField(max_length=200, blank=True)
    governorate = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        verbose_name_plural = 'facilities'
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en


class FuelInventory(AuditedModel):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='inventories')
    inventory_date = models.DateField(db_index=True)
    fuel_type = models.CharField(max_length=50)
    current_volume = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    max_capacity = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'fuel inventories'
        constraints = [
            models.UniqueConstraint(
                fields=['facility', 'inventory_date', 'fuel_type'],
                name='oil_gas_unique_fuel_inventory',
            ),
        ]
        ordering = ['-inventory_date']


class Pipeline(models.Model):
    class Status(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        DEGRADED = 'degraded', 'Degraded'
        SHUTDOWN = 'shutdown', 'Shutdown'

    name = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    source_location = models.CharField(max_length=200, blank=True)
    destination_location = models.CharField(max_length=200, blank=True)
    length_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    source_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    source_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    dest_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    dest_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    # Optional full LineString as [[lng, lat], ...] (GeoJSON order). Falls back to source→dest.
    path_coordinates = models.JSONField(default=list, blank=True)
    design_capacity_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NORMAL)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def label_ar(self) -> str:
        return self.name_ar or self.name


class PowerGasSupply(models.Model):
    supply_date = models.DateField(db_index=True)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='power_gas_supplies',
    )
    supplied_mmscf = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['supply_date', 'facility'],
                name='oil_gas_unique_power_gas_supply',
            ),
        ]
        ordering = ['-supply_date']


class PowerGasRequirement(models.Model):
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='power_gas_requirements',
    )
    requirement_date = models.DateField(db_index=True)
    required_mmscf = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['facility', 'requirement_date'],
                name='oil_gas_unique_power_gas_requirement',
            ),
        ]
        ordering = ['-requirement_date']


class Export(AuditedModel):
    export_date = models.DateField(db_index=True)
    destination_country = models.CharField(max_length=100, blank=True)
    crude_bbl = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    revenue_usd = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        ordering = ['-export_date']


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


class OperationalTarget(models.Model):
    class ScopeType(models.TextChoices):
        NATIONAL = 'national', 'National'
        FIELD = 'field', 'Field'
        REFINERY = 'refinery', 'Refinery'
        FACILITY = 'facility', 'Facility'

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
                name='oil_gas_unique_operational_target',
            ),
        ]
        indexes = [
            models.Index(fields=['scope_type', 'scope_code', 'period_start']),
        ]

    def __str__(self) -> str:
        scope = self.scope_code or self.scope_type
        return f'{self.metric_key} @ {scope} ({self.period_start})'


class KpiDailySnapshot(models.Model):
    snapshot_date = models.DateField(primary_key=True)
    total_oil_production_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_gas_production_mmscf = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    refinery_utilization_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gasoline_stock_days = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diesel_stock_days = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    gas_supply_to_power_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_export_bbl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    export_revenue_usd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    total_losses_bbl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_total_oil_production_bpd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_total_gas_production_mmscf = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_total_export_bbl = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_export_revenue_usd = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    target_gasoline_stock_days = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    target_gas_supply_to_power_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    active_alerts_count = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=20, default='computed')
    built_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self) -> str:
        return str(self.snapshot_date)
