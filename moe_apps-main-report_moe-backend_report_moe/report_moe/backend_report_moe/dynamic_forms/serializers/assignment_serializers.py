from rest_framework import serializers

from ..assignment_checks import assert_sub_main_is_leaf
from ..models import UserSubMain, UserTitle, UserTitleCategory


class UserSubMainSerializer(serializers.ModelSerializer):
    sub_main_name = serializers.CharField(
        source="sub_main.name", read_only=True)
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.display_name

    class Meta:
        model = UserSubMain
        fields = ("id", "user", "user_name", "sub_main", "sub_main_name")

    def validate_sub_main(self, value):
        assert_sub_main_is_leaf(value)
        return value


class UserTitleSerializer(serializers.ModelSerializer):
    title_name = serializers.CharField(source="title.name", read_only=True)
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.display_name

    class Meta:
        model = UserTitle
        fields = ("id", "user", "user_name", "title", "title_name")


class UserTitleCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    user_name = serializers.SerializerMethodField()

    def get_user_name(self, obj):
        return obj.user.display_name

    class Meta:
        model = UserTitleCategory
        fields = ("id", "user", "user_name", "category", "category_name")
