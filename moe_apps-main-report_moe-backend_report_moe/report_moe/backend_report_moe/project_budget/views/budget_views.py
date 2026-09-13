from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..category_tree import (
    build_category_lookup,
    filter_categories_by_project_type,
)
from ..models import (
    AnnualBudget,
    Currency,
    Foundation,
    MeasureUnit,
    Milestone,
    MilestoneTransaction,
    Policy,
    Project,
    ProjectCategory,
    ProjectChangeLog,
    ProjectTransaction,
    ProjectType,
    ProjectUserAssignment,
    Responsible,
    Target,
    Transaction,
)
from ..pagination import BudgetPagination
from ..permissions import (
    CanManageBudgetUsers,
    CanManageResponsiblesOrReadOnly,
    IsAnnualBudgetAdminOrReadOnly,
    IsBudgetAdminOrReadOnly,
    IsReferenceDataAdminOrReadOnly,
)
from ..scoping import (
    filter_queryset_by_project_scope,
    filter_queryset_by_user_foundation,
    user_can_manage_budget_users,
    user_is_foundation_budget_manager,
)
from ..serializers import (
    AnnualBudgetOptionSerializer,
    AnnualBudgetSerializer,
    CurrencyOptionSerializer,
    CurrencySerializer,
    FoundationOptionSerializer,
    FoundationSerializer,
    MilestoneSerializer,
    MilestoneTransactionSerializer,
    PreviousProjectOptionSerializer,
    ProjectCategoryOptionSerializer,
    ProjectCategorySerializer,
    ProjectChangeLogSerializer,
    ProjectSerializer,
    ProjectTransactionSerializer,
    ProjectTypeOptionSerializer,
    ProjectTypeSerializer,
    ResponsibleSerializer,
    TransactionSerializer,
)
from ..serializers.budget_serializers import (
    MeasureUnitOptionSerializer,
    MeasureUnitSerializer,
    PolicyOptionSerializer,
    PolicySerializer,
    TargetOptionSerializer,
    TargetSerializer,
)
from ..serializers.project_assignment_serializers import (
    ProjectAssignmentCreateSerializer,
    ProjectAssignmentUserSerializer,
)

User = get_user_model()


