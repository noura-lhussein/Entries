from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.swagger_views import OpenApiJsonView, SwaggerUiView

urlpatterns = [
    # /admin/ is owned by the moe-portal Angular router; Django admin lives here
    # so a same-origin deployment does not collide on a hard reload of /admin/*.
    path("django-admin/", admin.site.urls),
    path("api/docs/", SwaggerUiView.as_view(), name="api-docs"),
    path("api/docs/openapi.json", OpenApiJsonView.as_view(), name="api-openapi"),
    path("api/v1/", include("dynamic_forms.api_urls")),
    path("api/v1/budget/", include("project_budget.api_urls")),
    path("api/v1/locations/", include("locations.api_urls")),
    path("api/v1/master-data/", include("master_data.urls")),
    # ── Portal sector APIs (converted from Django Ninja) ─────────────────
    # Prefixes are fixed by the portal frontend and must not be renamed.
    path("api/v1/gis/", include("map_layers.urls")),
    path("api/v1/datasets/", include("datasets.urls")),
    path("api/v1/projects/", include("projects.urls")),
    path("api/v1/geology/", include("geology.urls")),
    path("api/v1/electricity/", include("electricity.urls")),
    path("api/v1/oil-gas/", include("oil_gas.urls")),
    path("api/v1/water/", include("water.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
