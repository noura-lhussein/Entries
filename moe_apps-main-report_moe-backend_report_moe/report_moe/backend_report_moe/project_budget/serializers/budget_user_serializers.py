from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from ..models import BudgetUserScope, Foundation, ProjectUserAssignment

User = get_user_model()

BUDGET_USER_FIELDS = (
    "can_view_budget",
    "can_write_budget",
    "can_manage_budget_users",
    "can_manage_budget",
    "can_manage_reference_data",
)


class BudgetUserSerializer(serializers.ModelSerializer):
    # Frontend compatibility: expose email under the legacy "username" key.
    username = serializers.SerializerMethodField()
    foundation = serializers.IntegerField(
        source="budget_scope.foundation_id", read_only=True, allow_null=True)
    foundation_name = serializers.CharField(
        source="budget_scope.foundation.name_ar", read_only=True, allow_null=True
    )
    assigned_project_ids = serializers.SerializerMethodField()
    assigned_project_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "status",
            "is_active",
            "foundation",
            "foundation_name",
            "assigned_project_ids",
            "assigned_project_count",
            *BUDGET_USER_FIELDS,
        )
        read_only_fields = (
            "id",
            "username",
            "foundation",
            "foundation_name",
            "assigned_project_ids",
            "assigned_project_count",
        )

    def get_username(self, obj):
        return obj.email

    def get_assigned_project_ids(self, obj):
        return list(
            ProjectUserAssignment.objects.filter(user=obj).values_list(
                "project_id", flat=True
            )
        )

    def get_assigned_project_count(self, obj):
        return ProjectUserAssignment.objects.filter(user=obj).count()


class BudgetUserCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=4)
    full_name = serializers.CharField(
        required=False, allow_blank=True, default="")
    status = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    foundation = serializers.PrimaryKeyRelatedField(
        queryset=Foundation.objects.filter(deleted=False),
    )
    can_view_budget = serializers.BooleanField(required=False, default=True)
    can_write_budget = serializers.BooleanField(required=False, default=False)
    can_manage_budget_users = serializers.BooleanField(
        required=False, default=False)
    can_manage_budget = serializers.BooleanField(required=False, default=False)
    can_manage_reference_data = serializers.BooleanField(
        required=False, default=False)

    def validate(self, attrs):
        # Prefer email; accept legacy "username" as email identifier.
        email = (attrs.get("email") or "").strip()
        if not email:
            email = str(self.initial_data.get("username") or "").strip()
        if not email:
            raise serializers.ValidationError(
                {"email": "Email is required."})
        attrs["email"] = email
        return attrs

    def validate_foundation(self, foundation):
        request = self.context.get("request")
        if request is None:
            return foundation
        from ..scoping import get_user_foundation_id, is_system_admin

        if is_system_admin(request.user):
            return foundation
        manager_foundation_id = get_user_foundation_id(request.user)
        if manager_foundation_id is None or foundation.pk != manager_foundation_id:
            raise serializers.ValidationError(
                "لا يمكنك إنشاء مستخدمين خارج مؤسستك.")
        return foundation

    @transaction.atomic
    def create(self, validated_data):
        foundation = validated_data.pop("foundation")
        password = validated_data.pop("password")
        request = self.context["request"]
        requester = request.user

        user = User(
            is_staff=False,
            is_superuser=False,
            parent=requester,
            **validated_data,
        )
        user.set_password(password)
        user.save()
        BudgetUserScope.objects.create(user=user, foundation=foundation)
        return user


class BudgetUserUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    full_name = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(
        required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=4)
    foundation = serializers.PrimaryKeyRelatedField(
        queryset=Foundation.objects.filter(deleted=False),
        required=False,
    )
    can_view_budget = serializers.BooleanField(required=False)
    can_write_budget = serializers.BooleanField(required=False)
    can_manage_budget_users = serializers.BooleanField(required=False)
    can_manage_budget = serializers.BooleanField(required=False)
    can_manage_reference_data = serializers.BooleanField(required=False)

    def validate_foundation(self, foundation):
        request = self.context.get("request")
        if request is None:
            return foundation
        from ..scoping import get_user_foundation_id, is_system_admin

        if is_system_admin(request.user):
            return foundation
        manager_foundation_id = get_user_foundation_id(request.user)
        if manager_foundation_id is None or foundation.pk != manager_foundation_id:
            raise serializers.ValidationError(
                "لا يمكنك نقل المستخدم خارج مؤسستك.")
        return foundation

    @transaction.atomic
    def update(self, instance, validated_data):
        foundation = validated_data.pop("foundation", None)
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        if foundation is not None:
            scope, _ = BudgetUserScope.objects.get_or_create(user=instance)
            scope.foundation = foundation
            scope.save(update_fields=["foundation"])

        return instance
