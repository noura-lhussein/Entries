"""Dataset routes, mounted at `/api/v1/datasets/`.

Order matters: `meta/` must precede the `<int:pk>/` patterns so it is not read as
a dataset id.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.dataset_list, name="datasets-list"),
    path("meta/", views.datasets_meta, name="datasets-meta"),
    path("<int:pk>/download/", views.download_dataset, name="datasets-download"),
    path("<int:pk>/preview/", views.preview_dataset, name="datasets-preview"),
    path(
        "<int:pk>/spatial-layers/",
        views.dataset_spatial_layers,
        name="datasets-spatial-layers",
    ),
    path(
        "<int:pk>/record-download/",
        views.record_download,
        name="datasets-record-download",
    ),
    path("<int:pk>/", views.dataset_detail, name="datasets-detail"),
]
