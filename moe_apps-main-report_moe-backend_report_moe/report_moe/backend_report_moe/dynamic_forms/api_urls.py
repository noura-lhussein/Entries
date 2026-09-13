from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register(r"users", api_views.UserViewSet, basename="user")
router.register(r"main-sections", api_views.MainSectionViewSet,
                basename="main-section")
router.register(r"sub-sections", api_views.SubMainSectionViewSet,
                basename="sub-section")
router.register(r"title-categories", api_views.TitleCategoryViewSet,
                basename="title-category")
router.register(r"titles", api_views.TitleViewSet, basename="title")
router.register(r"attributes", api_views.AttributeViewSet,
                basename="attribute")
router.register(r"options", api_views.OptionViewSet, basename="option")
router.register(r"reports", api_views.ReqReportViewSet, basename="report")
router.register(r"infos", api_views.InfoViewSet, basename="info")
router.register(r"user-sub-mains", api_views.UserSubMainViewSet,
                basename="user-sub-main")
router.register(r"user-titles", api_views.UserTitleViewSet,
                basename="user-title")
router.register(r"user-title-categories", api_views.UserTitleCategoryViewSet,
                basename="user-title-category")

urlpatterns = [
    # Auth
    path("auth/csrf/", api_views.get_csrf_token, name="api_csrf"),
    path("auth/login/", api_views.LoginView.as_view(), name="api_login"),
    path("auth/logout/", api_views.LogoutView.as_view(), name="api_logout"),
    path("auth/me/", api_views.MeView.as_view(), name="api_me"),
    path("auth/permissions/", api_views.UserPermissionsView.as_view(),
         name="api_permissions"),

    # Dashboard
    path("dashboard/stats/", api_views.DashboardStatsView.as_view(),
         name="api_dashboard_stats"),

    # User sections
    path("user/main-sections/", api_views.UserMainSectionsView.as_view(),
         name="api_user_main_sections"),

    path("uploads/limits/", api_views.UploadLimitsView.as_view(),
         name="api_upload_limits"),
    path("uploads/form-file/", api_views.FormFileUploadView.as_view(),
         name="api_form_file_upload"),

    # Reports
    path("reports/submit/", api_views.SubmitReportView.as_view(),
         name="api_submit_report"),
    path("reports/submit-full/", api_views.SubmitFullReportView.as_view(),
         name="api_submit_full_report"),
    path("reports/check-date/", api_views.CheckReportDateView.as_view(),
         name="api_check_report_date"),
    path("reports/full-structure/", api_views.FullStructureView.as_view(),
         name="api_full_structure"),
    path("reports/form-schema/", api_views.FormSchemaView.as_view(),
         name="api_form_schema"),

    path("export-reports/", api_views.ExportReportsView.as_view(),
         name="api_export_reports"),
    path("export-reports/download/", api_views.ExportReportsDownloadView.as_view(),
         name="api_export_reports_download"),

    # Info detail
    path("infos/row-count/", api_views.InfoRowCountView.as_view(),
         name="api_info_row_count"),
    path("info-rows/", api_views.InfoRowsListView.as_view(),
         name="api_info_rows"),
    path("infos/<int:pk>/detail/",
         api_views.InfoDetailView.as_view(), name="api_info_detail"),

    path("geocode/search/", api_views.GeocodeSearchView.as_view(),
         name="api_geocode_search"),

    path(
        "entity-options/<str:entity_type>/",
        api_views.EntityOptionsView.as_view(),
        name="api_entity_options",
    ),

    # CRUD
    path("", include(router.urls)),
]
