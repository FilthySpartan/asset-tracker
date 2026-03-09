from django.db.models import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from apps.assets.models import Asset


# Create your views here.
class AssetListView(ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10

class AssetDetailView(DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

class AssetCreateView(CreateView):
    model = Asset
    template_name = "assets/asset_create.html"
    fields = "__all__"
    success_url = reverse_lazy("assets:asset_list")

class AssetUpdateView(UpdateView):
    model = Asset
    template_name = "assets/asset_update.html"
    context_object_name = "asset"
    fields = "__all__"
    success_url = reverse_lazy("assets:asset_list")

class AssetDeleteView(DeleteView):
    model = Asset
    template_name = "assets/asset_delete.html"
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "You cannot delete this asset, as it is currently assigned to a user")
            return redirect("assets:asset_detail", pk=self.object.pk)