from django.urls import path
from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="asset_list"),
    path("<int:pk>/", views.AssetDetailView.as_view(), name="asset_detail"),
    path("create/", views.AssetCreateView.as_view(), name="asset_create"),
    path("<int:pk>/update/", views.AssetUpdateView.as_view(), name="asset_update"),
    path("<int:pk>/delete/", views.AssetDeleteView.as_view(), name="asset_delete"),
]