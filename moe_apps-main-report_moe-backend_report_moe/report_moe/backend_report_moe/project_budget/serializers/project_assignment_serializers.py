from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..models import Project, ProjectUserAssignment

User = get_user_model()


class ProjectAssignmentUserSerializer(serializers.ModelSerializer):
    # Frontend compatibility: expose email under the legacy "username" key.
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "email")
        read_only_fields = fields

    def get_username(self, obj):
        return obj.email


class ProjectAssignmentCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.select_related("budget_scope").get(
                pk=value, deleted=False
            )
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("المستخدم غير موجود.") from exc
        if not getattr(user, "budget_scope", None):
            raise serializers.ValidationError(
                "المستخدم ليس مستخدم ميزانية."
            )
        return user


class UserProjectAssignmentsSerializer(serializers.Serializer):
    project_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
    )

    def validate_project_ids(self, value):
        project_ids = list(dict.fromkeys(value))
        project = self.context.get("project")
        target_user = self.context.get("target_user")
        if project is not None:
            if target_user is None:
                raise serializers.ValidationError("المستخدم مطلوب.")
            scope = getattr(target_user, "budget_scope", None)
            if scope is None:
                raise serializers.ValidationError(
                    "المستخدم ليس مستخدم ميزانية."
                )
            if project.foundation_id != scope.foundation_id:
                raise serializers.ValidationError(
                    "المستخدم والمشروع يجب أن يكونا في نفس المؤسسة."
                )
            return project_ids

        if target_user is None:
            raise serializers.ValidationError("المستخدم مطلوب.")
        foundation_id = getattr(
            getattr(target_user, "budget_scope", None), "foundation_id", None
        )
        if foundation_id is None:
            raise serializers.ValidationError(
                "المستخدم ليس مستخدم ميزانية."
            )
        found = set(
            Project.objects.filter(
                pk__in=project_ids,
                deleted=False,
                foundation_id=foundation_id,
            ).values_list("pk", flat=True)
        )
        missing = set(project_ids) - found
        if missing:
            raise serializers.ValidationError(
                f"مشاريع غير صالحة أو خارج المؤسسة: {sorted(missing)}"
            )
        return project_ids

    def save(self):
        target_user = self.context["target_user"]
        project_ids = self.validated_data["project_ids"]
        assigned_by = self.context["request"].user

        ProjectUserAssignment.objects.filter(user=target_user).exclude(
            project_id__in=project_ids
        ).delete()

        existing = set(
            ProjectUserAssignment.objects.filter(user=target_user).values_list(
                "project_id", flat=True
            )
        )
        for project_id in project_ids:
            if project_id in existing:
                continue
            assignment = ProjectUserAssignment(
                user=target_user,
                project_id=project_id,
                assigned_by=assigned_by,
            )
            assignment.full_clean()
            assignment.save()
        return project_ids
