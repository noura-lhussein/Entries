from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ..category_tree import category_breadcrumb
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
    Responsible,
    Target,
    Transaction,
)
from ..project_change_log import extract_change_meta


class CleanModelSerializer(serializers.ModelSerializer):
    """Run model clean() so relationship invariants are enforced through the API."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance or self.Meta.model()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                exc.message_dict or exc.messages) from exc
        return attrs


class AuditReadFieldsMixin(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.email", read_only=True, allow_null=True
    )
    updated_by_name = serializers.CharField(
        source="updated_by.email", read_only=True, allow_null=True
    )


class ProjectCategorySerializer(AuditReadFieldsMixin, CleanModelSerializer):
    parent_name = serializers.CharField(
        source="parent.name_ar", read_only=True, allow_null=True)

    class Meta:
        model = ProjectCategory
        fields = (
            "id",
            "parent",
            "parent_name",
            "code",
            "name_ar",
            "name_en",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = (
            "id",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )


class FoundationSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Foundation
        fields = (
            "id",
            "name_ar",
            "name_en",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class ResponsibleSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    foundation_name = serializers.CharField(
        source="foundation.name_ar", read_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from ..scoping import get_user_foundation_id, is_system_admin

            if not is_system_admin(request.user):
                foundation_id = get_user_foundation_id(request.user)
                if foundation_id is None:
                    raise serializers.ValidationError(
                        {"foundation": "لا توجد مؤسسة مرتبطة بحسابك."}
                    )
                foundation = attrs.get(
                    "foundation",
                    getattr(self.instance, "foundation", None),
                )
                if foundation is not None and foundation.pk != foundation_id:
                    raise serializers.ValidationError(
                        {"foundation": "لا يمكنك اختيار مؤسسة خارج نطاقك."}
                    )
                if foundation is None:
                    attrs["foundation"] = Foundation.objects.get(
                        pk=foundation_id)
        return attrs

    class Meta:
        model = Responsible
        fields = (
            "id",
            "foundation",
            "foundation_name",
            "name_ar",
            "name_en",
            "phone",
            "email",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class ProjectTypeSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = (
            "id",
            "name_ar",
            "name_en",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class CurrencySerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = (
            "id",
            "code",
            "name_ar",
            "name_en",
            "symbol",
            "exchange_rate",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class AnnualBudgetSerializer(serializers.ModelSerializer):
    project_type_name = serializers.CharField(
        source="project_type.name_ar", read_only=True)
    currency_code = serializers.CharField(
        source="currency.code", read_only=True)

    class Meta:
        model = AnnualBudget
        fields = (
            "id",
            "project_type",
            "project_type_name",
            "currency",
            "currency_code",
            "code",
            "year",
            "amount",
            "notes",
            "approved_at",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )
        read_only_fields = ("id", "code", "created_at", "updated_at",
                            "created_by", "updated_by")


class ProjectSerializer(CleanModelSerializer):
    annual_budget_year = serializers.IntegerField(
        source="annual_budget.year", read_only=True)
    target_name = serializers.CharField(
        source="target.name_ar", read_only=True, allow_null=True)
    policy_name = serializers.CharField(
        source="policy.name_ar", read_only=True, allow_null=True)
    quantitative_target_unit_name = serializers.CharField(
        source="quantitative_target_unit.name_ar", read_only=True, allow_null=True
    )
    quantitative_target_unit_symbol = serializers.CharField(
        source="quantitative_target_unit.symbol", read_only=True, allow_null=True
    )
    annual_budget_code = serializers.CharField(
        source="annual_budget.code", read_only=True)
    project_type_id = serializers.IntegerField(
        source="annual_budget.project_type_id", read_only=True
    )
    project_type_name = serializers.CharField(
        source="annual_budget.project_type.name_ar", read_only=True
    )
    foundation_name = serializers.CharField(
        source="foundation.name_ar", read_only=True)
    governorate_name = serializers.CharField(
        source="governorate.name_ar", read_only=True)
    district_name = serializers.CharField(
        source="district.name_ar", read_only=True)
    subdistrict_name = serializers.CharField(
        source="subdistrict.name_ar", read_only=True)
    community_name = serializers.CharField(
        source="community.name_ar", read_only=True)
    previous_project_name = serializers.CharField(
        source="previous_project.name_ar", read_only=True, allow_null=True
    )

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from ..scoping import (
                assert_project_accessible,
                get_user_foundation_id,
                is_system_admin,
                user_skips_project_filter,
            )

            if not is_system_admin(request.user):
                foundation_id = get_user_foundation_id(request.user)
                if foundation_id is None:
                    raise serializers.ValidationError(
                        {"foundation": "لا توجد مؤسسة مرتبطة بحسابك."}
                    )
                foundation = attrs.get(
                    "foundation",
                    getattr(self.instance, "foundation", None),
                )
                if foundation is not None and foundation.pk != foundation_id:
                    raise serializers.ValidationError(
                        {"foundation": "لا يمكنك اختيار مؤسسة خارج نطاقك."}
                    )
                if foundation is None:
                    attrs["foundation"] = Foundation.objects.get(
                        pk=foundation_id)

            annual_budget = attrs.get(
                "annual_budget",
                getattr(self.instance, "annual_budget", None),
            )
            if annual_budget is None and self.instance:
                annual_budget = self.instance.annual_budget
            if annual_budget is None:
                raise serializers.ValidationError(
                    {"annual_budget": "الموازنة السنوية مطلوبة."}
                )

            if self.instance is not None and not user_skips_project_filter(request.user):
                assert_project_accessible(request.user, self.instance)
        community = attrs.get("community") or getattr(
            self.instance, "community", None)
        if community is None and self.instance is None:
            raise serializers.ValidationError(
                {"community": "التجمّع (الموقع) مطلوب."})
        return super().validate(attrs)

    def _sync_completion(self, project):
        """Recompute completion from milestones unless the user set it manually."""
        if not project.completion_is_manual:
            from ..completion import update_project_completion

            update_project_completion(project.pk, force=True)
            project.refresh_from_db(fields=["percentage_completion"])

    def create(self, validated_data):
        request = self.context.get("request")
        change_meta = extract_change_meta(getattr(self, "initial_data", None))
        project = super().create(validated_data)
        self._sync_completion(project)
        from ..project_change_log import log_project_created, refresh_project_for_snapshot

        log_project_created(
            refresh_project_for_snapshot(project),
            request=request,
            change_meta=change_meta,
        )
        return project

    def update(self, instance, validated_data):
        request = self.context.get("request")
        change_meta = extract_change_meta(getattr(self, "initial_data", None))
        from ..project_change_log import (
            log_project_changes,
            refresh_project_for_snapshot,
            snapshot_project,
        )

        old_snapshot = snapshot_project(refresh_project_for_snapshot(instance))
        project = super().update(instance, validated_data)
        self._sync_completion(project)
        new_snapshot = snapshot_project(refresh_project_for_snapshot(project))
        log_project_changes(
            project,
            old_snapshot,
            new_snapshot,
            request=request,
            change_meta=change_meta,
            action=ProjectChangeLog.Action.UPDATE,
        )
        return project

    class Meta:
        model = Project
        fields = (
            "id",
            "annual_budget",
            "annual_budget_year",
            "annual_budget_code",
            "project_type_id",
            "project_type_name",
            "foundation",
            "foundation_name",
            "governorate",
            "governorate_name",
            "district",
            "district_name",
            "subdistrict",
            "subdistrict_name",
            "community",
            "community_name",
            "previous_project",
            "previous_project_name",
            "is_round",
            "code",
            "name_ar",
            "name_en",
            "latitude",
            "longitude",
            "percentage_completion",
            "completion_is_manual",
            "proposed_budget",
            "approved_budget",
            "budget_expenditure",
            "status",
            "description",
            "start_date",
            "end_date",
            "target",
            "target_name",
            "policy",
            "policy_name",
            "quantitative_target_value",
            "quantitative_target_unit",
            "quantitative_target_unit_name",
            "quantitative_target_unit_symbol",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_by",
        )
        read_only_fields = (
            "id",
            "code",
            "governorate",
            "governorate_name",
            "district",
            "district_name",
            "subdistrict",
            "subdistrict_name",
            "target_name",
            "policy_name",
            "quantitative_target_unit_name",
            "quantitative_target_unit_symbol",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_by",
        )


class ProjectChangeLogSerializer(serializers.ModelSerializer):
    project_id = serializers.IntegerField(read_only=True)
    project_name = serializers.CharField(
        source="project.name_ar", read_only=True)
    project_code = serializers.CharField(source="project.code", read_only=True)
    changed_by_name = serializers.SerializerMethodField()
    # Keep response key; source from email for shared User model.
    changed_by_username = serializers.CharField(
        source="changed_by.email", read_only=True, allow_null=True
    )

    class Meta:
        model = ProjectChangeLog
        fields = (
            "id",
            "project_id",
            "project_name",
            "project_code",
            "batch_id",
            "action",
            "field_name",
            "field_label",
            "old_value",
            "new_value",
            "changed_by",
            "changed_by_name",
            "changed_by_username",
            "changed_at",
            "ip_address",
            "client_latitude",
            "client_longitude",
            "user_agent",
        )

    def get_changed_by_name(self, obj):
        user = obj.changed_by
        if not user:
            return ""
        return user.display_name


class PreviousProjectOptionSerializer(serializers.ModelSerializer):
    annual_budget_year = serializers.IntegerField(
        source="annual_budget.year", read_only=True
    )

    class Meta:
        model = Project
        fields = ("id", "code", "name_ar", "annual_budget_year")


class FoundationOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = Foundation
        fields = ("id", "name")


class ProjectCategoryOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)
    parent = serializers.IntegerField(
        source="parent_id", read_only=True, allow_null=True)
    breadcrumb = serializers.SerializerMethodField()
    depth = serializers.SerializerMethodField()

    class Meta:
        model = ProjectCategory
        fields = ("id", "name", "code", "parent", "breadcrumb", "depth")

    def get_breadcrumb(self, obj):
        by_id = self.context.get("category_by_id")
        if not by_id:
            return [obj.name_ar or str(obj.pk)]
        return category_breadcrumb(obj, by_id)

    def get_depth(self, obj):
        return max(0, len(self.get_breadcrumb(obj)) - 1)


class ProjectTypeOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = ProjectType
        fields = ("id", "name")


class CurrencyOptionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Currency
        fields = ("id", "name")

    def get_name(self, obj):
        if obj.code and obj.name_ar:
            return f"{obj.code} — {obj.name_ar}"
        return obj.name_ar or obj.code or str(obj.pk)


class AnnualBudgetOptionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = AnnualBudget
        fields = ("id", "name", "code", "year")

    def get_name(self, obj):
        parts = []
        if obj.code:
            parts.append(obj.code)
        parts.append(str(obj.year))
        project_type = getattr(obj, "project_type", None)
        type_name = getattr(project_type, "name_ar",
                            None) if project_type else None
        if type_name:
            parts.append(type_name)
        return " — ".join(parts)


class MilestoneSerializer(CleanModelSerializer):
    project_name = serializers.CharField(
        source="project.name_ar", read_only=True)
    parent_name = serializers.CharField(
        source="parent.name_ar", read_only=True, allow_null=True)
    responsible_name = serializers.CharField(
        source="responsible.name_ar", read_only=True, allow_null=True
    )
    category_name = serializers.CharField(
        source="category.name_ar", read_only=True, allow_null=True
    )

    def validate(self, attrs):
        from ..category_tree import category_prefix_for_project_type_name
        from ..models import Project, ProjectCategory

        request = self.context.get("request")
        project = attrs.get("project")
        if project is None and self.instance:
            project = self.instance.project

        category = attrs.get("category")
        if category is None and self.instance and "category" not in attrs:
            category = self.instance.category

        if request and request.user.is_authenticated and project is not None:
            from ..scoping import assert_project_accessible

            if isinstance(project, int):
                project = Project.objects.select_related(
                    "annual_budget__project_type"
                ).get(pk=project)
            assert_project_accessible(request.user, project)

        if category is not None and project is not None:
            if isinstance(project, int):
                project = Project.objects.select_related(
                    "annual_budget__project_type"
                ).get(pk=project)
            if isinstance(category, int):
                category = ProjectCategory.objects.get(pk=category)

            prefix = category_prefix_for_project_type_name(
                project.annual_budget.project_type.name_ar
            )
            if prefix and category.code and not category.code.startswith(prefix):
                raise serializers.ValidationError(
                    {
                        "category": (
                            "الفئة لا تتوافق مع نوع المشروع "
                            f"({project.annual_budget.project_type.name_ar})."
                        )
                    }
                )

        return super().validate(attrs)

    class Meta:
        model = Milestone
        fields = (
            "id",
            "project",
            "project_name",
            "parent",
            "parent_name",
            "responsible",
            "responsible_name",
            "category",
            "category_name",
            "name_ar",
            "name_en",
            "latitude",
            "longitude",
            "percentage_completion",
            "start_date",
            "end_date",
            "order",
            "due_date",
            "status",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_by",
        )
        read_only_fields = (
            "id",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_by",
        )


class TransactionSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            "id",
            "name_ar",
            "name_en",
            "disabled",
            "description",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class ProjectTransactionSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(
        source="project.name_ar", read_only=True)
    transaction_name = serializers.CharField(
        source="transaction.name_ar", read_only=True)
    currency_code = serializers.CharField(
        source="currency.code", read_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from ..models import Project
            from ..scoping import assert_project_accessible

            project = attrs.get("project")
            if project is None and self.instance:
                project = self.instance.project
            if project is not None:
                if isinstance(project, int):
                    project = Project.objects.get(pk=project)
                assert_project_accessible(request.user, project)
        return super().validate(attrs)

    class Meta:
        model = ProjectTransaction
        fields = (
            "id",
            "project",
            "project_name",
            "transaction",
            "transaction_name",
            "currency",
            "currency_code",
            "amount",
            "reference",
            "transaction_date",
            "description",
            "created_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "created_by")


class MilestoneTransactionSerializer(serializers.ModelSerializer):
    milestone_name = serializers.CharField(
        source="milestone.name_ar", read_only=True)
    transaction_name = serializers.CharField(
        source="transaction.name_ar", read_only=True)
    currency_code = serializers.CharField(
        source="currency.code", read_only=True)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from ..scoping import assert_project_accessible

            milestone = attrs.get("milestone")
            if milestone is None and self.instance:
                milestone = self.instance.milestone
            if milestone is not None:
                project = milestone.project
                assert_project_accessible(request.user, project)
        return super().validate(attrs)

    class Meta:
        model = MilestoneTransaction
        fields = (
            "id",
            "milestone",
            "milestone_name",
            "transaction",
            "transaction_name",
            "currency",
            "currency_code",
            "amount",
            "reference",
            "transaction_date",
            "description",
            "created_at",
            "created_by",
        )
        read_only_fields = ("id", "created_at", "created_by")


class TargetSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Target
        fields = (
            "id",
            "name_ar",
            "name_en",
            "description",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class PolicySerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = (
            "id",
            "name_ar",
            "name_en",
            "description",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class TargetOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = Target
        fields = ("id", "name")


class PolicyOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = Policy
        fields = ("id", "name")


class MeasureUnitSerializer(AuditReadFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = MeasureUnit
        fields = (
            "id",
            "name_ar",
            "name_en",
            "symbol",
            "deleted",
            "created_at",
            "updated_at",
            "created_by",
            "created_by_name",
            "updated_by",
            "updated_by_name",
        )
        read_only_fields = ("id", "deleted", "created_at",
                            "updated_at", "created_by", "updated_by")


class MeasureUnitOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = MeasureUnit
        fields = ("id", "name", "symbol")
