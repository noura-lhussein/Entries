from django.contrib.auth import get_user_model
from dynamic_forms.user_username import assert_email_available_for_parent, unique_email
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from ..models import ProjectUserAssignment
from ..permissions import CanManageBudgetUsers
from ..scoping import (
    get_user_foundation_id,
    is_system_admin,
    user_can_manage_budget_users,
    user_is_foundation_budget_manager,
)
from ..serializers.budget_user_serializers import (
    BUDGET_USER_FIELDS,
    BudgetUserCreateSerializer,
    BudgetUserSerializer,
    BudgetUserUpdateSerializer,
)
from ..serializers.project_assignment_serializers import (
    UserProjectAssignmentsSerializer,
)

User = get_user_model()


class BudgetUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(
        deleted=False,
        budget_scope__isnull=False,
    ).select_related("budget_scope__foundation")
    permission_classes = [CanManageBudgetUsers]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["email", "full_name"]
    ordering_fields = ["id", "email", "full_name", "date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return BudgetUserCreateSerializer
        if self.action in ("update", "partial_update"):
            return BudgetUserUpdateSerializer
        return BudgetUserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if is_system_admin(user):
            return qs.order_by("id")
        foundation_id = get_user_foundation_id(user)
        if foundation_id is None:
            return qs.none()
        qs = qs.filter(budget_scope__foundation_id=foundation_id)
        if self.action == "list":
            qs = qs.exclude(pk=user.pk)
        return qs.order_by("id")

    def _check_permission_escalation(self, requester, data):
        if is_system_admin(requester) or getattr(requester, "can_manage_budget", False):
            return
        denied = [
            flag
            for flag in BUDGET_USER_FIELDS
            if data.get(flag) and not getattr(requester, flag, False)
        ]
        if denied:
            raise PermissionDenied(f"لا تملك صلاحية منح: {', '.join(denied)}")

    def perform_create(self, serializer):
        requester = self.request.user
        if not user_can_manage_budget_users(requester):
            raise PermissionDenied("لا تملك صلاحية إدارة مستخدمي الميزانية.")
        self._check_permission_escalation(requester, serializer.validated_data)

        desired = serializer.validated_data.get("email", "")
        assert_email_available_for_parent(requester, desired)
        final_email = unique_email(desired, parent=requester)
        serializer.save(email=final_email)

    def perform_update(self, serializer):
        requester = self.request.user
        if not user_can_manage_budget_users(requester):
            raise PermissionDenied("لا تملك صلاحية إدارة مستخدمي الميزانية.")
        self._check_permission_escalation(requester, serializer.validated_data)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deleted = True
        instance.is_active = False
        suffix = f"__deleted_{instance.id}"
        if not instance.email.endswith(suffix):
            instance.email = f"{instance.email}{suffix}"[:254]
        instance.save(update_fields=["deleted", "is_active", "email"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "put"], url_path="assignments")
    def assignments(self, request, pk=None):
        if not user_can_manage_budget_users(request.user):
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")
        target_user = self.get_object()
        if request.method == "GET":
            project_ids = list(
                ProjectUserAssignment.objects.filter(user=target_user).values_list(
                    "project_id", flat=True
                )
            )
            return Response({"project_ids": project_ids})

        if not user_is_foundation_budget_manager(request.user):
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")
        serializer = UserProjectAssignmentsSerializer(
            data=request.data,
            context={"request": request, "target_user": target_user},
        )
        serializer.is_valid(raise_exception=True)
        project_ids = serializer.save()
        return Response({"project_ids": project_ids})
