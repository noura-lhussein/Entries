"""Unified geographic hierarchy: Governorate → District → SubDistrict → Community."""

from django.conf import settings
from django.contrib.gis.db import models


class SoftDeleteMixin(models.Model):
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
    )

    class Meta:
        abstract = True


class LocationBase(SoftDeleteMixin):
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    code = models.CharField(max_length=20, unique=True, db_index=True)
    uid = models.UUIDField(unique=True, db_index=True)
    geom = models.MultiPolygonField(srid=4326, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    @property
    def display_name(self):
        return self.name_ar or self.name_en

    def __str__(self):
        return self.display_name


class Governorate(LocationBase):
    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name = "Governorate"
        verbose_name_plural = "Governorates"


class District(LocationBase):
    governorate = models.ForeignKey(
        Governorate,
        on_delete=models.PROTECT,
        related_name="districts",
    )

    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name = "District"
        verbose_name_plural = "Districts"


class SubDistrict(LocationBase):
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="subdistricts",
    )

    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name = "Sub-district"
        verbose_name_plural = "Sub-districts"


class Community(SoftDeleteMixin):
    subdistrict = models.ForeignKey(
        SubDistrict,
        on_delete=models.PROTECT,
        related_name="communities",
    )
    name_ar = models.CharField(max_length=255)
    name_en = models.CharField(max_length=255, blank=True, default="")
    code = models.CharField(max_length=20, blank=True,
                            default="", db_index=True)
    uid = models.UUIDField(null=True, blank=True, unique=True, db_index=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name_ar", "id"]
        verbose_name = "Community"
        verbose_name_plural = "Communities"

    @property
    def display_name(self):
        return self.name_ar or self.name_en

    def __str__(self):
        return self.display_name
