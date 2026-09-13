from django.urls import path

from .views import (
    MasterDataDetailView,
    MasterDataEntitySlugView,
    MasterDataListCreateView,
    MasterDataOptionsView,
    MasterDataRegistryView,
)

urlpatterns = [
    path('registry/', MasterDataRegistryView.as_view(), name='master-data-registry'),
    path(
        'by-entity/<str:entity_type>/',
        MasterDataEntitySlugView.as_view(),
        name='master-data-by-entity',
    ),
    path('<slug:slug>/options/', MasterDataOptionsView.as_view(), name='master-data-options'),
    path('<slug:slug>/', MasterDataListCreateView.as_view(), name='master-data-list'),
    path('<slug:slug>/<str:pk>/', MasterDataDetailView.as_view(), name='master-data-detail'),
]