class BudgetSelectOptionsMixin:
    """Lightweight id/name lists for dropdowns — GET .../options/."""

    option_serializer_class = None

    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        if self.option_serializer_class is None:
            return Response(
                {"detail": "Options not available."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        qs = self.filter_queryset(self.get_queryset())
        exclude_id = request.query_params.get("exclude")
        if exclude_id:
            try:
                qs = qs.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid exclude."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer = self.option_serializer_class(qs, many=True)
        return Response(serializer.data)


class BudgetModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsBudgetAdminOrReadOnly]
    pagination_class = BudgetPagination

    def perform_create(self, serializer):
        kwargs = {}
        model = serializer.Meta.model
        if hasattr(model, "created_by"):
            kwargs["created_by"] = self.request.user
        if hasattr(model, "updated_by"):
            kwargs["updated_by"] = self.request.user
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        kwargs = {}
        model = serializer.Meta.model
        if hasattr(model, "updated_by"):
            kwargs["updated_by"] = self.request.user
        serializer.save(**kwargs)

    def perform_destroy(self, instance):
        if hasattr(instance, "assert_can_delete"):
            instance.assert_can_delete()
        if hasattr(instance, "deleted"):
            instance.deleted = True
            instance.deleted_at = timezone.now()
            if hasattr(instance, "deleted_by"):
                instance.deleted_by = self.request.user
            instance.save()
            return
        super().perform_destroy(instance)


class ReferenceDataModelViewSet(BudgetModelViewSet):
    permission_classes = [IsReferenceDataAdminOrReadOnly]


class ProjectCategoryViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = ProjectCategory.objects.select_related(
        "parent", "created_by", "updated_by"
    ).filter(deleted=False)
    serializer_class = ProjectCategorySerializer
    option_serializer_class = ProjectCategoryOptionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        project_type_id = self.request.query_params.get("project_type")
        if project_type_id:
            qs = filter_categories_by_project_type(qs, project_type_id)
        parent_id = self.request.query_params.get("parent")
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        root_only = self.request.query_params.get("root")
        if root_only in ("1", "true", "yes"):
            qs = qs.filter(parent__isnull=True)
        return qs

    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        qs = self.filter_queryset(self.get_queryset())
        exclude_id = request.query_params.get("exclude")
        if exclude_id:
            try:
                qs = qs.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid exclude."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        categories = list(qs)
        by_id = build_category_lookup(categories)
        serializer = self.option_serializer_class(
            categories,
            many=True,
            context={"category_by_id": by_id, "request": request},
        )
        return Response(serializer.data)


class FoundationViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = Foundation.objects.filter(deleted=False)
    serializer_class = FoundationSerializer
    option_serializer_class = FoundationOptionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_queryset_by_user_foundation(qs, self.request.user, "pk")


class ResponsibleViewSet(BudgetModelViewSet):
    queryset = Responsible.objects.select_related(
        "foundation").filter(deleted=False)
    serializer_class = ResponsibleSerializer
    permission_classes = [CanManageResponsiblesOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_queryset_by_user_foundation(qs, self.request.user)
        foundation_id = self.request.query_params.get("foundation")
        if foundation_id:
            qs = qs.filter(foundation_id=foundation_id)
        return qs


class ProjectTypeViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = ProjectType.objects.filter(deleted=False)
    serializer_class = ProjectTypeSerializer
    option_serializer_class = ProjectTypeOptionSerializer


class CurrencyViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = Currency.objects.filter(deleted=False)
    serializer_class = CurrencySerializer
    option_serializer_class = CurrencyOptionSerializer


class AnnualBudgetViewSet(BudgetSelectOptionsMixin, BudgetModelViewSet):
    queryset = AnnualBudget.objects.select_related(
        "project_type", "currency").all()
    serializer_class = AnnualBudgetSerializer
    option_serializer_class = AnnualBudgetOptionSerializer
    permission_classes = [IsAnnualBudgetAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        project_type_id = self.request.query_params.get("project_type")
        if project_type_id:
            qs = qs.filter(project_type_id=project_type_id)
        year = self.request.query_params.get("year")
        if year:
            qs = qs.filter(year=year)
        return qs


class ProjectViewSet(BudgetModelViewSet):
    queryset = Project.objects.select_related(
        "annual_budget",
        "annual_budget__project_type",
        "foundation",
        "governorate",
        "district",
        "subdistrict",
        "community",
        "previous_project",
        "target",
        "policy",
        "quantitative_target_unit",
    ).filter(deleted=False)
    serializer_class = ProjectSerializer
    search_fields = ["name_ar", "name_en", "code", "description"]
    ordering_fields = ["created_at", "name_ar", "start_date", "status"]

    def perform_create(self, serializer):
        super().perform_create(serializer)
        user = self.request.user
        from ..scoping import user_skips_project_filter

        if not user_skips_project_filter(user):
            ProjectUserAssignment.objects.get_or_create(
                project=serializer.instance,
                user=user,
                defaults={"assigned_by": user},
            )

    def perform_destroy(self, instance):
        from ..project_change_log import log_project_deleted

        log_project_deleted(instance, request=self.request)
        super().perform_destroy(instance)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_queryset_by_project_scope(qs, self.request.user)
        annual_budget_id = self.request.query_params.get("annual_budget")
        if annual_budget_id:
            qs = qs.filter(annual_budget_id=annual_budget_id)
        project_type_id = self.request.query_params.get("project_type")
        if project_type_id:
            qs = qs.filter(annual_budget__project_type_id=project_type_id)
        foundation_id = self.request.query_params.get("foundation")
        if foundation_id:
            qs = qs.filter(foundation_id=foundation_id)
        community_id = self.request.query_params.get("community")
        if community_id:
            qs = qs.filter(community_id=community_id)
        subdistrict_id = self.request.query_params.get("subdistrict")
        if subdistrict_id:
            qs = qs.filter(subdistrict_id=subdistrict_id)
        district_id = self.request.query_params.get("district")
        if district_id:
            qs = qs.filter(district_id=district_id)
        governorate_id = self.request.query_params.get("governorate")
        if governorate_id:
            qs = qs.filter(governorate_id=governorate_id)
        status_value = self.request.query_params.get("status")
        if status_value:
            qs = qs.filter(status=status_value)
        year = self.request.query_params.get("year")
        if year:
            try:
                qs = qs.filter(annual_budget__year=int(year))
            except (TypeError, ValueError):
                pass
        return qs

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        from ..project_dashboard import build_project_dashboard

        qs = self.get_queryset()
        return Response(build_project_dashboard(qs))

    @action(detail=False, methods=["get"], url_path="map-points")
    def map_points(self, request):
        """Lean geo points for project distribution map (scoped + filtered)."""
        from django.db.models import Q
        from django.db.models.functions import Coalesce

        qs = self.get_queryset().select_related("community", "governorate")
        total_projects = qs.count()

        geo_qs = qs.filter(
            Q(latitude__isnull=False, longitude__isnull=False)
            | Q(
                community__latitude__isnull=False,
                community__longitude__isnull=False,
            )
        ).annotate(
            map_latitude=Coalesce("latitude", "community__latitude"),
            map_longitude=Coalesce("longitude", "community__longitude"),
        )
        with_coordinates = geo_qs.count()

        max_points = 5000
        rows = geo_qs.values(
            "id",
            "name_ar",
            "name_en",
            "code",
            "status",
            "governorate_id",
            "governorate__name_ar",
            "community_id",
            "community__name_ar",
            "map_latitude",
            "map_longitude",
        )[:max_points]

        results = []
        for row in rows:
            lat = row["map_latitude"]
            lng = row["map_longitude"]
            if lat is None or lng is None:
                continue
            results.append(
                {
                    "id": row["id"],
                    "name_ar": row["name_ar"],
                    "name_en": row["name_en"] or "",
                    "code": row["code"],
                    "status": row["status"],
                    "governorate_id": row["governorate_id"],
                    "governorate_name": row["governorate__name_ar"] or "",
                    "community_id": row["community_id"],
                    "community_name": row["community__name_ar"] or "",
                    "latitude": float(lat),
                    "longitude": float(lng),
                }
            )

        return Response(
            {
                "count": len(results),
                "total_projects": total_projects,
                "without_coordinates": max(total_projects - with_coordinates, 0),
                "truncated": with_coordinates > max_points,
                "results": results,
            }
        )

    @action(detail=False, methods=["get"], url_path="eligible-previous")
    def eligible_previous(self, request):
        annual_budget_id = request.query_params.get("annual_budget")
        if not annual_budget_id:
            return Response(
                {"detail": "annual_budget is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            budget = AnnualBudget.objects.get(pk=int(annual_budget_id))
        except (ValueError, TypeError, AnnualBudget.DoesNotExist):
            return Response(
                {"detail": "Invalid annual_budget."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = (
            self.get_queryset()
            .filter(annual_budget__year__lt=budget.year)
            .order_by("-annual_budget__year", "code")
        )
        exclude_id = request.query_params.get("exclude")
        if exclude_id:
            try:
                qs = qs.exclude(pk=int(exclude_id))
            except (ValueError, TypeError):
                return Response(
                    {"detail": "Invalid exclude."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = PreviousProjectOptionSerializer(qs, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="assignments",
        permission_classes=[CanManageBudgetUsers],
    )
    def assignments(self, request, pk=None):
        if not user_can_manage_budget_users(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")
        project = self.get_object()

        if request.method == "GET":
            users = User.objects.filter(
                project_assignments__project=project,
                deleted=False,
            ).select_related("budget_scope")
            serializer = ProjectAssignmentUserSerializer(users, many=True)
            return Response(serializer.data)

        if not user_is_foundation_budget_manager(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")

        serializer = ProjectAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user = serializer.validated_data["user_id"]
        assignment = ProjectUserAssignment(
            project=project,
            user=target_user,
            assigned_by=request.user,
        )
        assignment.full_clean()
        assignment.save()
        return Response(
            ProjectAssignmentUserSerializer(target_user).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"assignments/(?P<user_id>[^/.]+)",
        permission_classes=[CanManageBudgetUsers],
    )
    def remove_assignment(self, request, pk=None, user_id=None):
        if not user_can_manage_budget_users(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")
        if not user_is_foundation_budget_manager(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("لا تملك صلاحية إدارة الإسناد.")
        project = self.get_object()
        deleted, _ = ProjectUserAssignment.objects.filter(
            project=project,
            user_id=user_id,
        ).delete()
        if not deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="change-log")
    def change_log(self, request, pk=None):
        project = self.get_object()
        qs = project.change_logs.select_related("changed_by").all()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ProjectChangeLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProjectChangeLogSerializer(qs, many=True)
        return Response(serializer.data)


class ProjectChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectChangeLogSerializer
    permission_classes = [IsBudgetAdminOrReadOnly]
    pagination_class = BudgetPagination

    def get_queryset(self):
        from django.db.models import Q

        qs = ProjectChangeLog.objects.select_related("project", "changed_by").filter(
            project__deleted=False
        )
        qs = filter_queryset_by_project_scope(
            qs,
            self.request.user,
            foundation_path="project__foundation_id",
            project_path="project_id",
        )

        params = self.request.query_params
        project_id = params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        action = params.get("action")
        if action:
            qs = qs.filter(action=action)
        field_name = params.get("field_name")
        if field_name:
            qs = qs.filter(field_name=field_name)
        changed_by = params.get("changed_by")
        if changed_by:
            qs = qs.filter(changed_by_id=changed_by)
        changed_after = params.get("changed_after")
        if changed_after:
            qs = qs.filter(changed_at__date__gte=changed_after)
        changed_before = params.get("changed_before")
        if changed_before:
            qs = qs.filter(changed_at__date__lte=changed_before)
        search = params.get("search")
        if search:
            qs = qs.filter(
                Q(field_label__icontains=search)
                | Q(old_value__icontains=search)
                | Q(new_value__icontains=search)
                | Q(project__name_ar__icontains=search)
                | Q(project__code__icontains=search)
                | Q(changed_by__email__icontains=search)
                | Q(changed_by__full_name__icontains=search)
            )
        return qs


class MilestoneViewSet(BudgetModelViewSet):
    queryset = Milestone.objects.select_related(
        "project",
        "project__foundation",
        "parent",
        "responsible",
        "category",
    ).filter(deleted=False)
    serializer_class = MilestoneSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_queryset_by_project_scope(
            qs,
            self.request.user,
            foundation_path="project__foundation_id",
            project_path="project_id",
        )
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)
        parent_id = self.request.query_params.get("parent")
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        root_only = self.request.query_params.get("root")
        if root_only in ("1", "true", "yes"):
            qs = qs.filter(parent__isnull=True)
        return qs


class TargetViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = Target.objects.filter(deleted=False)
    serializer_class = TargetSerializer
    option_serializer_class = TargetOptionSerializer


class PolicyViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = Policy.objects.filter(deleted=False)
    serializer_class = PolicySerializer
    option_serializer_class = PolicyOptionSerializer


class MeasureUnitViewSet(BudgetSelectOptionsMixin, ReferenceDataModelViewSet):
    queryset = MeasureUnit.objects.filter(deleted=False)
    serializer_class = MeasureUnitSerializer
    option_serializer_class = MeasureUnitOptionSerializer


class TransactionViewSet(BudgetModelViewSet):
    queryset = Transaction.objects.filter(deleted=False)
    serializer_class = TransactionSerializer


class ProjectTransactionViewSet(BudgetModelViewSet):
    queryset = ProjectTransaction.objects.select_related(
        "project", "transaction", "currency"
    ).all()
    serializer_class = ProjectTransactionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_queryset_by_project_scope(
            qs,
            self.request.user,
            foundation_path="project__foundation_id",
            project_path="project_id",
        )
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        transaction_id = self.request.query_params.get("transaction")
        if transaction_id:
            qs = qs.filter(transaction_id=transaction_id)
        return qs


class MilestoneTransactionViewSet(BudgetModelViewSet):
    queryset = MilestoneTransaction.objects.select_related(
        "milestone",
        "milestone__project",
        "transaction",
        "currency",
    ).all()
    serializer_class = MilestoneTransactionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        qs = filter_queryset_by_project_scope(
            qs,
            self.request.user,
            foundation_path="milestone__project__foundation_id",
            project_path="milestone__project_id",
        )
        milestone_id = self.request.query_params.get("milestone")
        if milestone_id:
            qs = qs.filter(milestone_id=milestone_id)
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(milestone__project_id=project_id)
        transaction_id = self.request.query_params.get("transaction")
        if transaction_id:
            qs = qs.filter(transaction_id=transaction_id)
        return qs
