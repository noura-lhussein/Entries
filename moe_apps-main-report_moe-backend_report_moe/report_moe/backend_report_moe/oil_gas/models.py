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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='oil_gas_reports',
    )

    class Meta:
        ordering = ['-report_date']

    def __str__(self) -> str:
        return f'Petroleum report {self.report_date}'


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
                name='oil_gas_unique_metric_per_report',
            ),
        ]
        indexes = [
            models.Index(fields=['metric_key', 'report']),
        ]

    def __str__(self) -> str:
        dim = f'[{self.dimension}]' if self.dimension else ''
        return f'{self.metric_key}{dim}={self.value}'


from .operational_models import (  # noqa: E402, F401
    Alert,
    DailyProduction,
    DataSource,
    Export,
    Facility,
    Field,
    FuelInventory,
    KpiDailySnapshot,
    OperationalTarget,
    Pipeline,
    PowerGasRequirement,
    PowerGasSupply,
    ProductionLoss,
    Refinery,
    RefineryDailyOutput,
    Well,
)
