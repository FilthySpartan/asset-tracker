from django.shortcuts import render
from django.views.generic import ListView
from apps.assets.models import Asset


# Create your views here.
class AssetListView(ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10