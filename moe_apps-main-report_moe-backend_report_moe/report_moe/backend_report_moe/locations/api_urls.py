from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"governorates", views.GovernorateViewSet,
                basename="location-governorate")
router.register(r"districts", views.DistrictViewSet,
                basename="location-district")
router.register(r"subdistricts", views.SubDistrictViewSet,
                basename="location-subdistrict")
router.register(r"communities", views.CommunityViewSet,
                basename="location-community")

urlpatterns = [
    path("", include(router.urls)),
]
