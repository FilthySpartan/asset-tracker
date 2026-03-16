from django.urls import path
from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="asset_list"),
    path("<int:pk>/", views.AssetDetailView.as_view(), name="asset_detail"),
    path("create/", views.AssetCreateView.as_view(), name="asset_create"),
    path("<int:pk>/update/", views.AssetUpdateView.as_view(), name="asset_update"),
    path("<int:pk>/delete/", views.AssetDeleteView.as_view(), name="asset_delete"),
    path("assignments/", views.AssetAssignmentListView.as_view(), name="asset_assignment_list"),
    path("assignments/create/", views.AssetAssignmentCreateView.as_view(), name="asset_assignment_create"),
    path("assignments/<int:pk>/", views.AssetAssignmentDetailView.as_view(), name="asset_assignment_detail"),
    path("assignments/<int:pk>/update/", views.AssetAssignmentUpdateView.as_view(), name="asset_assignment_update"),
    path("assignments/<int:pk>/delete/", views.AssetAssignmentDeleteView.as_view(), name="asset_assignment_delete"),
]