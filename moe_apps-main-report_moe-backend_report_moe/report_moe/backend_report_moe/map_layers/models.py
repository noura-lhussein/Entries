"""ORM access to the two GIS feature tables.

These tables are created by RunSQL in this app's migrations, not by Django's model
layer, so `managed = False`: Django reads and writes rows but never issues DDL for
them. They carry a `geom` column that Django is not told about — geometry work goes
through raw SQL in `master_data/gis.py`, and these models cover the plain columns
that entity dropdowns need.

They used to live in `portal_mirror` as read-only mirrors, because report_moe reached
moeds' tables through a second connection. With one backend that indirection is gone.
"""

from __future__ import annotations

from django.db import models


class GisWaterFeature(models.Model):
    """Springs, lakes, rivers, streams and geology features share this table."""

    layer_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gis_water_feature'
        ordering = ['name', 'id']

    def __str__(self) -> str:
        return self.name or f'{self.layer_id}#{self.pk}'


class GisElectricityFeature(models.Model):
    """Voltage-level and renewable electricity features."""

    layer_id = models.CharField(max_length=64)
    name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'gis_electricity_feature'
        ordering = ['name', 'id']

    def __str__(self) -> str:
        return self.name or f'{self.layer_id}#{self.pk}'
