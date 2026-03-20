from django.db.models import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.assets.models import Asset, AssetAssignment

# Create your views here.
class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10

class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    template_name = "assets/asset_create.html"
    fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
    success_url = reverse_lazy("assets:asset_list")

class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    template_name = "assets/asset_update.html"
    context_object_name = "asset"
    fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
    success_url = reverse_lazy("assets:asset_list")

class AssetDeleteView(LoginRequiredMixin, UserPassesTestMixin , DeleteView):
    model = Asset
    template_name = "assets/asset_delete.html"
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, "You cannot delete this asset, as it is currently assigned to a user")
            return redirect("assets:asset_detail", pk=self.object.pk)

    def test_func(self):
        return self.request.user.is_staff

class AssetAssignmentListView(LoginRequiredMixin, ListView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_list.html"
    context_object_name = "asset_assignments"
    paginate_by = 10

class AssetAssignmentDetailView(LoginRequiredMixin, DetailView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_detail.html"
    context_object_name = "asset_assignment"

class AssetAssignmentCreateView(LoginRequiredMixin, CreateView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_create.html"
    fields = ["user", "asset", "date_given"]
    success_url = reverse_lazy("assets:asset_assignment_list")

class AssetAssignmentUpdateView(LoginRequiredMixin, UpdateView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_update.html"
    context_object_name = "asset_assignment"
    fields = ["user", "asset", "date_given"]
    success_url = reverse_lazy("assets:asset_assignment_list")

class AssetAssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_delete.html"
    success_url = reverse_lazy("assets:asset_assignment_list")
    context_object_name = "asset_assignment"

    def test_func(self):
        return self.request.user.is_staff