"""Map layer routes.

Mounted at `/api/v1/gis/` — the prefix is part of the portal's contract and stays
`gis` even though the app was renamed to avoid colliding with `django.contrib.gis`.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("admin-layers/", views.admin_layers, name="gis-admin-layers"),
    path(
        "admin-layers/<str:layer_id>/geojson/",
        views.admin_layer_geojson,
        name="gis-admin-layer-geojson",
    ),
    path("filters/<str:filter_key>/", views.filter_options, name="gis-filter-options"),
    path("water-layers/", views.water_layers, name="gis-water-layers"),
    path(
        "water-layers/<str:layer_id>/geojson/",
        views.water_layer_geojson,
        name="gis-water-layer-geojson",
    ),
    path("springs/map-catalog/", views.springs_map_catalog, name="gis-springs-map-catalog"),
    path("geology-layers/", views.geology_layers, name="gis-geology-layers"),
    path(
        "geology-layers/<str:layer_id>/geojson/",
        views.geology_layer_geojson,
        name="gis-geology-layer-geojson",
    ),
    path("geology-info/", views.geology_info, name="gis-geology-info"),
]
