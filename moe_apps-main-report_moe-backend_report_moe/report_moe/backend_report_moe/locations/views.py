from django.utils import timezone
from dynamic_forms.permissions import IsAdminOrReadOnly
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Community, District, Governorate, SubDistrict
from .serializers import (
    CommunityOptionSerializer,
    CommunitySerializer,
    DistrictOptionSerializer,
    DistrictSerializer,
    GovernorateOptionSerializer,
    GovernorateSerializer,
    SubDistrictOptionSerializer,
    SubDistrictSerializer,
)


class LocationOptionsMixin:
    option_serializer_class = None

    @action(detail=False, methods=["get"], url_path="options")
    def options(self, request):
        if self.option_serializer_class is None:
            return Response(
                {"detail": "Options not available."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.option_serializer_class(qs, many=True)
        return Response(serializer.data)


class LocationModelViewSet(LocationOptionsMixin, viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return self.queryset.filter(deleted=False, is_active=True)

    def perform_create(self, serializer):
        kwargs = {"created_by": self.request.user,
                  "updated_by": self.request.user}
        serializer.save(**kwargs)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save()


class GovernorateViewSet(LocationModelViewSet):
    queryset = Governorate.objects.all()
    serializer_class = GovernorateSerializer
    option_serializer_class = GovernorateOptionSerializer
    search_fields = ("name_ar", "name_en", "code")
    ordering_fields = ("name_ar", "code", "id")


class DistrictViewSet(LocationModelViewSet):
    queryset = District.objects.select_related("governorate")
    serializer_class = DistrictSerializer
    option_serializer_class = DistrictOptionSerializer
    search_fields = ("name_ar", "name_en", "code")
    ordering_fields = ("name_ar", "code", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        governorate_id = self.request.query_params.get("governorate")
        if governorate_id:
            qs = qs.filter(governorate_id=governorate_id)
        return qs


class SubDistrictViewSet(LocationModelViewSet):
    queryset = SubDistrict.objects.select_related(
        "district", "district__governorate")
    serializer_class = SubDistrictSerializer
    option_serializer_class = SubDistrictOptionSerializer
    search_fields = ("name_ar", "name_en", "code")
    ordering_fields = ("name_ar", "code", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        district_id = self.request.query_params.get("district")
        if district_id:
            qs = qs.filter(district_id=district_id)
        governorate_id = self.request.query_params.get("governorate")
        if governorate_id:
            qs = qs.filter(district__governorate_id=governorate_id)
        return qs


class CommunityViewSet(LocationModelViewSet):
    queryset = Community.objects.select_related(
        "subdistrict",
        "subdistrict__district",
        "subdistrict__district__governorate",
    )
    serializer_class = CommunitySerializer
    option_serializer_class = CommunityOptionSerializer
    search_fields = ("name_ar", "name_en", "code")
    ordering_fields = ("name_ar", "code", "id")

    def get_queryset(self):
        qs = super().get_queryset()
        subdistrict_id = self.request.query_params.get("subdistrict")
        if subdistrict_id:
            qs = qs.filter(subdistrict_id=subdistrict_id)
        district_id = self.request.query_params.get("district")
        if district_id:
            qs = qs.filter(subdistrict__district_id=district_id)
        governorate_id = self.request.query_params.get("governorate")
        if governorate_id:
            qs = qs.filter(
                subdistrict__district__governorate_id=governorate_id)
        return qs
