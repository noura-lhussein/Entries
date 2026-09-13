from __future__ import annotations

from django.db import models


class RainfallBasin(models.Model):
    slug = models.SlugField(max_length=32, unique=True)
    name_en = models.CharField(max_length=128)
    name_ar = models.CharField(max_length=128)
    area_km2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['name_en']

    def __str__(self) -> str:
        return self.name_en


class RainfallStation(models.Model):
    basin = models.ForeignKey(RainfallBasin, on_delete=models.CASCADE, related_name='stations')
    name = models.CharField(max_length=128)
    governorate = models.CharField(max_length=64, blank=True)
    utm_x = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    utm_y = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['basin', 'name'], name='uniq_rainfall_station_per_basin'),
        ]

    def __str__(self) -> str:
        return self.name


class RainfallObservation(models.Model):
    station = models.ForeignKey(RainfallStation, on_delete=models.CASCADE, related_name='observations')
    observation_date = models.DateField(db_index=True)
    precipitation_mm = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-observation_date']
        constraints = [
            models.UniqueConstraint(
                fields=['station', 'observation_date'],
                name='uniq_rainfall_observation',
            ),
        ]
        indexes = [
            models.Index(fields=['observation_date', 'station']),
        ]

    def __str__(self) -> str:
        return f'{self.station.name} @ {self.observation_date}'


class Dam(models.Model):
    name = models.CharField(max_length=128)
    governorate = models.CharField(max_length=64, blank=True)
    utm_x = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    utm_y = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status_note = models.CharField(max_length=128, blank=True)
    dam_type = models.CharField(max_length=128, blank=True)
    height_m = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    length_m = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_storage_mcm = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    dead_storage_mcm = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    built_year = models.PositiveSmallIntegerField(null=True, blank=True)
    purpose = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['governorate', 'name']
        constraints = [
            models.UniqueConstraint(fields=['governorate', 'name'], name='uniq_dam_per_governorate'),
        ]

    def __str__(self) -> str:
        return self.name


class DamStorageReading(models.Model):
    dam = models.ForeignKey(Dam, on_delete=models.CASCADE, related_name='readings')
    reading_date = models.DateField(db_index=True)
    storage_mcm = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-reading_date']
        constraints = [
            models.UniqueConstraint(
                fields=['dam', 'reading_date'],
                name='uniq_dam_storage_reading',
            ),
        ]
        indexes = [
            models.Index(fields=['reading_date', 'dam']),
        ]

    def __str__(self) -> str:
        return f'{self.dam.name} @ {self.reading_date}'


class EuphratesCascadeReading(models.Model):
    """Daily hydraulic and generation readings for the Euphrates cascade dams."""

    reading_date = models.DateField(unique=True, db_index=True)
    inflow_jarabulus = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    tishreen_level_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    tishreen_storage_mcm = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    tishreen_outflow = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    tishreen_generation_mwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    furat_level_m = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    furat_storage_mcm = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    furat_outflow = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    furat_generation_mwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    kadiran_outflow = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    kadiran_generation_mwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    al_jalab_discharge = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    total_generation_mwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    report_label = models.CharField(max_length=255, blank=True)
    source_file = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-reading_date']

    def __str__(self) -> str:
        return f'Euphrates cascade @ {self.reading_date}'


class DrinkingWaterStation(models.Model):
    tei_id = models.CharField(max_length=64, blank=True)
    org_unit = models.CharField(max_length=128, blank=True)
    station_code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    governorate = models.CharField(max_length=128, blank=True, db_index=True)
    district = models.CharField(max_length=128, blank=True)
    subdistrict = models.CharField(max_length=128, blank=True)
    community = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    enrollment_date = models.DateField(null=True, blank=True)
    incident_date = models.DateField(null=True, blank=True)
    is_operational = models.BooleanField(null=True, blank=True, db_index=True)
    is_boosting_station = models.BooleanField(null=True, blank=True, db_index=True)
    is_well_station = models.BooleanField(null=True, blank=True, db_index=True)
    is_filtration_station = models.BooleanField(null=True, blank=True, db_index=True)
    needs_solar_power = models.BooleanField(null=True, blank=True, db_index=True)
    has_grid_power = models.BooleanField(null=True, blank=True, db_index=True)
    non_operational_reason = models.CharField(max_length=64, blank=True, db_index=True)
    building_condition = models.CharField(max_length=8, blank=True, db_index=True)
    safety_procedures = models.CharField(max_length=16, blank=True, db_index=True)
    previously_rehabilitated = models.BooleanField(null=True, blank=True, db_index=True)
    rehabilitation_type = models.CharField(max_length=16, blank=True)
    has_water_hammer_protection = models.BooleanField(null=True, blank=True, db_index=True)
    water_hammer_efficiency = models.CharField(max_length=8, blank=True)
    has_public_grid_supply = models.BooleanField(null=True, blank=True, db_index=True)
    grid_connection_working = models.BooleanField(null=True, blank=True, db_index=True)
    electrical_connection_efficiency = models.CharField(max_length=8, blank=True, db_index=True)
    electrical_panel_efficiency = models.CharField(max_length=8, blank=True)
    transformer_efficiency = models.CharField(max_length=8, blank=True)
    solar_power_available = models.BooleanField(null=True, blank=True, db_index=True)
    solar_system_efficiency = models.CharField(max_length=8, blank=True)
    needs_solar_installation = models.BooleanField(null=True, blank=True, db_index=True)
    generator_available = models.BooleanField(null=True, blank=True, db_index=True)
    alternative_power_source = models.BooleanField(null=True, blank=True, db_index=True)
    solar_space_available = models.BooleanField(null=True, blank=True, db_index=True)
    grid_power_productivity = models.CharField(max_length=16, blank=True)
    solar_power_productivity = models.CharField(max_length=16, blank=True)
    is_water_analyzed = models.BooleanField(null=True, blank=True, db_index=True)
    lab_equipment_status = models.CharField(max_length=16, blank=True, db_index=True)
    has_water_tanks = models.BooleanField(null=True, blank=True, db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        ordering = ['governorate', 'name']
        indexes = [
            models.Index(fields=['governorate', 'district']),
        ]

    def __str__(self) -> str:
        return self.name


from .operational_models import (  # noqa: E402, F401
    Alert,
    DailyMetric,
    DailyReport,
    KpiDailySnapshot,
    OperationalTarget,
)
