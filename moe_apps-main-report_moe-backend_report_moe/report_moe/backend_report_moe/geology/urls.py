"""Geology routes, mounted at `/api/v1/geology/`.

The fixed `admin/...` paths come before `admin/<slug>/` so `registry` and
`daily-report` are never read as resource slugs.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="geology-dashboard"),
    path("reports/export/", views.reports_export, name="geology-reports-export"),
    path("admin/registry/", views.admin_registry, name="geology-admin-registry"),
    path(
        "admin/daily-report/template/",
        views.daily_report_template,
        name="geology-daily-report-template",
    ),
    path(
        "admin/daily-report/export/",
        views.daily_report_export,
        name="geology-daily-report-export",
    ),
    path(
        "admin/daily-report/import/",
        views.daily_report_import,
        name="geology-daily-report-import",
    ),
    path("admin/daily-report/", views.daily_report, name="geology-daily-report"),
    path("admin/<str:slug>/options/", views.admin_options, name="geology-admin-options"),
    path("admin/<str:slug>/<str:pk>/", views.admin_detail, name="geology-admin-detail"),
    path("admin/<str:slug>/", views.admin_list, name="geology-admin-list"),
]
