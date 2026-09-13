"""API views split by domain. Re-exported from api_views for backward compatibility."""

from .auth_views import (
    LoginView,
    LogoutView,
    MeView,
    UserMainSectionsView,
    UserPermissionsView,
    get_csrf_token,
)
from .dashboard_views import DashboardStatsView
from .export_views import ExportReportsDownloadView, ExportReportsView
from .geocode_views import GeocodeSearchView
from .info_rows_views import InfoRowsListView
from .info_views import InfoDetailView, InfoViewSet
from .report_views import (
    CheckReportDateView,
    FormSchemaView,
    FullStructureView,
    ReqReportViewSet,
    SubmitFullReportView,
    SubmitReportView,
)
from .row_count_views import InfoRowCountView
from .structure_views import (
    AttributeViewSet,
    EntityOptionsView,
    MainSectionViewSet,
    OptionViewSet,
    SubMainSectionViewSet,
    TitleCategoryViewSet,
    TitleViewSet,
)
from .upload_views import FormFileUploadView, UploadLimitsView
from .user_views import (
    UserSubMainViewSet,
    UserTitleCategoryViewSet,
    UserTitleViewSet,
    UserViewSet,
)

__all__ = [
    "LoginView",
    "LogoutView",
    "MeView",
    "UserMainSectionsView",
    "UserPermissionsView",
    "get_csrf_token",
    "DashboardStatsView",
    "ExportReportsDownloadView",
    "ExportReportsView",
    "GeocodeSearchView",
    "InfoDetailView",
    "InfoRowsListView",
    "InfoRowCountView",
    "InfoViewSet",
    "FormSchemaView",
    "FullStructureView",
    "ReqReportViewSet",
    "CheckReportDateView",
    "SubmitFullReportView",
    "SubmitReportView",
    "AttributeViewSet",
    "EntityOptionsView",
    "MainSectionViewSet",
    "OptionViewSet",
    "SubMainSectionViewSet",
    "TitleCategoryViewSet",
    "TitleViewSet",
    "FormFileUploadView",
    "UploadLimitsView",
    "UserSubMainViewSet",
    "UserTitleCategoryViewSet",
    "UserTitleViewSet",
    "UserViewSet",
]
