from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from ..info_confirmation import ACCEPT
from ..models import (
    Attribute,
    AuditLog,
    Info,
    MainSection,
    ReqReport,
    SubMainSection,
    Title,
)
from ..permissions import IsAdmin
from ..row_grouping import row_stats_via_sql

User = get_user_model()


def _dashboard_rates(infos_qs):
    field_total = infos_qs.count()
    field_confirmed = infos_qs.filter(confirmed=ACCEPT).count()
    field_pending = max(field_total - field_confirmed, 0)
    field_confirmation_rate = (
        round(100 * field_confirmed / field_total) if field_total else 0
    )

    # SQL-aggregated, not materialized into Python — this queryset is
    # unscoped (whole table) and production has millions of rows.
    row_stats = row_stats_via_sql(infos_qs)
    rows_total = row_stats["rows_count"]
    rows_confirmed = row_stats["rows_confirmed_count"]
    rows_pending = row_stats["rows_pending_count"]
    rows_confirmation_rate = (
        round(100 * rows_confirmed / rows_total) if rows_total else 0
    )

    week_ago = timezone.now() - timedelta(days=7)
    recent_fields = infos_qs.filter(created_at__gte=week_ago).count()
    activity_rate_7d = (
        round(100 * recent_fields / field_total) if field_total else 0
    )

    return {
        "infos_count": field_total,
        "infos_confirmed_count": field_confirmed,
        "infos_pending_count": field_pending,
        "confirmation_rate": field_confirmation_rate,
        "rows_count": rows_total,
        "rows_confirmed_count": rows_confirmed,
        "rows_pending_count": rows_pending,
        "rows_confirmation_rate": rows_confirmation_rate,
        "activity_rate_7d": activity_rate_7d,
    }


def _serialize_audit_activities(logs):
    rows = []
    for log in logs:
        username = "—"
        if log.user_id:
            username = (
                log.user.display_name or log.user.email or str(log.user_id)
            )
        rows.append({
            "action": log.action,
            "model_name": log.model_name or "",
            "object_id": log.object_id,
            "details": log.details,
            "timestamp": log.timestamp.isoformat(),
            "user_name": username,
        })
    return rows


class DashboardStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        infos_qs = Info.objects.filter(archived=False)
        rates = _dashboard_rates(infos_qs)
        logs = AuditLog.objects.select_related(
            "user").order_by("-timestamp")[:12]
        return Response({
            "is_admin_view": True,
            "users_count": User.objects.filter(deleted=False).count(),
            "main_sections_count": MainSection.objects.filter(deleted=False).count(),
            "sub_sections_count": SubMainSection.objects.filter(deleted=False).count(),
            "reports_count": ReqReport.objects.count(),
            "titles_count": Title.objects.filter(deleted=False).count(),
            "attributes_count": Attribute.objects.count(),
            **rates,
            "recent_activities": _serialize_audit_activities(logs),
        })
