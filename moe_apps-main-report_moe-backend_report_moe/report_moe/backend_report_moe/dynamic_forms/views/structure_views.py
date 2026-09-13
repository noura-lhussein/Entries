import re

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpResponse
from rest_framework import parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ..archive_structure import (
    soft_delete_main_section,
    soft_delete_sub_main,
    soft_delete_title,
)
from ..assignment_checks import (
    allowed_title_category_ids,
    allowed_title_ids,
    is_admin,
)
from ..audit_log import log_action
from ..entity_registry import ENTITY_TYPE_SPECS, list_entity_options
from ..info_querysets import main_sections_queryset_for_user
from ..models import Attribute, MainSection, Option, SubMainSection, Title, TitleCategory
from ..pagination import LargePagination
from ..permissions import CanWriteInfo, IsAdmin, IsAdminOrReadOnly
from ..serializers import (
    AttributeSerializer,
    MainSectionSerializer,
    OptionSerializer,
    SubMainSectionSerializer,
    TitleSerializer,
)
from ..serializers.structure_serializers import TitleCategorySerializer
from ..title_excel.measures import DEFAULT_TEMPLATE_LAYOUT, LayoutNotSupported
from ..title_excel_registry import get_handler_for_title

User = get_user_model()


def _serialize_assigned_users(user_qs):
    rows = []
    for u in user_qs.select_related("parent").order_by("full_name", "email", "id"):
        rows.append(
            {
                "id": u.id,
                "full_name": u.full_name or u.email,
                "username": u.email,
                "email": u.email,
                "is_active": u.is_active,
                "parent_name": (
                    u.parent.display_name if getattr(
                        u, "parent_id", None) else None
                ),
            }
        )
    return rows


class MainSectionViewSet(viewsets.ModelViewSet):
    queryset = MainSection.objects.filter(deleted=False).order_by("name")
    serializer_class = MainSectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargePagination

    def get_queryset(self):
        return main_sections_queryset_for_user(self.request.user)

    def perform_destroy(self, instance):
        soft_delete_main_section(instance, self.request.user)
        log_action(
            self.request,
            "DELETE",
            "MainSection",
            instance.id,
            {"soft_delete": True, "archived": True},
        )


