from django.contrib.auth import get_user_model
from rest_framework import serializers

from ..assignment_checks import allowed_title_ids, assert_sub_main_is_leaf
from ..models import SubMainSection, Title, UserSubMain, UserTitle, UserTitleCategory

User = get_user_model()


def _portal_sectors_field():
    """`portal_sectors` write field — a subset of User.PORTAL_SECTORS.

    The report_moe user form is the single admin surface for both systems: this
    picks the moeds portal sectors, and the existing can_view_info / can_write_info
    checkboxes set the level. `User.apply_portal_sectors()` (called from
    create/update) turns that into the per-sector booleans the portal reads.
    """
    return serializers.ListField(
        child=serializers.ChoiceField(choices=list(User.PORTAL_SECTORS)),
        required=False,
        write_only=True,
        allow_empty=True,
    )


def _assert_leaf_sub_main_ids(sub_main_ids: list[int]) -> None:
    if not sub_main_ids:
        return
    subs = {
        s.id: s
        for s in SubMainSection.objects.filter(id__in=sub_main_ids).prefetch_related(
            "children"
        )
    }
    for sid in sub_main_ids:
        sub = subs.get(sid)
        if sub is None:
            raise serializers.ValidationError(
                {"sub_main_ids": f"قسم فرعي غير موجود: {sid}"}
            )
        try:
            assert_sub_main_is_leaf(sub)
        except Exception as exc:
            detail = getattr(exc, "detail", None)
            if detail is not None:
                raise serializers.ValidationError(detail) from exc
            raise serializers.ValidationError(
                {"sub_main_ids": "الإدخال والصلاحيات مسموحة فقط على الأوراق."}
            ) from exc


def _sync_user_title_categories(user, category_ids: list[int]) -> None:
    user.user_title_categories.all().delete()
    for category_id in category_ids:
        UserTitleCategory.objects.get_or_create(
            user=user, category_id=category_id)


def _sync_user_titles(user, title_ids: list[int]) -> None:
    user.user_titles.all().delete()
    for title_id in title_ids:
        UserTitle.objects.get_or_create(user=user, title_id=title_id)


def _assert_titles_in_categories(title_ids: list[int], category_ids: list[int]) -> None:
    if category_ids and not title_ids:
        raise serializers.ValidationError(
            {"title_ids": "اختر مسمى واحداً على الأقل ضمن الفئات المحددة."}
        )
    if not title_ids:
        return
    if not category_ids:
        raise serializers.ValidationError(
            {"title_ids": "اختر فئة مسميات قبل إسناد المسميات."}
        )
    valid = set(
        Title.objects.filter(
            deleted=False,
            id__in=title_ids,
            category_id__in=category_ids,
        ).values_list("id", flat=True)
    )
    bad = [tid for tid in title_ids if tid not in valid]
    if bad:
        raise serializers.ValidationError(
            {"title_ids": f"مسميات خارج الفئات المحددة: {bad}"}
        )


def _title_ids_for_categories(category_ids: list[int]) -> list[int]:
    if not category_ids:
        return []
    return list(
        Title.objects.filter(deleted=False, category_id__in=category_ids)
        .order_by("order", "id")
        .values_list("id", flat=True)
    )


