import uuid

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from ..assignment_checks import (
    allowed_title_ids,
    assert_sub_main_assigned,
    assert_sub_main_is_leaf,
)
from ..audit_log import log_action
from ..duplicate_date import (
    check_submit_duplicate_date,
    find_duplicate_date_conflict,
    is_date_attribute,
    normalize_date_value,
)
from ..location_resolution import build_info_records_from_row
from ..models import Attribute, Info, ReqReport, SubMainSection, Title
from ..permissions import CanWriteInfo
from ..serializers import ReqReportSerializer

def _persist_attribute_values(user, sub_main, items, allowed_title_ids):
    """Create Info rows, skipping attributes whose title is not assigned to the user.

    One transaction, one bulk_create: a logical row lands whole or not at all.
    Field resolution — the entity-first ordering, the location context cascade and
    the row-wide entity stamp — is delegated to `build_info_records_from_row`,
    which the Excel and JSON importers already use. This function carried a
    hand-maintained copy of that logic, and saved cell-by-cell outside any
    transaction, so a failure mid-row left a half-written record behind.
    """
    attr_ids: list[int] = []
    for item in items:
        raw_id = item.get("id")
        try:
            attr_ids.append(int(raw_id))
        except (TypeError, ValueError):
            raise Http404(f"No Attribute matches the given query: {raw_id!r}")

    attrs_by_id = {a.id: a for a in Attribute.objects.filter(pk__in=attr_ids)}

    row_attrs: list[tuple[int, object]] = []
    skipped = 0
    for item, attr_id in zip(items, attr_ids):
        attr = attrs_by_id.get(attr_id)
        if attr is None:
            raise Http404(f"No Attribute matches the given query: {attr_id}")
        if allowed_title_ids is not None and attr.title_id not in allowed_title_ids:
            skipped += 1
            continue
        row_attrs.append((attr.id, item.get("value", "")))

    if not row_attrs:
        return 0, skipped

    records = build_info_records_from_row(
        row_attrs,
        attrs_by_id,
        sub_main=sub_main,
        user=user,
        row_key=uuid.uuid4(),
    )
    with transaction.atomic():
        Info.objects.bulk_create(records)
    return len(records), skipped


class ReqReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        ReqReport.objects.select_related(
            "user",
            "req_report_sub_main__sub_main",
        )
        .prefetch_related("report_titles__title")
        .order_by("-id")
    )
    serializer_class = ReqReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    ordering_fields = ["id", "date_from", "date_to"]


class FullStructureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from ..form_schema import attribute_display_label

        title_id = request.query_params.get("title_id")
        qs = Title.objects.filter(
            deleted=False, attributes__isnull=False
        ).distinct().order_by("order", "id")
        if title_id:
            qs = qs.filter(pk=title_id)
        structure = []
        for title in qs:
            attrs = [
                {
                    "id": attr.id,
                    "label": attribute_display_label(attr),
                    "type": attr.type,
                    "required": attr.required,
                }
                for attr in title.attributes.all()
            ]
            structure.append({
                "id": title.id,
                "name": title.name,
                "order": title.order,
                "attributes": attrs,
            })
        return Response({"structure": structure})


