"""Geology planning & monitoring models (mirror water / electricity ops)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class DailyReport(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    report_date = models.DateField(unique=True, db_index=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    notes_ar = models.TextField(blank=True)
    notes_en = models.TextField(blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='geology_reports',
    )

    class Meta:
        ordering = ['-report_date']

    def __str__(self) -> str:
        return f'Geology report {self.report_date}'


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
                name='geology_unique_metric_per_report',
            ),
        ]
        indexes = [
            models.Index(fields=['metric_key', 'report']),
        ]

    def __str__(self) -> str:
        dim = f'[{self.dimension}]' if self.dimension else ''
        return f'{self.metric_key}{dim}={self.value}'


class OperationalTarget(models.Model):
    class ScopeType(models.TextChoices):
        NATIONAL = 'national', 'National'
        GOVERNORATE = 'governorate', 'Governorate'
        SITE = 'site', 'Site'

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
                name='geology_unique_operational_target',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.metric_key} @ {self.period_start}'


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
    mapped_units_count = models.PositiveIntegerField(default=0)
    active_alerts_count = models.PositiveIntegerField(default=0)
    layers_count = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=20, default='computed')
    built_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-snapshot_date']

    def __str__(self) -> str:
        return str(self.snapshot_date)


class OreProduct(models.Model):
    """Ore/mineral product catalog (reference data).

    Table lives in the moeds schema but is report_moe-owned per
    enforce_single_writer.sql — moeds only reads it (see
    geology/info_dashboard.py). Do not add any write path to this model
    in moeds beyond the initial seed migration.
    """

    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True, default='')
    # ذاتي / معهّد — operating mode, not a measurement unit
    production_type = models.CharField(max_length=64, blank=True, default='')
    # طن / م3 — actual quantity unit
    unit = models.CharField(max_length=64, blank=True, default='')
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        bits = [self.name_ar]
        if self.production_type:
            bits.append(self.production_type)
        if self.unit:
            bits.append(self.unit)
        return ' / '.join(bits)