class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()
    # Frontend compatibility: expose email under the legacy "username" key.
    username = serializers.SerializerMethodField()
    sub_main_ids = serializers.SerializerMethodField()
    title_ids = serializers.SerializerMethodField()
    title_category_ids = serializers.SerializerMethodField()
    sub_mains = serializers.SerializerMethodField()
    titles = serializers.SerializerMethodField()
    title_categories = serializers.SerializerMethodField()
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', read_only=True)
    parent_name = serializers.SerializerMethodField()
    foundation_id = serializers.SerializerMethodField()
    foundation_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "full_name",
            "status", "is_active", "is_staff", "is_superuser",
            "is_admin", "date_joined", "sub_main_ids", "title_ids",
            "title_category_ids",
            "sub_mains", "titles", "title_categories",
            "parent_id", "parent_name",
            "can_write_info", "can_view_info", "can_confirm_info",
            "can_export_reports", "can_add_user",
            "can_view_budget", "can_write_budget", "can_manage_budget_users",
            "can_manage_budget", "can_manage_reference_data",
            # `portal_sectors` is the input the admin edits; the per-sector
            # booleans are the derived cache the portal reads from /auth/me/.
            "portal_sectors",
            "can_view_oil_gas", "can_write_oil_gas",
            "can_view_electricity", "can_write_electricity",
            "can_view_water", "can_write_water",
            "can_view_mineral", "can_write_mineral",
            "can_manage_projects", "can_manage_datasets", "can_manage_control_panel",
            "display_name",
            "foundation_id", "foundation_name",
        )
        read_only_fields = (
            "id", "username", "date_joined", "is_admin", "display_name",
            "sub_main_ids", "title_ids", "title_category_ids",
            "sub_mains", "titles", "title_categories", "parent_name",
            "portal_sectors",
            "can_view_oil_gas", "can_write_oil_gas",
            "can_view_electricity", "can_write_electricity",
            "can_view_water", "can_write_water",
            "can_view_mineral", "can_write_mineral",
            "can_manage_projects",
        )

    def get_username(self, obj):
        return obj.email

    def get_is_admin(self, obj):
        # Full portal admin — see User.is_portal_admin. This is what the moeds
        # portal reads to unlock every sector + admin menu.
        return obj.is_portal_admin

    def get_sub_main_ids(self, obj):
        return list(obj.user_sub_mains.values_list('sub_main_id', flat=True))

    def get_title_category_ids(self, obj):
        return list(obj.user_title_categories.values_list('category_id', flat=True))

    def get_title_ids(self, obj):
        explicit = list(obj.user_titles.values_list("title_id", flat=True))
        if explicit:
            return sorted(explicit)
        allowed = allowed_title_ids(obj)
        if allowed is None:
            return list(
                Title.objects.filter(
                    deleted=False).values_list("id", flat=True)
            )
        return sorted(allowed)

    def get_sub_mains(self, obj):
        return list(
            obj.user_sub_mains
            .select_related('sub_main__main_section')
            .values(
                'sub_main__id',
                'sub_main__name',
                'sub_main__main_section__name',
            )
        )

    def get_title_categories(self, obj):
        return list(
            obj.user_title_categories
            .select_related('category')
            .values('category__id', 'category__name', 'category__order')
        )

    def get_titles(self, obj):
        allowed = allowed_title_ids(obj)
        qs = (
            Title.objects.filter(deleted=False)
            .select_related('category')
            .order_by('order', 'id')
        )
        if allowed is not None:
            qs = qs.filter(id__in=allowed)
        return [
            {
                'title__id': t.id,
                'title__name': t.name,
                'title__category_id': t.category_id,
                'title__category_name': t.category.name if t.category_id else None,
            }
            for t in qs
        ]

    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.display_name
        return None

    def get_foundation_id(self, obj):
        scope = getattr(obj, "budget_scope", None)
        return scope.foundation_id if scope else None

    def get_foundation_name(self, obj):
        scope = getattr(obj, "budget_scope", None)
        if scope and scope.foundation_id:
            return scope.foundation.name_ar
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)
    # Uniqueness is enforced in the view; skip DRF's unique validator here.
    email = serializers.EmailField()
    full_name = serializers.CharField(
        required=False, allow_blank=True, default="")
    # Frontend compatibility: response key returns email.
    username = serializers.SerializerMethodField()
    sub_main_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    title_category_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    # Explicit title subset within the selected categories (UserTitle rows).
    title_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    portal_sectors = _portal_sectors_field()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "full_name",
            "status", "is_active", "password",
            "sub_main_ids", "title_category_ids", "title_ids",
            "can_write_info", "can_view_info", "can_confirm_info",
            "can_export_reports", "can_add_user",
            "can_view_budget", "can_write_budget", "can_manage_budget_users",
            "can_manage_budget", "can_manage_reference_data",
            # moeds portal: sectors (the input) + the 3 flags not tied to a sector.
            "portal_sectors", "is_admin",
            "can_manage_datasets", "can_manage_control_panel",
        )
        read_only_fields = ("id", "username")

    def get_username(self, obj):
        return obj.email

    def validate(self, attrs):
        # Accept legacy "username" body field as email identifier.
        email = (attrs.get("email") or "").strip()
        if not email:
            email = str(self.initial_data.get("username") or "").strip()
        if not email:
            raise serializers.ValidationError(
                {"email": "Email is required."})
        attrs["email"] = email
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        sub_main_ids = validated_data.pop("sub_main_ids", [])
        category_ids = validated_data.pop("title_category_ids", None)
        title_ids = validated_data.pop("title_ids", None)
        if category_ids is None:
            category_ids = []
        _assert_leaf_sub_main_ids(sub_main_ids)

        validated_data["is_staff"] = False
        validated_data["is_superuser"] = False
        validated_data["parent"] = self.context["request"].user

        user = User(**validated_data)
        user.apply_portal_sectors()
        user.set_password(password)
        user.save()

        for sub_main_id in sub_main_ids:
            UserSubMain.objects.get_or_create(
                user=user, sub_main_id=sub_main_id)

        _sync_user_title_categories(user, category_ids)
        if title_ids is None:
            title_ids = _title_ids_for_categories(category_ids)
        _assert_titles_in_categories(title_ids, category_ids)
        _sync_user_titles(user, title_ids)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, min_length=4)
    full_name = serializers.CharField(required=False, allow_blank=True)
    sub_main_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    title_category_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    title_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True)
    portal_sectors = _portal_sectors_field()
    # Frontend compatibility: expose email under "username".
    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "full_name",
            "status", "is_active", "password",
            "sub_main_ids", "title_category_ids", "title_ids",
            "can_write_info", "can_view_info", "can_confirm_info",
            "can_export_reports", "can_add_user",
            "can_view_budget", "can_write_budget", "can_manage_budget_users",
            "can_manage_budget", "can_manage_reference_data",
            # moeds portal: sectors (the input) + the 3 flags not tied to a sector.
            "portal_sectors", "is_admin",
            "can_manage_datasets", "can_manage_control_panel",
        )
        read_only_fields = ("id", "username", "parent")

    def get_username(self, obj):
        return obj.email

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        sub_main_ids = validated_data.pop("sub_main_ids", None)
        category_ids = validated_data.pop("title_category_ids", None)
        title_ids = validated_data.pop("title_ids", None)
        sectors_given = "portal_sectors" in validated_data

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # Recompute the derived per-sector booleans whenever the sector list OR
        # the view/write level might have changed.
        if sectors_given or "can_view_info" in validated_data or "can_write_info" in validated_data:
            instance.apply_portal_sectors()
        if password:
            instance.set_password(password)
        instance.save()

        if sub_main_ids is not None:
            _assert_leaf_sub_main_ids(sub_main_ids)
            instance.user_sub_mains.all().delete()
            for sub_main_id in sub_main_ids:
                UserSubMain.objects.get_or_create(
                    user=instance, sub_main_id=sub_main_id)

        if category_ids is not None:
            _sync_user_title_categories(instance, category_ids)

        effective_cats = (
            category_ids
            if category_ids is not None
            else list(instance.user_title_categories.values_list("category_id", flat=True))
        )
        if title_ids is not None:
            _assert_titles_in_categories(title_ids, effective_cats)
            _sync_user_titles(instance, title_ids)
        elif category_ids is not None:
            # Category list changed without explicit titles → grant all in categories.
            _sync_user_titles(
                instance, _title_ids_for_categories(category_ids))

        return instance
