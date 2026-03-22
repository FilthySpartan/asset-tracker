from django.db import models
from django.db.models import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.assets.models import Asset, AssetAssignment
from .forms import AssetForm, AssetUpdateForm, AssetAssignmentForm
import logging

logger = logging.getLogger(__name__)


# ---- Asset Views ----

class AssetListView(LoginRequiredMixin, ListView):
    """Displays a paginated, searchable, sortable list of all assets."""
    model = Asset
    template_name = "assets/asset_list.html"
    context_object_name = "assets"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by search term across asset name and auto-generated ID
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                models.Q(asset_name__icontains=search) |
                models.Q(asset_id__icontains=search)
            )

        # Validate sort parameter against whitelist to prevent arbitrary field access
        allowed_sorts = ['asset_id', 'asset_name', 'type', 'status', 'cost', 'last_pat_test']
        sort = self.request.GET.get('sort', 'asset_id')
        direction = self.request.GET.get('dir', 'asc')
        if sort not in allowed_sorts:
            sort = 'asset_id'
        if direction == 'desc':
            sort = f'-{sort}'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        # Pass sort and search state to template so pagination and column headers preserve them
        context = super().get_context_data(**kwargs)
        context['current_sort'] = self.request.GET.get('sort', 'asset_id')
        context['current_dir'] = self.request.GET.get('dir', 'asc')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Displays a single asset's details along with its full assignment history."""
    model = Asset
    template_name = "assets/asset_detail.html"
    context_object_name = "asset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Include all assignments for this asset, most recent first, to show chain of custody
        context['assignments'] = AssetAssignment.objects.filter(
            asset=self.object
        ).order_by('-date_given')
        return context


class AssetCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Creates a new asset and optionally assigns it to a user in a single step.
    The optional assignment is handled in form_valid after the asset is saved.
    """
    model = Asset
    template_name = "assets/asset_create.html"
    form_class = AssetForm
    success_url = reverse_lazy("assets:asset_list")
    success_message = "Asset created successfully."

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"Asset '{self.object.display_name()}' ({self.object.asset_id}) created by {self.request.user}")

        # If the user chose to assign the asset during creation, create the assignment record
        assign_to = form.cleaned_data.get("assign_to")
        date_given = form.cleaned_data.get("date_given")
        if assign_to and date_given:
            AssetAssignment.objects.create(
                user=assign_to,
                asset=self.object,
                date_given=date_given
            )
            logger.info(f"Asset '{self.object.asset_id}' assigned to {assign_to.get_full_name()} by {self.request.user}")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Add Asset'
        context['cancel_url'] = reverse_lazy('assets:asset_list')
        return context


class AssetUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Updates an existing asset. Uses AssetUpdateForm which excludes assignment fields."""
    model = Asset
    template_name = "assets/asset_update.html"
    context_object_name = "asset"
    form_class = AssetUpdateForm
    success_url = reverse_lazy("assets:asset_list")
    success_message = "Asset updated successfully."

    def form_valid(self, form):
        logger.info(f"Asset '{self.object.asset_id}' updated by {self.request.user}")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Asset'
        context['cancel_url'] = reverse_lazy('assets:asset_list')
        return context


