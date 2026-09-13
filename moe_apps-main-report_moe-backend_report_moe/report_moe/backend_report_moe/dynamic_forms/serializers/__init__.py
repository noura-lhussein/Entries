"""
DRF serializers split by domain. Import from `dynamic_forms.serializers` (stable API).
"""

from .assignment_serializers import (
    UserSubMainSerializer,
    UserTitleCategorySerializer,
    UserTitleSerializer,
)
from .info_serializers import InfoRowDataSerializer, InfoSerializer
from .report_serializers import ReqReportSerializer, ReqReportTitleSerializer
from .structure_serializers import (
    AttributeSerializer,
    MainSectionSerializer,
    OptionSerializer,
    SubMainSectionSerializer,
    TitleCategorySerializer,
    TitleSerializer,
)
from .user_serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

__all__ = [
    "AttributeSerializer",
    "InfoRowDataSerializer",
    "InfoSerializer",
    "MainSectionSerializer",
    "OptionSerializer",
    "ReqReportSerializer",
    "ReqReportTitleSerializer",
    "SubMainSectionSerializer",
    "TitleCategorySerializer",
    "TitleSerializer",
    "UserCreateSerializer",
    "UserSerializer",
    "UserSubMainSerializer",
    "UserTitleCategorySerializer",
    "UserTitleSerializer",
    "UserUpdateSerializer",
]
