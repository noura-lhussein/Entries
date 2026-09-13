from __future__ import annotations

from django.db import models
from django.utils import timezone
from projects.models import ProjectGovernorate, ProjectOrganization, Sector


class DatasetStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    ARCHIVED = 'archived', 'Archived'


DATASET_FORMAT_CHOICES = [
    'CSV',
    'XLSX',
    'GeoJSON',
    'SHP',
    'JSON',
    'KML',
    'KMZ',
    'ZIP',
    'PDF',
    'API',
    'DOCX',
]


class Dataset(models.Model):
    # view_count/download_count are usage counters, not core content — moeds bumps
    # them on every portal view/download. Matching column-level GRANT lives in
    # enforce_single_writer.sql; every other field on this model stays report_app-only.
    _moeds_writable_fields = frozenset({'view_count', 'download_count'})

    title_en = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    description_en = models.TextField(blank=True)
    description_ar = models.TextField(blank=True)
    organization = models.ForeignKey(
        ProjectOrganization,
        on_delete=models.PROTECT,
        related_name='datasets',
    )
    governorate = models.ForeignKey(
        ProjectGovernorate,
        on_delete=models.PROTECT,
        related_name='datasets',
    )
    sector = models.CharField(max_length=32, db_index=True)
    resource_formats = models.JSONField(default=list, blank=True)
    source_file = models.FileField(upload_to='datasets/files/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    data_start_date = models.DateField(null=True, blank=True)
    data_end_date = models.DateField(null=True, blank=True)
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=DatasetStatus.choices,
        default=DatasetStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return self.title_en

    @property
    def status_display(self) -> str:
        try:
            return DatasetStatus(self.status).label
        except ValueError:
            return self.status.replace('-', ' ').title()

    @property
    def has_download(self) -> bool:
        if self.external_url:
            return True
        if self.source_file:
            return True
        return self.resources.exists()

    @property
    def sector_display(self) -> str:
        try:
            return Sector(self.sector).label
        except ValueError:
            return self.sector.replace('-', ' ').title()


class DatasetResource(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='resources',
    )
    file = models.FileField(upload_to='datasets/files/')
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self) -> str:
        return self.file.name.rsplit('/', 1)[-1]
