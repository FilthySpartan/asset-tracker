from django.db.models import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.assets.models import Asset, AssetAssignment
from .forms import AssetForm, AssetUpdateForm, AssetAssignmentForm


class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        allowed_sorts = ['asset_id', 'asset_name', 'type', 'status', 'cost', 'last_pat_test']
        sort = self.request.GET.get('sort', 'asset_id')
        direction = self.request.GET.get('dir', 'asc')
        if sort not in allowed_sorts:
            sort = 'asset_id'
        if direction == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'asset_id')
        context['current_dir'] = self.request.GET.get('dir', 'asc')
        return context

class AssetDetailView(LoginRequiredMixin, DetailView):
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignments'] = AssetAssignment.objects.filter(
            asset=self.object
        ).order_by('-date_given')
        return context

class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    template_name = "assets/asset_create.html"
    form_class = AssetForm
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        assign_to = form.cleaned_data.get("assign_to")
        date_given = form.cleaned_data.get("date_given")
        if assign_to and date_given:
            AssetAssignment.objects.create(
                user=assign_to,
                asset=self.object,
                date_given=date_given
            )
        return response

class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    template_name = "assets/asset_update.html"
    context_object_name = "asset"
    form_class = AssetUpdateForm
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

    def get_queryset(self):
        queryset = super().get_queryset()
        allowed_sorts = ['asset__asset_name', 'user__last_name', 'date_given', 'date_retrieved']
        sort = self.request.GET.get('sort', 'date_given')
        direction = self.request.GET.get('dir', 'desc')
        if sort not in allowed_sorts:
            sort = 'date_given'
        if direction == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'date_given')
        context['current_dir'] = self.request.GET.get('dir', 'desc')
        return context

class AssetAssignmentDetailView(LoginRequiredMixin, DetailView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_detail.html"
    context_object_name = "asset_assignment"

class AssetAssignmentCreateView(LoginRequiredMixin, CreateView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_create.html"
    form_class = AssetAssignmentForm
    success_url = reverse_lazy("assets:asset_assignment_list")

class AssetAssignmentUpdateView(LoginRequiredMixin, UpdateView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_update.html"
    context_object_name = "asset_assignment"
    form_class = AssetAssignmentForm
    success_url = reverse_lazy("assets:asset_assignment_list")

    def form_valid(self, form):
        original = AssetAssignment.objects.get(pk=self.object.pk)
        user_changed = form.cleaned_data['user'] != original.user
        asset_changed = form.cleaned_data['asset'] != original.asset

        if user_changed or asset_changed:
            # Close out the old assignment
            original.date_retrieved = form.cleaned_data['date_given']
            original.save()

            # Create a new assignment
            AssetAssignment.objects.create(
                user=form.cleaned_data['user'],
                asset=form.cleaned_data['asset'],
                date_given=form.cleaned_data['date_given'],
                date_retrieved=form.cleaned_data.get('date_retrieved')
            )
            return redirect(self.success_url)
        else:
            return super().form_valid(form)

class AssetAssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AssetAssignment
    template_name = "assets/asset_assignment_delete.html"
    success_url = reverse_lazy("assets:asset_assignment_list")
    context_object_name = "asset_assignment"

    def test_func(self):
        return self.request.user.is_staff