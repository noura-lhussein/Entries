from rest_framework import serializers

from ..assignment_checks import (
    assert_attribute_title_assigned,
    assert_sub_main_assigned,
    assert_sub_main_is_leaf,
)
from ..entity_registry import apply_entity_to_info, is_entity_attribute
from ..location_resolution import apply_location_to_info, is_location_attribute
from ..models import Info


class InfoSerializer(serializers.ModelSerializer):
    attribute_label = serializers.SerializerMethodField()
    title_id = serializers.IntegerField(
        source="attribute.title_id", read_only=True, allow_null=True)
    title_name = serializers.CharField(
        source="attribute.title.name", read_only=True, allow_null=True)
    user_name = serializers.CharField(
        source="user.email", read_only=True, allow_null=True)
    sub_main_name = serializers.CharField(
        source="sub_main.name", read_only=True, allow_null=True)
    main_section_name = serializers.CharField(
        source="sub_main.main_section.name", read_only=True, allow_null=True)
    district_name = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    loc_governorate_name = serializers.CharField(
        source="loc_governorate.name_ar", read_only=True, allow_null=True)
    loc_district_name = serializers.CharField(
        source="loc_district.name_ar", read_only=True, allow_null=True)
    loc_subdistrict_name = serializers.CharField(
        source="loc_subdistrict.name_ar", read_only=True, allow_null=True)
    loc_community_name = serializers.CharField(
        source="loc_community.name_ar", read_only=True, allow_null=True)
    value = serializers.CharField(max_length=5000)

    class Meta:
        model = Info
        fields = (
            "id", "row_key", "attribute", "attribute_label", "title_id", "title_name",
            "sub_main", "sub_main_name", "main_section_name", "district_name", "city_name",
            "loc_governorate", "loc_governorate_name",
            "loc_district", "loc_district_name",
            "loc_subdistrict", "loc_subdistrict_name",
            "loc_community", "loc_community_name",
            "entity_type", "entity_id",
            "user", "user_name", "value", "confirmed",
            "confirm_note", "commit_note", "created_at",
        )
        read_only_fields = (
            "id",
            "row_key",
            "created_at",
            "user",
            "confirm_note",
            "commit_note",
            "confirmed",
            "loc_governorate",
            "loc_district",
            "loc_subdistrict",
            "loc_community",
            "entity_type",
            "entity_id",
        )

    def get_district_name(self, obj):
        if obj.sub_main and obj.sub_main.location_district_id:
            return obj.sub_main.location_district.name_ar
        return None

    def get_attribute_label(self, obj):
        from ..form_schema import attribute_display_label

        if not obj.attribute_id:
            return None
        return attribute_display_label(obj.attribute)

    def get_city_name(self, obj):
        if obj.sub_main and obj.sub_main.location_district_id:
            return obj.sub_main.location_district.governorate.name_ar
        return None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["sub_main"].read_only = True

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            return attrs

        if self.instance is not None and "sub_main" in attrs:
            raise serializers.ValidationError(
                {"sub_main": "لا يمكن تغيير القسم الفرعي بعد الإنشاء."}
            )

        sub_main = attrs.get("sub_main")
        if sub_main is None and self.instance is not None:
            sub_main = self.instance.sub_main
        attribute = attrs.get("attribute")
        if attribute is None and self.instance is not None:
            attribute = self.instance.attribute

        user = request.user
        if sub_main is not None:
            assert_sub_main_assigned(user, sub_main)
            assert_sub_main_is_leaf(sub_main)
        if attribute is not None:
            assert_attribute_title_assigned(user, attribute)
        return attrs

    def validate_value(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("القيمة لا يمكن أن تكون فارغة.")
        return value.strip()

    def validate_attribute(self, value):
        if not value:
            raise serializers.ValidationError("الحقل مطلوب.")
        return value

    def validate_sub_main(self, value):
        if not value:
            raise serializers.ValidationError("القسم الفرعي مطلوب.")
        return value

    def create(self, validated_data):
        attribute = validated_data["attribute"]
        sub_main = validated_data.get("sub_main")
        raw_value = validated_data.pop("value")
        info = Info(**validated_data)
        info.is_report_date = attribute.is_report_date
        context = {}
        if sub_main and sub_main.location_district_id:
            context["governorate_id"] = sub_main.location_district.governorate_id
        if is_location_attribute(attribute.type):
            apply_location_to_info(info, attribute, raw_value, context=context)
        elif is_entity_attribute(attribute.type):
            apply_entity_to_info(info, attribute, raw_value)
        else:
            info.value = raw_value
        info.save()
        return info

    def update(self, instance, validated_data):
        attribute = validated_data.get("attribute", instance.attribute)
        raw_value = validated_data.pop("value", instance.value)
        for key, val in validated_data.items():
            setattr(instance, key, val)
        context = {}
        if instance.sub_main and instance.sub_main.location_district_id:
            context["governorate_id"] = instance.sub_main.location_district.governorate_id
        if is_location_attribute(attribute.type):
            apply_location_to_info(instance, attribute,
                                   raw_value, context=context)
        elif is_entity_attribute(attribute.type):
            apply_entity_to_info(instance, attribute, raw_value)
        else:
            instance.value = raw_value
        instance.save()
        return instance


class InfoRowDataSerializer(InfoSerializer):
    """Alias kept for export/list compatibility."""

    pass
