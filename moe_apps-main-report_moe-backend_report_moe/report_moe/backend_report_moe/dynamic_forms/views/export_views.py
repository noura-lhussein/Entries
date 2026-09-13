from django.db import transaction
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..application.export_report import (
    EmptyExportError,
    ExportReportService,
    ExportRowLimitError,
)
from ..audit_log import log_action
from ..pagination import LargePagination
from ..permissions import CanExportReports
from ..serializers import InfoRowDataSerializer


def _normalize_export_format(raw: str) -> str | None:
    fmt = (raw or "").lower().strip()
    if fmt in ("xlsx",):
        return "excel"
    if fmt in ("docx",):
        return "word"
    if fmt in ("pdf",):
        return "pdf"
    if fmt in ("excel", "word", "pdf"):
        return fmt
    return None


def export_reports_file_response(request, fmt: str):
    try:
        response = ExportReportService.file_http_response(request, fmt)
    except EmptyExportError as exc:
        return exc.to_response()
    except ExportRowLimitError as exc:
        return exc.to_response()

    qs = ExportReportService.queryset_for_request(request)
    log_action(
        request,
        "EXPORT",
        "Info",
        details={
            "export_reports_download": True,
            "format": fmt,
            "full_report": ExportReportService.is_full_report(request),
            "filters": dict(request.query_params),
            "count": qs.count(),
        },
    )
    return response


# Read-only, and a full-report build walks tens of thousands of rows: under
# ATOMIC_REQUESTS that would keep a transaction (and its snapshot) open for the
# whole render with nothing to roll back.
@method_decorator(transaction.non_atomic_requests, name="dispatch")
class ExportReportsView(APIView):
    """List or download confirmed Info rows for users with can_export_reports."""

    permission_classes = [CanExportReports]
    pagination_class = LargePagination

    def get(self, request):
        fmt = _normalize_export_format(
            request.query_params.get("export_format"))
        if fmt:
            return export_reports_file_response(request, fmt)

        qs = ExportReportService.queryset_for_request(request)
        total = qs.count()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = InfoRowDataSerializer(page, many=True)
        log_action(
            request,
            "EXPORT",
            "Info",
            details={
                "export_reports_list": True,
                "filters": dict(request.query_params),
                "count": total,
            },
        )
        return paginator.get_paginated_response(serializer.data)


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class ExportReportsDownloadView(APIView):
    """Backward-compatible alias for file download on /export-reports/download/."""

    permission_classes = [CanExportReports]

    def get(self, request):
        fmt = _normalize_export_format(
            request.query_params.get("export_format")
        ) or "excel"
        if fmt not in ("excel", "word", "pdf"):
            return Response(
                {"detail": "export_format يجب أن يكون excel أو word أو pdf."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return export_reports_file_response(request, fmt)
