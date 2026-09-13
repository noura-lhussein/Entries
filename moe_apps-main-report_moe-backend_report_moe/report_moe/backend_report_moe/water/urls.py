"""Water routes, mounted at `/api/v1/water/`.

Fixed segments precede the parameterised ones so `admin/registry`, `admin/lookups`
and the template paths are never read as resource slugs.
"""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "sector-info-dashboard/",
        views.sector_info_dashboard,
        name="water-sector-info-dashboard",
    ),
    path("rainfall/dashboard/", views.rainfall_dashboard, name="water-rainfall-dashboard"),
    path("dams/dashboard/", views.dams_dashboard, name="water-dams-dashboard"),
    path("dams/map-catalog/", views.dams_map_catalog, name="water-dams-map-catalog"),
    path(
        "dams/euphrates/dashboard/",
        views.euphrates_dashboard,
        name="water-euphrates-dashboard",
    ),
    path(
        "drinking-water/dashboard/",
        views.drinking_water_dashboard,
        name="water-drinking-dashboard",
    ),
    path(
        "drinking-water/stations/",
        views.drinking_water_stations,
        name="water-drinking-stations",
    ),
    path(
        "drinking-water/stations/<int:station_id>/report-facts/",
        views.drinking_water_station_report_facts,
        name="water-drinking-station-facts",
    ),
    path(
        "dams/<int:dam_id>/report-facts/",
        views.dam_report_facts,
        name="water-dam-facts",
    ),
    path(
        "rainfall/stations/<int:station_id>/report-facts/",
        views.rainfall_station_report_facts,
        name="water-rainfall-station-facts",
    ),
    path(
        "rainfall/basins/<int:basin_id>/report-facts/",
        views.rainfall_basin_report_facts,
        name="water-rainfall-basin-facts",
    ),
    path(
        "springs/<int:feature_id>/report-facts/",
        views.spring_report_facts,
        name="water-spring-facts",
    ),
    path(
        "lakes/<int:feature_id>/report-facts/",
        views.lake_report_facts,
        name="water-lake-facts",
    ),
    path(
        "rivers/<int:feature_id>/report-facts/",
        views.river_report_facts,
        name="water-river-facts",
    ),
    path(
        "streams/<int:feature_id>/report-facts/",
        views.stream_report_facts,
        name="water-stream-facts",
    ),
    path(
        "geology-units/<int:feature_id>/report-facts/",
        views.geology_unit_report_facts,
        name="water-geology-unit-facts",
    ),
    path("reports/export/", views.report_export, name="water-report-export"),
    path("admin/imports/status/", views.import_status, name="water-import-status"),
    path("admin/lookups/", views.lookups, name="water-lookups"),
    # Every import and clear route answers the same 410.
    path("admin/imports/rainfall/", views.import_moved, name="water-import-rainfall"),
    path(
        "admin/imports/rainfall/clear/",
        views.import_moved,
        name="water-clear-rainfall",
    ),
    path("admin/imports/dams/", views.import_moved, name="water-import-dams"),
    path("admin/imports/dams/clear/", views.import_moved, name="water-clear-dams"),
    path("admin/imports/euphrates/", views.import_moved, name="water-import-euphrates"),
    path(
        "admin/imports/euphrates/clear/",
        views.import_moved,
        name="water-clear-euphrates",
    ),
    path(
        "admin/imports/drinking-water/geo/",
        views.import_moved,
        name="water-import-drinking-geo",
    ),
    path(
        "admin/imports/drinking-water/survey/",
        views.import_moved,
        name="water-import-drinking-survey",
    ),
    path(
        "admin/exports/drinking-water/survey/",
        views.export_drinking_water_survey,
        name="water-export-drinking-survey",
    ),
    path("admin/templates/rainfall/", views.template_rainfall, name="water-tpl-rainfall"),
    path(
        "admin/templates/dams-metadata/",
        views.template_dams_metadata,
        name="water-tpl-dams-metadata",
    ),
    path(
        "admin/templates/dams-storage/",
        views.template_dams_storage,
        name="water-tpl-dams-storage",
    ),
    path(
        "admin/templates/euphrates/",
        views.template_euphrates,
        name="water-tpl-euphrates",
    ),
    path(
        "admin/templates/drinking-water-survey/",
        views.template_drinking_water_survey,
        name="water-tpl-drinking-survey",
    ),
    path("admin/daily/euphrates/", views.euphrates_daily, name="water-daily-euphrates"),
    path(
        "admin/daily/dam-storage/", views.dam_storage_daily, name="water-daily-dam-storage"
    ),
    path("admin/daily/rainfall/", views.rainfall_daily, name="water-daily-rainfall"),
    path(
        "admin/daily/drinking-water/",
        views.drinking_water_daily,
        name="water-daily-drinking",
    ),
    path("admin/registry/", views.admin_registry, name="water-admin-registry"),
    path("admin/<str:slug>/options/", views.admin_options, name="water-admin-options"),
    path("admin/<str:slug>/<str:pk>/", views.admin_detail, name="water-admin-detail"),
    path("admin/<str:slug>/", views.admin_list, name="water-admin-list"),
]
