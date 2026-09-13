"""Export confirmed Info rows to Excel, Word, or PDF."""

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response

from ..export_reports_file import build_export_excel, build_export_pdf, build_export_word
from ..info_confirmation import ACCEPT
from ..info_querysets import (
    INFO_LIST_SELECT_RELATED,
    apply_info_list_filters,
    scope_info_queryset_for_user,
)
from ..models import Info
from ..row_grouping import count_export_rows_for_queryset


def export_filter_params(query_params):
    scope = (query_params.get("export_scope") or "").lower().strip()
    if scope != "full":
        return query_params
    params = query_params.copy()
    for key in ("main_section_id", "sub_main_id", "title_id", "export_scope"):
        params.pop(key, None)
    return params


class ExportReportService:
    """Build export querysets and file responses."""

    @staticmethod
    def base_queryset():
        return (
            Info.objects.select_related(*INFO_LIST_SELECT_RELATED)
            .filter(confirmed=ACCEPT)
            .order_by(
                "attribute__title__order",
                "sub_main__main_section__name",
                "sub_main__name",
                "attribute__id",
                "-created_at",
            )
        )

    @classmethod
    def queryset_for_request(cls, request):
        qs = cls.base_queryset()
        qs = scope_info_queryset_for_user(qs, request.user)
        qs = apply_info_list_filters(
            qs, export_filter_params(request.query_params)
        )
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(value__icontains=search) | Q(
                    attribute__label__icontains=search)
            )
        return qs

    @staticmethod
    def is_full_report(request) -> bool:
        return (request.query_params.get("export_scope") or "").lower().strip() == "full"

    @classmethod
    def row_count_for_request(cls, request) -> int:
        # NOTE: `count_export_rows_for_queryset` groups by (user_id, slot
        # matching) — it does NOT use row_key at all, so a distinct-row_key
        # count is *not* a valid bound for it (verified against real data:
        # the row_key count came out lower than the true dedup count for a
        # real title, i.e. not an upper bound at all). No cheap SQL substitute
        # without reimplementing the same slot-matching in SQL — left as is.
        return count_export_rows_for_queryset(cls.queryset_for_request(request))

    @classmethod
    def enforce_export_limits(cls, request) -> None:
        count = cls.row_count_for_request(request)
        if count == 0:
            raise EmptyExportError()
        limit = getattr(settings, "EXPORT_MAX_ROWS", 50_000)
        if count > limit:
            raise ExportRowLimitError(count=count, limit=limit)

    @classmethod
    def build_file(cls, request, fmt: str) -> tuple[bytes, str, str]:
        """Return (file_bytes, filename, content_type)."""
        cls.enforce_export_limits(request)
        qs = cls.queryset_for_request(request)

        full_report = cls.is_full_report(request)
        if fmt == "excel":
            data, filename = build_export_excel(
                qs, full_report=full_report, user=request.user
            )
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        elif fmt == "pdf":
            data, filename = build_export_pdf(
                qs, full_report=full_report, user=request.user
            )
            content_type = "application/pdf"
        else:
            data, filename = build_export_word(
                qs, full_report=full_report, user=request.user
            )
            content_type = (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        return data, filename, content_type

    @classmethod
    def file_http_response(cls, request, fmt: str) -> HttpResponse:
        data, filename, content_type = cls.build_file(request, fmt)
        response = HttpResponse(data, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class EmptyExportError(Exception):
    """Raised when export queryset has no rows."""

    message = "لا توجد بيانات مطابقة للفلاتر المحددة."

    def to_response(self):
        return Response(
            {"detail": self.message},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ExportRowLimitError(Exception):
    """Raised when export row count exceeds EXPORT_MAX_ROWS."""

    def __init__(self, *, count: int, limit: int):
        self.count = count
        self.limit = limit

    @property
    def message(self) -> str:
        return (
            f"تجاوز التصدير الحد الأقصى ({self.limit} صف). "
            f"النتيجة الحالية: {self.count} صف. قلّل النطاق باستخدام الفلاتر."
        )

    def to_response(self):
        return Response(
            {
                "detail": self.message,
                "count": self.count,
                "limit": self.limit,
            },
            status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
