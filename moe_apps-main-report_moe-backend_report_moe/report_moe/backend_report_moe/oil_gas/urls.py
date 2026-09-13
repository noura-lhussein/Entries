"""Oil & gas routes, mounted at `/api/v1/oil-gas/`.

Fixed segments precede the parameterised ones: `targets/catalog`, `targets/compare`
and friends must not be read as a target id, and `admin/registry` not as a slug.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="oilgas-dashboard"),
    path("trends/<str:metric_key>/", views.trend, name="oilgas-trend"),
    path("report-dates/", views.report_dates, name="oilgas-report-dates"),
    path("reports/", views.report_list, name="oilgas-reports"),
    path("reports/detail/", views.report_detail, name="oilgas-report-detail"),
    path("reports/export/", views.report_export, name="oilgas-report-export"),
    path("reports/template/", views.report_template, name="oilgas-report-template"),
    path("reports/import/", views.report_import, name="oilgas-report-import"),
    path("reports/upsert/", views.report_upsert, name="oilgas-report-upsert"),
    path(
        "map-layers/<str:layer_id>/geojson/",
        views.map_layer_geojson,
        name="oilgas-map-layer-geojson",
    ),
    path("master/facilities/", views.facility_list, name="oilgas-facilities"),
    path("master/refineries/", views.refinery_list, name="oilgas-refineries"),
    path("master/fields/", views.field_list, name="oilgas-fields"),
    path("master/fields/<str:code>/", views.field_detail, name="oilgas-field-detail"),
    path(
        "fields/<int:field_id>/report-facts/",
        views.oil_field_report_facts,
        name="oilgas-field-facts",
    ),
    path(
        "refineries/<int:refinery_id>/report-facts/",
        views.oil_refinery_report_facts,
        name="oilgas-refinery-facts",
    ),
    path(
        "fuel-stations/<int:facility_id>/report-facts/",
        views.fuel_station_report_facts,
        name="oilgas-fuel-station-facts",
    ),
    path(
        "wells/<int:well_id>/report-facts/",
        views.oil_well_report_facts,
        name="oilgas-well-facts",
    ),
    path(
        "storage-depots/<int:facility_id>/report-facts/",
        views.storage_depot_report_facts,
        name="oilgas-storage-depot-facts",
    ),
    path(
        "pipelines/<int:pipeline_id>/report-facts/",
        views.pipeline_report_facts,
        name="oilgas-pipeline-facts",
    ),
    path(
        "operations/daily/", views.daily_operations_upsert, name="oilgas-operations-daily"
    ),
    path(
        "operations/publish/",
        views.daily_operations_publish,
        name="oilgas-operations-publish",
    ),
    path("targets/catalog/", views.target_catalog, name="oilgas-target-catalog"),
    path("targets/compare/", views.target_compare, name="oilgas-target-compare"),
    path("targets/coverage/", views.target_coverage, name="oilgas-target-coverage"),
    path("targets/fields/", views.target_field_matrix, name="oilgas-target-fields"),
    path("targets/monthly/", views.target_monthly, name="oilgas-target-monthly"),
    path("targets/", views.target_list, name="oilgas-targets"),
    path("targets/<int:pk>/", views.target_detail, name="oilgas-target-detail"),
    path("admin/registry/", views.admin_registry, name="oilgas-admin-registry"),
    path("admin/<str:slug>/options/", views.admin_options, name="oilgas-admin-options"),
    path("admin/<str:slug>/<str:pk>/", views.admin_detail, name="oilgas-admin-detail"),
    path("admin/<str:slug>/", views.admin_list, name="oilgas-admin-list"),
]
