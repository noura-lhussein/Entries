from django.contrib import admin
from django.contrib.gis import admin as gis_admin

from .models import Community, District, Governorate, SubDistrict


@gis_admin.register(Governorate)
class GovernorateAdmin(gis_admin.GISModelAdmin):
    list_display = ("name_ar", "name_en", "code", "is_active", "deleted")
    list_filter = ("is_active", "deleted")
    search_fields = ("name_ar", "name_en", "code")


@gis_admin.register(District)
class DistrictAdmin(gis_admin.GISModelAdmin):
    list_display = ("name_ar", "name_en", "code",
                    "governorate", "is_active", "deleted")
    list_filter = ("governorate", "is_active", "deleted")
    search_fields = ("name_ar", "name_en", "code")
    autocomplete_fields = ("governorate",)


@gis_admin.register(SubDistrict)
class SubDistrictAdmin(gis_admin.GISModelAdmin):
    list_display = ("name_ar", "name_en", "code",
                    "district", "is_active", "deleted")
    list_filter = ("district__governorate", "is_active", "deleted")
    search_fields = ("name_ar", "name_en", "code")
    autocomplete_fields = ("district",)


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = (
        "name_ar", "name_en", "code", "latitude", "longitude",
        "subdistrict", "is_active", "deleted",
    )
    list_filter = ("subdistrict__district__governorate",
                   "is_active", "deleted")
    search_fields = ("name_ar", "name_en", "code")
    autocomplete_fields = ("subdistrict",)
