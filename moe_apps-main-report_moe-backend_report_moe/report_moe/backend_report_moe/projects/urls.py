"""Development-project routes, mounted at `/api/v1/projects/`.

Literal segments come before `<int:pk>/` so `meta`, `summary`, `dashboard` and
`organizations` are never read as project ids.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.project_list, name="projects-list"),
    path("meta/", views.projects_meta, name="projects-meta"),
    path("summary/", views.projects_summary, name="projects-summary"),
    path("dashboard/", views.projects_dashboard, name="projects-dashboard"),
    path("organizations/", views.organization_list, name="projects-organizations"),
    path(
        "organizations/<int:pk>/",
        views.organization_detail,
        name="projects-organization-detail",
    ),
    path("<int:pk>/monitoring/", views.project_monitoring, name="projects-monitoring"),
    path("<int:pk>/", views.project_detail, name="projects-detail"),
]