class SubMainSectionViewSet(viewsets.ModelViewSet):
    queryset = SubMainSection.objects.filter(deleted=False).order_by("name")
    serializer_class = SubMainSectionSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargePagination

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            qs = SubMainSection.objects.filter(deleted=False).order_by("name")
        else:
            assigned = list(user.user_sub_mains.values_list(
                "sub_main_id", flat=True))
            qs = SubMainSection.objects.filter(
                deleted=False, id__in=assigned
            ).order_by("name")
        main = self.request.query_params.get("main_section")
        if main:
            qs = qs.filter(main_section_id=main)
        parent = self.request.query_params.get("parent")
        if parent is not None and parent != "":
            if str(parent).lower() in ("null", "none", "root"):
                qs = qs.filter(parent__isnull=True)
            else:
                qs = qs.filter(parent_id=parent)
        active_children = Count("children", filter=Q(children__deleted=False))
        leaves = self.request.query_params.get("leaves")
        if str(leaves).lower() in ("1", "true", "yes"):
            qs = qs.annotate(_cc=active_children).filter(_cc=0)
        return qs.annotate(children_count=active_children).select_related(
            "main_section", "parent", "location_district",
            "location_district__governorate",
        )

    def perform_destroy(self, instance):
        soft_delete_sub_main(instance, self.request.user)
        log_action(
            self.request,
            "DELETE",
            "SubMainSection",
            instance.id,
            {"soft_delete": True, "archived": True},
        )

    @action(detail=False, methods=["get"], url_path="tree")
    def tree(self, request):
        """Nested tree of sub-sections for one main section (admin/structure UI)."""
        main = request.query_params.get("main_section")
        if not main:
            return Response(
                {"detail": "main_section مطلوب."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = (
            SubMainSection.objects.filter(main_section_id=main, deleted=False)
            .annotate(
                children_count=Count(
                    "children", filter=Q(children__deleted=False)
                )
            )
            .order_by("name", "id")
        )
        if not is_admin(request.user):
            assigned = set(
                request.user.user_sub_mains.values_list("sub_main_id", flat=True)
            )
            # Include ancestors so the tree stays coherent for assigned leaves.
            visible = set(assigned)
            by_id = {row.id: row for row in qs}
            for sid in assigned:
                cur = by_id.get(sid)
                while cur is not None and cur.parent_id is not None:
                    visible.add(cur.parent_id)
                    cur = by_id.get(cur.parent_id)
            qs = [row for row in qs if row.id in visible]
        by_parent: dict[int | None, list] = {}
        for row in qs:
            by_parent.setdefault(row.parent_id, []).append(row)

        def build(parent_id: int | None) -> list[dict]:
            nodes = []
            for row in by_parent.get(parent_id, []):
                nodes.append({
                    "id": row.id,
                    "name": row.name,
                    "main_section": row.main_section_id,
                    "parent": row.parent_id,
                    "is_leaf": int(row.children_count) == 0,
                    "children": build(row.id),
                })
            return nodes

        return Response(build(None))

    @action(
        detail=True,
        methods=["get"],
        url_path="assigned-users",
        permission_classes=[IsAdmin],
    )
    def assigned_users(self, request, pk=None):
        """Users assigned to this leaf/sub-section via UserSubMain."""
        sub = self.get_object()
        users = User.objects.filter(
            deleted=False,
            user_sub_mains__sub_main_id=sub.id,
        ).distinct()
        return Response(_serialize_assigned_users(users))


class TitleCategoryViewSet(viewsets.ModelViewSet):
    queryset = TitleCategory.objects.all().order_by("order", "id")
    serializer_class = TitleCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargePagination

    def get_queryset(self):
        allowed = allowed_title_category_ids(self.request.user)
        qs = TitleCategory.objects.all().order_by("order", "id")
        if allowed is not None:
            qs = qs.filter(id__in=allowed)
        return qs


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.filter(deleted=False).order_by("order", "id")
    serializer_class = TitleSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = LargePagination

    def get_queryset(self):
        user = self.request.user
        allowed = allowed_title_ids(user)
        if allowed is None:
            qs = Title.objects.filter(deleted=False).order_by("order", "id")
        else:
            qs = Title.objects.filter(
                deleted=False, id__in=allowed
            ).order_by("order", "id")
        category = self.request.query_params.get("category")
        if category not in (None, ""):
            qs = qs.filter(category_id=category)
        return qs.select_related("category")

    def perform_destroy(self, instance):
        if instance.is_system:
            raise PermissionDenied(
                "لا يمكن حذف مسمى نظامي — يعتمد عليه moeds. عطّل عرضه من الإعدادات بدلاً من حذفه."
            )
        soft_delete_title(instance, self.request.user)
        log_action(
            self.request,
            "DELETE",
            "Title",
            instance.id,
            {"soft_delete": True, "archived": True},
        )

    def _user_can_access_title_excel(self, user, title: Title) -> bool:
        allowed = allowed_title_ids(user)
        if allowed is None:
            return True
        return title.id in allowed

    @action(
        detail=True,
        methods=["get"],
        url_path="assigned-users",
        permission_classes=[IsAdmin],
    )
    def assigned_users(self, request, pk=None):
        """Users who have access via an assigned TitleCategory containing this title."""
        title = self.get_object()
        if not title.category_id:
            return Response([])
        users = User.objects.filter(
            deleted=False,
            user_title_categories__category_id=title.category_id,
        ).distinct()
        return Response(_serialize_assigned_users(users))

    @action(
        detail=True,
        methods=["get"],
        url_path="excel-template",
        permission_classes=[CanWriteInfo],
    )
    def excel_template(self, request, pk=None):
        title = self.get_object()
        if not self._user_can_access_title_excel(request.user, title):
            raise PermissionDenied("ليس لديك صلاحية على هذا العنوان.")
        handler = get_handler_for_title(title)
        sub_main_id = self._parse_optional_sub_main_id(request)
        if sub_main_id is not None:
            self._ensure_sub_main_access(request.user, sub_main_id)
        # The long, one-row-per-indicator sheet is the house format; ?layout=wide
        # still returns the one-column-per-field sheet. A multi_record title has
        # no long form, so the default quietly falls back rather than failing --
        # but an explicit ?layout=measures on such a title is answered with an error.
        requested_layout = request.query_params.get("layout")
        layout = (requested_layout or DEFAULT_TEMPLATE_LAYOUT).strip().lower()
        try:
            data = handler.build_template_bytes(
                title, sub_main_id=sub_main_id, layout=layout
            )
        except LayoutNotSupported as exc:
            if requested_layout:
                raise ValidationError({"layout": str(exc)}) from exc
            layout = "wide"
            data = handler.build_template_bytes(
                title, sub_main_id=sub_main_id, layout=layout
            )
        safe_name = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", title.name)[:40]
        suffix = "measures" if layout == "measures" else "template"
        filename = f"{safe_name}-{suffix}.xlsx"
        response = HttpResponse(
            data,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @action(
        detail=True,
        methods=["get"],
        url_path="excel-export",
        permission_classes=[CanWriteInfo],
    )
    def excel_export(self, request, pk=None):
        """Export accepted Info for a report date into the Attribute-driven Excel shape."""
        title = self.get_object()
        if not self._user_can_access_title_excel(request.user, title):
            raise PermissionDenied("ليس لديك صلاحية على هذا العنوان.")
        report_date = (request.query_params.get("report_date") or "").strip()
        if not report_date:
            raise ValidationError({"report_date": "التاريخ مطلوب."})
        sub_main_id = self._parse_optional_sub_main_id(request)
        if sub_main_id is not None:
            self._ensure_sub_main_access(request.user, sub_main_id)
        handler = get_handler_for_title(title)
        if not hasattr(handler, "build_export_bytes"):
            raise ValidationError(
                {"detail": "تصدير البيانات غير مدعوم لهذا العنوان."}
            )
        data = handler.build_export_bytes(
            title, report_date=report_date, sub_main_id=sub_main_id
        )
        safe_name = re.sub(r"[^\w\u0600-\u06FF\-]+", "_", title.name)[:40]
        filename = f"{safe_name}-{report_date}.xlsx"
        response = HttpResponse(
            data,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @action(
        detail=True,
        methods=["post"],
        url_path="excel-import",
        permission_classes=[CanWriteInfo],
        parser_classes=[parsers.MultiPartParser, parsers.FormParser],
    )
    def excel_import(self, request, pk=None):
        title = self.get_object()
        if not self._user_can_access_title_excel(request.user, title):
            raise PermissionDenied("ليس لديك صلاحية على هذا العنوان.")
        handler = get_handler_for_title(title)
        upload = request.FILES.get("file")
        if not upload:
            return Response(
                {"detail": "لم يُرفع ملف."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dry_run = str(request.query_params.get("dry_run", "")).lower() in (
            "1",
            "true",
            "yes",
        )
        sub_main_id = self._parse_optional_sub_main_id(request)
        if sub_main_id is not None:
            self._ensure_sub_main_access(request.user, sub_main_id)

        def _log(details):
            log_action(request, "CREATE", "Info", details=details)

        result = handler.import_workbook(
            title=title,
            user=request.user,
            file_obj=upload,
            dry_run=dry_run,
            log_action=_log if not dry_run else None,
            sub_main_id=sub_main_id,
        )
        return Response(result, status=status.HTTP_200_OK)

    def _parse_optional_sub_main_id(self, request) -> int | None:
        raw = request.query_params.get("sub_main_id")
        if raw in (None, ""):
            raw = request.data.get("sub_main_id")
        if raw in (None, ""):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                {"sub_main_id": "معرّف القسم الفرعي غير صالح."}) from exc

    def _ensure_sub_main_access(self, user, sub_main_id: int) -> None:
        if not SubMainSection.objects.filter(pk=sub_main_id).exists():
            raise ValidationError(
                {"sub_main_id": "القسم الفرعي المحدد غير موجود."})
        if user.is_staff or user.is_superuser:
            return
        if not user.user_sub_mains.filter(sub_main_id=sub_main_id).exists():
            raise PermissionDenied("ليس لديك صلاحية على هذا القسم الفرعي.")


class AttributeViewSet(viewsets.ModelViewSet):
    queryset = Attribute.objects.all().order_by("id")
    serializer_class = AttributeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        allowed = allowed_title_ids(user)
        qs = Attribute.objects.filter(
            Q(title__isnull=True) | Q(title__deleted=False)
        ).order_by("order", "id")
        if allowed is not None:
            qs = qs.filter(title_id__in=allowed)
        title = self.request.query_params.get("title")
        if title:
            qs = qs.filter(title_id=title)
        return qs

    def perform_destroy(self, instance):
        if instance.is_system:
            raise PermissionDenied(
                "لا يمكن حذف حقل نظامي — يعتمد عليه moeds. عطّل عرضه من الإعدادات بدلاً من حذفه."
            )
        instance.delete()


class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all().order_by("id")
    serializer_class = OptionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset().select_related("attribute")
        allowed = allowed_title_ids(self.request.user)
        if allowed is not None:
            qs = qs.filter(attribute__title_id__in=allowed)
        attr = self.request.query_params.get("attribute")
        if attr:
            qs = qs.filter(attribute_id=attr)
        return qs


class EntityOptionsView(APIView):
    """Dropdown options for Form Builder entity attribute types."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, entity_type: str):
        if entity_type not in ENTITY_TYPE_SPECS:
            return Response(
                {"detail": f"نوع كيان غير معروف: {entity_type}"},
                status=status.HTTP_404_NOT_FOUND,
            )
        query = request.query_params.get("q", "")
        try:
            limit = int(request.query_params.get("limit", "100"))
        except (TypeError, ValueError):
            limit = 100
        try:
            options = list_entity_options(
                entity_type, query=query, limit=limit)
        except Exception:
            # Sector tables unavailable (sqlite / offline) — empty list, not 500.
            options = []
        return Response(options)
