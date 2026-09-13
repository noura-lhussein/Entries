import uuid

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from ..audit_log import log_action
from ..info_confirmation import (
    ACCEPT,
    REJECT,
    next_toggle_status,
    status_from_request,
)
from ..info_querysets import (
    apply_info_list_filters,
    info_list_base_queryset,
    scope_info_queryset_for_user,
)
from ..models import Info
from ..pagination import LargePagination
from ..permissions import CanConfirmInfo, CanWriteInfo
from ..row_grouping import count_logical_rows_for_infos_qs
from ..serializers import InfoRowDataSerializer


def _assigned_sub_main_ids(user):
    return list(user.user_sub_mains.values_list("sub_main_id", flat=True))


def _scope_confirm_queryset(qs, user):
    if user.is_staff or user.is_superuser:
        return qs
    return qs.filter(sub_main_id__in=_assigned_sub_main_ids(user))


def _assert_deletable(qs):
    """Accepted records are final. The frontend only disables the button — this
    is where the rule is actually enforced, for single cells and whole rows."""
    if qs.filter(confirmed=ACCEPT).exists():
        raise PermissionDenied("لا يمكن حذف سجل معتمد.")


class InfoViewSet(viewsets.ModelViewSet):
    queryset = info_list_base_queryset()
    serializer_class = InfoRowDataSerializer
    permission_classes = [CanWriteInfo]
    pagination_class = LargePagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["value", "attribute__label"]
    ordering_fields = ["created_at", "confirmed"]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_info_queryset_for_user(qs, self.request.user)
        return apply_info_list_filters(qs, self.request.query_params)

    def perform_create(self, serializer):
        if not self.request.user.can_write_info and not (
            self.request.user.is_staff or self.request.user.is_superuser
        ):
            raise PermissionDenied("ليس لديك صلاحية إدخال بيانات.")
        extra = {
            "user": self.request.user,
            "row_key": uuid.uuid4(),
        }
        raw_key = self.request.data.get("row_key")
        if raw_key:
            try:
                key = uuid.UUID(str(raw_key))
            except ValueError as exc:
                raise ValidationError({"row_key": "قيمة غير صالحة."}) from exc
            sibling = (
                Info.objects.filter(row_key=key, archived=False)
                .select_related("sub_main")
                .first()
            )
            if sibling is None:
                raise ValidationError({"row_key": "السجل غير موجود."})
            extra["row_key"] = sibling.row_key
            extra["user"] = sibling.user or self.request.user
            if sibling.sub_main_id:
                extra["sub_main"] = sibling.sub_main
        instance = serializer.save(**extra)
        log_action(
            self.request,
            "CREATE",
            "Info",
            instance.id,
            {"attribute": instance.attribute_id, "value": instance.value},
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            self.request,
            "UPDATE",
            "Info",
            instance.id,
            {"attribute": instance.attribute_id, "value": instance.value},
        )

    def perform_destroy(self, instance):
        _assert_deletable(Info.objects.filter(pk=instance.pk))
        log_action(
            self.request,
            "DELETE",
            "Info",
            instance.id,
            {"attribute": instance.attribute_id, "value": instance.value},
        )
        instance.delete()

    @action(detail=False, methods=["post"], url_path="delete-row")
    def delete_row(self, request):
        """Delete every cell of one logical record in a single transaction.

        A record is a set of Info cells sharing `row_key`; deleting them one
        request at a time can leave a half-removed record behind if one fails.
        """
        row_key = request.data.get("row_key")
        if not row_key:
            raise ValidationError({"row_key": "مطلوب."})
        qs = scope_info_queryset_for_user(
            Info.objects.filter(row_key=row_key), request.user
        )
        if not qs.exists():
            raise NotFound("السجل غير موجود.")
        _assert_deletable(qs)
        with transaction.atomic():
            deleted, _ = qs.delete()
        log_action(
            request,
            "DELETE",
            "Info",
            details={"row_key": str(row_key), "deleted_fields": deleted},
        )
        return Response({"deleted": deleted, "deleted_rows": 1})

    @action(detail=True, methods=["post"], permission_classes=[CanConfirmInfo])
    def toggle_confirmed(self, request, pk=None):
        info = self.get_object()
        if not (request.user.is_staff or request.user.is_superuser):
            if info.sub_main_id not in _assigned_sub_main_ids(request.user):
                return Response(
                    {"detail": "ليس لديك صلاحية تأكيد هذا السجل."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        if "status" in request.data or (
            "confirmed" in request.data
            and request.data.get("confirmed") not in (True, False)
        ):
            info.confirmed = status_from_request(
                request.data, default=info.confirmed
            )
        else:
            info.confirmed = next_toggle_status(info.confirmed)
        update_fields = ["confirmed"]
        if "note" in request.data:
            info.confirm_note = (request.data.get("note") or "").strip()
            update_fields.append("confirm_note")
        info.save(update_fields=update_fields)
        log_action(
            request, "CONFIRM", "Info", info.id, {"confirmed": info.confirmed}
        )
        return Response(InfoRowDataSerializer(info).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-confirm",
        permission_classes=[CanConfirmInfo],
    )
    def bulk_confirm(self, request):
        qs = _scope_confirm_queryset(
            self.get_queryset().exclude(confirmed=ACCEPT), request.user
        )
        note_provided = "note" in request.data
        note_val = (request.data.get("note") or "").strip()
        updates = {"confirmed": ACCEPT}
        if note_provided:
            updates["confirm_note"] = note_val
        row_count = count_logical_rows_for_infos_qs(qs)
        count = qs.update(**updates)
        log_action(
            request,
            "CONFIRM",
            "Info",
            details={"bulk": True, "fields_updated": count,
                     "updated_rows": row_count},
        )
        return Response({"confirmed": count, "updated_rows": row_count})

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk-reject",
        permission_classes=[CanConfirmInfo],
    )
    def bulk_reject(self, request):
        qs = _scope_confirm_queryset(
            self.get_queryset().filter(confirmed=ACCEPT), request.user
        )
        note_provided = "note" in request.data
        note_val = (request.data.get("note") or "").strip()
        updates = {"confirmed": REJECT}
        if note_provided:
            updates["confirm_note"] = note_val
        row_count = count_logical_rows_for_infos_qs(qs)
        count = qs.update(**updates)
        log_action(
            request,
            "CONFIRM",
            "Info",
            details={"bulk_reject": True, "fields_updated": count,
                     "updated_rows": row_count},
        )
        return Response({"rejected": count, "updated_rows": row_count})

    @action(
        detail=False,
        methods=["post"],
        url_path="confirm-ids",
        permission_classes=[CanConfirmInfo],
    )
    def confirm_ids(self, request):
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"updated": 0})
        new_status = status_from_request(request.data, default=ACCEPT)
        qs = _scope_confirm_queryset(
            self.get_queryset().filter(id__in=ids), request.user
        )
        note_provided = "note" in request.data
        note_val = (request.data.get("note") or "").strip()
        updates = {"confirmed": new_status}
        if note_provided:
            updates["confirm_note"] = note_val
        row_count = count_logical_rows_for_infos_qs(qs)
        count = qs.update(**updates)
        log_action(
            request,
            "CONFIRM",
            "Info",
            details={
                "confirm_ids": True,
                "fields_updated": count,
                "updated_rows": row_count,
                "confirmed": new_status,
            },
        )
        return Response({"updated": count, "updated_rows": row_count})

    @action(
        detail=False,
        methods=["post"],
        url_path="confirm-row-keys",
        permission_classes=[CanConfirmInfo],
    )
    def confirm_row_keys(self, request):
        row_keys = request.data.get("row_keys", [])
        if not row_keys:
            return Response({"updated": 0, "updated_rows": 0})
        new_status = status_from_request(request.data, default=ACCEPT)
        qs = _scope_confirm_queryset(
            self.get_queryset().filter(row_key__in=row_keys), request.user
        )
        note_provided = "note" in request.data
        note_val = (request.data.get("note") or "").strip()
        updates = {"confirmed": new_status}
        if note_provided:
            updates["confirm_note"] = note_val
        row_count = count_logical_rows_for_infos_qs(qs)
        count = qs.update(**updates)
        log_action(
            request,
            "CONFIRM",
            "Info",
            details={
                "confirm_row_keys": True,
                "fields_updated": count,
                "updated_rows": row_count,
                "confirmed": new_status,
            },
        )
        return Response({"updated": count, "updated_rows": row_count})

    @action(
        detail=False,
        methods=["post"],
        url_path="commit-note-ids",
        permission_classes=[CanConfirmInfo],
    )
    def commit_note_ids(self, request):
        ids = request.data.get("ids", [])
        note = (request.data.get("note") or "").strip()
        if not ids:
            return Response({"updated": 0})
        qs = _scope_confirm_queryset(
            self.get_queryset().filter(id__in=ids), request.user
        )
        count = qs.update(commit_note=note)
        log_action(
            request, "UPDATE", "Info", details={"commit_note_ids": True, "count": count}
        )
        return Response({"updated": count})


class InfoDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        info = get_object_or_404(Info, pk=pk)
        if not (request.user.is_staff or request.user.is_superuser):
            if info.user_id != request.user.id:
                return Response(
                    {"detail": "ليس لديك صلاحية مشاهدة هذا السجل."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return Response(InfoRowDataSerializer(info).data)

    def put(self, request, pk):
        info = get_object_or_404(Info, pk=pk)
        if not (request.user.is_staff or request.user.is_superuser):
            if info.user_id != request.user.id:
                return Response(
                    {"detail": "ليس لديك صلاحية تعديل هذا السجل."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        serializer = InfoRowDataSerializer(
            info, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        info = get_object_or_404(Info, pk=pk)
        if not (request.user.is_staff or request.user.is_superuser):
            if info.user_id != request.user.id:
                return Response(
                    {"detail": "ليس لديك صلاحية حذف هذا السجل."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        _assert_deletable(Info.objects.filter(pk=info.pk))
        info.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
