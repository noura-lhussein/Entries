from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from ..models import Title, UserSubMain, UserTitle, UserTitleCategory
from ..pagination import LargePagination
from ..permissions import IsAdmin, IsAdminOrCanAddUser
from ..serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserSubMainSerializer,
    UserTitleCategorySerializer,
    UserTitleSerializer,
    UserUpdateSerializer,
)
from ..user_username import assert_email_available_for_parent, unique_email

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LargePagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["email", "full_name"]
    ordering_fields = ["id", "email", "full_name", "date_joined"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAdminOrCanAddUser()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            qs = User.objects.filter(deleted=False).order_by("id")
        else:
            subordinate_ids = [u.id for u in user.get_all_subordinates()]
            qs = User.objects.filter(
                id__in=subordinate_ids, deleted=False).order_by("id")
        if getattr(self, "action", None) == "list":
            qs = qs.exclude(pk=user.pk)
            qs = self._apply_list_filters(qs)
        return qs

    GRANTABLE_PERMS = [
        "can_write_info",
        "can_view_info",
        "can_confirm_info",
        "can_export_reports",
        "can_add_user",
        "can_view_budget",
        "can_write_budget",
        "can_manage_budget_users",
        "can_manage_budget",
        "can_manage_reference_data",
        # moeds portal flags not tied to a sector (portal_sectors is guarded
        # separately in _check_permission_escalation).
        "is_admin",
        "can_manage_datasets",
        "can_manage_control_panel",
    ]

    def _apply_list_filters(self, qs):
        params = self.request.query_params
        raw_active = params.get("is_active")
        if raw_active is not None and raw_active != "":
            qs = qs.filter(is_active=str(raw_active).lower() in ("1", "true", "yes"))

        sub_main = params.get("sub_main")
        if sub_main:
            qs = qs.filter(user_sub_mains__sub_main_id=sub_main).distinct()

        title = params.get("title")
        if title:
            category_id = (
                Title.objects.filter(pk=title)
                .values_list("category_id", flat=True)
                .first()
            )
            if category_id:
                qs = qs.filter(
                    user_title_categories__category_id=category_id
                ).distinct()
            else:
                qs = qs.none()

        title_category = params.get("title_category")
        if title_category:
            qs = qs.filter(
                user_title_categories__category_id=title_category
            ).distinct()

        parent = params.get("parent")
        if parent:
            qs = qs.filter(parent_id=parent)

        for perm in self.GRANTABLE_PERMS:
            raw = params.get(perm)
            if raw is None or raw == "":
                continue
            qs = qs.filter(**{perm: str(raw).lower() in ("1", "true", "yes")})

        return qs

    def _check_permission_escalation(self, requester, data):
        if requester.is_portal_admin:
            return
        denied = [p for p in self.GRANTABLE_PERMS if data.get(
            p) and not getattr(requester, p)]
        if denied:
            raise PermissionDenied(f"لا تملك صلاحية منح: {', '.join(denied)}")
        # A non-admin cannot grant a moeds portal sector it does not hold.
        if "portal_sectors" in data:
            extra = set(data["portal_sectors"]) - set(requester.portal_sectors or [])
            if extra:
                raise PermissionDenied(
                    f"لا تملك صلاحية منح قطاعات البوابة: {', '.join(sorted(extra))}"
                )

    def perform_create(self, serializer):
        requester = self.request.user
        is_admin = requester.is_portal_admin
        self._check_permission_escalation(requester, serializer.validated_data)

        desired = serializer.validated_data.get("email", "")
        assert_email_available_for_parent(requester, desired)
        final_email = unique_email(desired, parent=requester)

        kwargs = {
            "is_staff": False,
            "is_superuser": False,
            "email": final_email,
        }
        if not is_admin:
            kwargs["parent"] = requester
            kwargs["can_add_user"] = False
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        self._check_permission_escalation(
            self.request.user, serializer.validated_data)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted = True
        instance.is_active = False
        # Free the email for reuse by suffixing the row id on soft delete.
        suffix = f"__deleted_{instance.id}"
        if not instance.email.endswith(suffix):
            instance.email = f"{instance.email}{suffix}"[:254]
        instance.save(update_fields=["deleted", "is_active", "email"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubMainViewSet(viewsets.ModelViewSet):
    queryset = UserSubMain.objects.all()
    serializer_class = UserSubMainSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "sub_main")
        user = self.request.query_params.get("user")
        sub_main = self.request.query_params.get("sub_main")
        if user:
            qs = qs.filter(user_id=user)
        if sub_main:
            qs = qs.filter(sub_main_id=sub_main)
        return qs


class UserTitleViewSet(viewsets.ModelViewSet):
    queryset = UserTitle.objects.all()
    serializer_class = UserTitleSerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "title")
        user = self.request.query_params.get("user")
        title = self.request.query_params.get("title")
        if user:
            qs = qs.filter(user_id=user)
        if title:
            qs = qs.filter(title_id=title)
        return qs


class UserTitleCategoryViewSet(viewsets.ModelViewSet):
    queryset = UserTitleCategory.objects.all()
    serializer_class = UserTitleCategorySerializer
    permission_classes = [IsAdmin]
    pagination_class = LargePagination

    def get_queryset(self):
        qs = super().get_queryset().select_related("user", "category")
        user = self.request.query_params.get("user")
        category = self.request.query_params.get("category")
        if user:
            qs = qs.filter(user_id=user)
        if category:
            qs = qs.filter(category_id=category)
        return qs
