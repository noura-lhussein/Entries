"""Electricity routes, mounted at `/api/v1/electricity/`.

Fixed segments precede `admin/<slug>/` so `registry` is never read as a slug.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("info-catalog/", views.info_catalog, name="electricity-info-catalog"),
    path("dashboard/", views.dashboard, name="electricity-dashboard"),
    path("trends/<str:metric_key>/", views.trend, name="electricity-trend"),
    path("report-dates/", views.report_dates, name="electricity-report-dates"),
    path("reports/", views.report_list, name="electricity-reports"),
    path("reports/detail/", views.report_detail, name="electricity-report-detail"),
    path("reports/export/", views.report_export, name="electricity-report-export"),
    path("reports/template/", views.report_template, name="electricity-report-template"),
    path("reports/import/", views.report_import, name="electricity-report-import"),
    path("reports/upsert/", views.report_upsert, name="electricity-report-upsert"),
    path(
        "map-layers/<str:layer_id>/geojson/",
        views.map_layer_geojson,
        name="electricity-map-layer-geojson",
    ),
    path("master/power-plants/", views.power_plant_list, name="electricity-power-plants"),
    path(
        "power-plants/<int:plant_id>/report-facts/",
        views.power_plant_report_facts,
        name="electricity-power-plant-facts",
    ),
    path(
        "substations/<int:substation_id>/report-facts/",
        views.substation_report_facts,
        name="electricity-substation-facts",
    ),
    path(
        "transmission-lines/<int:line_id>/report-facts/",
        views.transmission_line_report_facts,
        name="electricity-transmission-line-facts",
    ),
    path(
        "gis-substations-66/<int:feature_id>/report-facts/",
        views.gis_substation_66_report_facts,
        name="electricity-gis-substation-66-facts",
    ),
    path(
        "gis-substations-230/<int:feature_id>/report-facts/",
        views.gis_substation_230_report_facts,
        name="electricity-gis-substation-230-facts",
    ),
    path(
        "gis-substations-400/<int:feature_id>/report-facts/",
        views.gis_substation_400_report_facts,
        name="electricity-gis-substation-400-facts",
    ),
    path(
        "gis-renewable-sites/<int:feature_id>/report-facts/",
        views.gis_renewable_report_facts,
        name="electricity-gis-renewable-facts",
    ),
    path(
        "operations/daily/",
        views.daily_operations_upsert,
        name="electricity-operations-daily",
    ),
    path(
        "operations/publish/",
        views.daily_operations_publish,
        name="electricity-operations-publish",
    ),
    path("targets/catalog/", views.target_catalog, name="electricity-target-catalog"),
    path("targets/coverage/", views.target_coverage, name="electricity-target-coverage"),
    path("targets/plants/", views.target_plant_matrix, name="electricity-target-plants"),
    path("targets/monthly/", views.target_monthly, name="electricity-target-monthly"),
    path("admin/registry/", views.admin_registry, name="electricity-admin-registry"),
    path(
        "admin/<str:slug>/options/",
        views.admin_options,
        name="electricity-admin-options",
    ),
    path(
        "admin/<str:slug>/<str:pk>/", views.admin_detail, name="electricity-admin-detail"
    ),
    path("admin/<str:slug>/", views.admin_list, name="electricity-admin-list"),
]