class FormSchemaView(APIView):
    """Metadata contract for dynamic entry UI (groups, units, order, rules)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from ..form_schema import build_title_form_schema

        title_id = request.query_params.get("title_id")
        if not title_id:
            return Response({"detail": "title_id مطلوب."}, status=400)
        title = get_object_or_404(Title, pk=title_id, deleted=False)
        allowed = allowed_title_ids(request.user)
        if allowed is not None and title.id not in allowed:
            return Response({"detail": "غير مصرح."}, status=403)
        return Response(build_title_form_schema(title))


class SubmitReportView(APIView):
    permission_classes = [CanWriteInfo]

    def post(self, request):
        sub_main = get_object_or_404(
            SubMainSection.objects.select_related("location_district"),
            pk=request.data.get("sub_main_id"),
        )
        assert_sub_main_assigned(request.user, sub_main)
        assert_sub_main_is_leaf(sub_main)
        title_ids = allowed_title_ids(request.user)
        title_id = request.data.get("title_id")
        try:
            title_id = int(title_id) if title_id is not None else None
        except (TypeError, ValueError):
            title_id = None
        if title_id is not None and title_ids is not None and title_id not in title_ids:
            return Response({"detail": "غير مصرح."}, status=403)

        items = request.data.get("attribute_values", []) or []
        conflict = check_submit_duplicate_date(
            title_id=title_id,
            sub_main_id=sub_main.id,
            items=items,
        )
        if conflict:
            return Response(conflict, status=409)

        created, skipped = _persist_attribute_values(
            request.user,
            sub_main,
            items,
            title_ids,
        )
        if created:
            log_action(
                request, "CREATE", "Info",
                details={"sub_main_id": sub_main.id,
                         "created": created, "skipped_unassigned": skipped},
            )
        return Response(
            {"status": "success", "created": created, "skipped": skipped})


class SubmitFullReportView(APIView):
    permission_classes = [CanWriteInfo]

    def post(self, request):
        sub_main = get_object_or_404(
            SubMainSection.objects.select_related("location_district"),
            pk=request.data.get("sub_main_id"),
        )
        assert_sub_main_assigned(request.user, sub_main)
        assert_sub_main_is_leaf(sub_main)
        title_ids = allowed_title_ids(request.user)
        created = 0
        skipped = 0
        for r_data in request.data.get("reports", []):
            items = r_data.get("attribute_values", []) or []
            try:
                report_title_id = int(r_data["title_id"]) if r_data.get("title_id") is not None else None
            except (TypeError, ValueError):
                report_title_id = None
            conflict = check_submit_duplicate_date(
                title_id=report_title_id,
                sub_main_id=sub_main.id,
                items=items,
            )
            if conflict:
                return Response(conflict, status=409)
            c, s = _persist_attribute_values(
                request.user,
                sub_main,
                items,
                title_ids,
            )
            created += c
            skipped += s
        if created:
            log_action(
                request, "CREATE", "Info",
                details={"sub_main_id": sub_main.id, "full_report": True,
                         "created": created, "skipped_unassigned": skipped},
            )
        return Response(
            {"status": "success", "created": created, "skipped": skipped})


class CheckReportDateView(APIView):
    """Warn data-entry users before save if the date already has a report."""

    permission_classes = [CanWriteInfo]

    def get(self, request):
        try:
            title_id = int(request.query_params.get("title_id"))
            sub_main_id = int(request.query_params.get("sub_main_id"))
        except (TypeError, ValueError):
            return Response(
                {"detail": "title_id و sub_main_id مطلوبان."},
                status=400,
            )

        date_value = normalize_date_value(request.query_params.get("date"))
        if not date_value:
            return Response({"detail": "date مطلوب بصيغة YYYY-MM-DD."}, status=400)

        allowed = allowed_title_ids(request.user)
        if allowed is not None and title_id not in allowed:
            return Response({"detail": "غير مصرح."}, status=403)

        sub_main = get_object_or_404(SubMainSection, pk=sub_main_id)
        assert_sub_main_assigned(request.user, sub_main)

        date_attrs = sorted(
            [
                a
                for a in Attribute.objects.filter(title_id=title_id)
                if is_date_attribute(a)
            ],
            key=lambda a: (
                0
                if (a.key or "").strip() == "report_date"
                or (a.label or "").strip() == "تاريخ التقرير"
                else 1
            ),
        )
        if not date_attrs:
            return Response({"duplicate": False, "date": date_value})

        entity_type = (request.query_params.get("entity_type") or "").strip()
        entity_id_raw = request.query_params.get("entity_id")
        entity_id = None
        if entity_id_raw not in (None, ""):
            try:
                entity_id = int(entity_id_raw)
            except (TypeError, ValueError):
                return Response({"detail": "entity_id غير صالح."}, status=400)

        conflict = find_duplicate_date_conflict(
            title_id=title_id,
            sub_main_id=sub_main_id,
            date_value=date_value,
            date_attr=date_attrs[0],
            entity_type=entity_type,
            entity_id=entity_id,
        )
        if not conflict:
            return Response({"duplicate": False, "date": date_value})
        return Response({"duplicate": True, **conflict})