class AssetDeleteView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin, DeleteView):
    """
    Deletes an asset. Restricted to admin users via UserPassesTestMixin.
    Catches ProtectedError when the asset has active assignments,
    redirecting with a user-friendly error message instead of crashing.
    """
    model = Asset
    template_name = "assets/asset_delete.html"
    success_url = reverse_lazy("assets:asset_list")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            logger.info(f"Asset '{self.object.display_name()}' ({self.object.asset_id}) deleted by {self.request.user}")
            messages.success(self.request, "Asset deleted successfully.")
            return response
        except ProtectedError:
            logger.warning( f"Failed to delete asset '{self.object.asset_id}' - protected by active assignments. Attempted by {self.request.user}")
            messages.error(self.request, "You cannot delete this asset, as it is currently assigned to a user")
            return redirect("assets:asset_detail", pk=self.object.pk)

    def test_func(self):
        """Only staff (admin) users can delete assets."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delete_title'] = 'Delete Asset'
        context['object_name'] = self.object.display_name()
        context['cancel_url'] = reverse_lazy('assets:asset_detail', kwargs={'pk': self.object.pk})
        return context

    def handle_no_permission(self):
        """Log unauthorised delete attempts for audit purposes."""
        logger.warning(f"Unauthorised delete attempt by {self.request.user} on {self.request.path}")
        return super().handle_no_permission()


# ---- Asset Assignment Views ----

class AssetAssignmentListView(LoginRequiredMixin, ListView):
    """
    Displays only current (active) assignments.
    Filters out historical records where date_retrieved is set.
    """
    model = AssetAssignment
    template_name = "assets/asset_assignment_list.html"
    context_object_name = "asset_assignments"
    paginate_by = 10

    def get_queryset(self):
        # Only show active assignments — historical records are visible on the asset detail page
        queryset = AssetAssignment.objects.filter(date_retrieved__isnull=True)

        # Search across related model fields using double-underscore syntax
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                models.Q(asset__asset_name__icontains=search) |
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(asset__asset_id__icontains=search)
            )

        allowed_sorts = ['asset__asset_name', 'user__last_name', 'date_given']
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
        context['search_query'] = self.request.GET.get('q', '')
        return context


class AssetAssignmentDetailView(LoginRequiredMixin, DetailView):
    """Displays full details of a single assignment."""
    model = AssetAssignment
    template_name = "assets/asset_assignment_detail.html"
    context_object_name = "asset_assignment"


class AssetAssignmentCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Creates a new assignment linking a user to an asset."""
    model = AssetAssignment
    template_name = "assets/asset_assignment_create.html"
    form_class = AssetAssignmentForm
    success_url = reverse_lazy("assets:asset_assignment_list")
    success_message = "Assignment created successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Add Assignment'
        context['cancel_url'] = reverse_lazy('assets:asset_assignment_list')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"Assignment created: '{self.object.asset.asset_id}' assigned to {self.object.user.get_full_name()} by {self.request.user}")
        return response


class AssetAssignmentUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Handles both simple edits and reassignments.
    If the user or asset changes, the old assignment is closed (date_retrieved set)
    and a new record is created to preserve the chain of custody.
    """
    model = AssetAssignment
    template_name = "assets/asset_assignment_update.html"
    context_object_name = "asset_assignment"
    form_class = AssetAssignmentForm
    success_url = reverse_lazy("assets:asset_assignment_list")

    def form_valid(self, form):
        # Fetch the original record to compare against the submitted data
        original = AssetAssignment.objects.get(pk=self.object.pk)
        user_changed = form.cleaned_data['user'] != original.user
        asset_changed = form.cleaned_data['asset'] != original.asset

        if user_changed or asset_changed:
            # Close the existing assignment by setting its retrieval date
            original.date_retrieved = form.cleaned_data['date_given']
            original.save()
            logger.info(f"Assignment closed: '{original.asset.asset_id}' retrieved from {original.user.get_full_name()} by {self.request.user}")

            # Create a new assignment record for the new user/asset combination
            AssetAssignment.objects.create(
                user=form.cleaned_data['user'],
                asset=form.cleaned_data['asset'],
                date_given=form.cleaned_data['date_given'],
                date_retrieved=form.cleaned_data.get('date_retrieved')
            )
            messages.success(self.request, "Asset reassigned successfully.")
            logger.info(f"Assignment created: '{form.cleaned_data['asset'].asset_id}' assigned to {form.cleaned_data['user'].get_full_name()} by {self.request.user}")
            return redirect(self.success_url)
        else:
            # No reassignment — just update the existing record's dates
            messages.success(self.request, "Assignment updated successfully.")
            logger.info(f"Assignment updated for '{self.object.asset.asset_id}' by {self.request.user}")
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Edit Assignment'
        context['cancel_url'] = reverse_lazy('assets:asset_assignment_list')
        return context


class AssetAssignmentDeleteView(LoginRequiredMixin, SuccessMessageMixin, UserPassesTestMixin, DeleteView):
    """Deletes an assignment record. Restricted to admin users."""
    model = AssetAssignment
    template_name = "assets/asset_assignment_delete.html"
    success_url = reverse_lazy("assets:asset_assignment_list")
    context_object_name = "asset_assignment"

    def test_func(self):
        """Only staff (admin) users can delete assignments."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['delete_title'] = 'Delete Assignment'
        context['object_name'] = str(self.object)
        context['cancel_url'] = reverse_lazy('assets:asset_assignment_detail', kwargs={'pk': self.object.pk})
        return context

    def form_valid(self, form):
        logger.info(f"Assignment deleted: '{self.object.asset.asset_id}' - {self.object.user.get_full_name()} by {self.request.user}")
        messages.success(self.request, "Assignment deleted successfully.")
        return super().form_valid(form)

    def handle_no_permission(self):
        """Log unauthorised delete attempts for audit purposes."""
        logger.warning(f"Unauthorised delete attempt by {self.request.user} on {self.request.path}")
        return super().handle_no_permission()