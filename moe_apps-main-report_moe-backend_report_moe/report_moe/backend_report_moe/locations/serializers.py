from rest_framework import serializers

from .models import Community, District, Governorate, SubDistrict


class GovernorateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Governorate
        fields = (
            "id",
            "name_ar",
            "name_en",
            "code",
            "uid",
            "is_active",
            "deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "deleted", "created_at", "updated_at")


class GovernorateOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = Governorate
        fields = ("id", "name", "code")


class DistrictSerializer(serializers.ModelSerializer):
    governorate_name = serializers.CharField(
        source="governorate.name_ar", read_only=True)

    class Meta:
        model = District
        fields = (
            "id",
            "governorate",
            "governorate_name",
            "name_ar",
            "name_en",
            "code",
            "uid",
            "is_active",
            "deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "deleted", "created_at", "updated_at")


class DistrictOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = District
        fields = ("id", "name", "code", "governorate")


class SubDistrictSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(
        source="district.name_ar", read_only=True)
    governorate_id = serializers.IntegerField(
        source="district.governorate_id", read_only=True)
    governorate_name = serializers.CharField(
        source="district.governorate.name_ar", read_only=True)

    class Meta:
        model = SubDistrict
        fields = (
            "id",
            "district",
            "district_name",
            "governorate_id",
            "governorate_name",
            "name_ar",
            "name_en",
            "code",
            "uid",
            "is_active",
            "deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "deleted", "created_at", "updated_at")


class SubDistrictOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = SubDistrict
        fields = ("id", "name", "code", "district")


class CommunitySerializer(serializers.ModelSerializer):
    subdistrict_code = serializers.CharField(
        source="subdistrict.code", read_only=True)
    subdistrict_name = serializers.CharField(
        source="subdistrict.name_ar", read_only=True)
    district_id = serializers.IntegerField(
        source="subdistrict.district_id", read_only=True)
    district_name = serializers.CharField(
        source="subdistrict.district.name_ar", read_only=True)
    governorate_id = serializers.IntegerField(
        source="subdistrict.district.governorate_id", read_only=True)
    governorate_name = serializers.CharField(
        source="subdistrict.district.governorate.name_ar", read_only=True)

    class Meta:
        model = Community
        fields = (
            "id",
            "subdistrict",
            "subdistrict_code",
            "subdistrict_name",
            "district_id",
            "district_name",
            "governorate_id",
            "governorate_name",
            "name_ar",
            "name_en",
            "code",
            "uid",
            "latitude",
            "longitude",
            "is_active",
            "deleted",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "deleted", "created_at", "updated_at")


class CommunityOptionSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="name_ar", read_only=True)

    class Meta:
        model = Community
        fields = (
            "id",
            "name",
            "code",
            "subdistrict",
            "latitude",
            "longitude",
        )
