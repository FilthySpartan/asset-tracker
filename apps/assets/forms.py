import re
from django import forms
from django.utils import timezone
from .models import Asset, AssetAssignment, User


class BaseAssetForm(forms.ModelForm):
    """
    Base form for Asset creation and updates.
    Contains shared validation logic inherited by AssetForm and AssetUpdateForm,
    following the DRY principle to avoid duplicating validation across forms.
    """
    class Meta:
        model = Asset
        fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
        widgets = {
            'last_pat_test': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_of_warranty': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            # Step attribute ensures browser allows two decimal places for currency input
            'cost': forms.NumberInput(attrs={'placeholder': '£0.00', 'step': '0.01'}),
        }

    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        if cost is not None and cost < 0:
            raise forms.ValidationError("Cost cannot be negative")
        return cost

    def clean_last_pat_test(self):
        """PAT tests are historical records — a future date would be invalid."""
        date = self.cleaned_data.get("last_pat_test")
        if date and date > timezone.now().date():
            raise forms.ValidationError("PAT test date cannot be in the future.")
        return date

    def clean_asset_name(self):
        """Prevent whitespace-only names which would pass CharField's blank check."""
        name = self.cleaned_data.get("asset_name")
        if name and not name.strip():
            raise forms.ValidationError("Asset name cannot be blank.")
        return name


class AssetForm(BaseAssetForm):
    """
    Form for creating new assets. Extends BaseAssetForm with optional
    assignment fields, allowing an asset to be assigned to a user in a single step.
    """
    assign_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Assign to user (optional)"
    )
    date_given = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        label="Date given (optional)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Display full names instead of usernames in the dropdown
        self.fields['assign_to'].label_from_instance = lambda obj: obj.get_full_name() or obj.username

    def clean(self):
        """Ensure both assignment fields are provided together or neither is provided."""
        cleaned_data = super().clean()
        assign_to = cleaned_data.get("assign_to")
        date_given = cleaned_data.get("date_given")

        if assign_to and not date_given:
            raise forms.ValidationError("You must provide a date given when assigning to a user.")
        if date_given and not assign_to:
            raise forms.ValidationError("You must select a user when providing a date given.")
        if date_given and date_given > timezone.now().date():
            raise forms.ValidationError("Date given cannot be in the future.")

        return cleaned_data


class AssetUpdateForm(BaseAssetForm):
    """
    Form for editing existing assets. Inherits all validation from BaseAssetForm
    but excludes the assignment fields since reassignment is handled separately.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill with capitalised name for display, model.save() normalises back to lowercase
        if self.instance and self.instance.pk:
            self.initial['asset_name'] = self.instance.display_name()


class AssetAssignmentForm(forms.ModelForm):
    """Form for creating and editing asset assignments with cross-field validation."""
    class Meta:
        model = AssetAssignment
        fields = ["user", "asset", "date_given", "date_retrieved"]
        widgets = {
            'date_given': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'date_retrieved': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].label_from_instance = lambda obj: obj.get_full_name() or obj.username

    def clean_date_given(self):
        """Assignment dates are historical records — a future date would be invalid."""
        date = self.cleaned_data.get("date_given")
        if date and date > timezone.now().date():
            raise forms.ValidationError("Date given cannot be in the future.")
        return date

    def clean(self):
        """
        Cross-field validation:
        - date_retrieved must be after date_given (logical chronology)
        - date_retrieved cannot be in the future
        - an asset cannot be assigned if it already has an active assignment
        """
        cleaned_data = super().clean()
        asset = cleaned_data.get("asset")
        date_given = cleaned_data.get("date_given")
        date_retrieved = cleaned_data.get("date_retrieved")

        if date_given and date_retrieved and date_retrieved < date_given:
            raise forms.ValidationError("Date retrieved cannot be before date given.")

        if date_retrieved and date_retrieved > timezone.now().date():
            raise forms.ValidationError("Date retrieved cannot be in the future.")

        # Check for active assignments, excluding the current record during edits
        if asset:
            active_assignment = AssetAssignment.objects.filter(
                asset=asset,
                date_retrieved__isnull=True
            )
            if self.instance.pk:
                active_assignment = active_assignment.exclude(pk=self.instance.pk)
            if active_assignment.exists():
                raise forms.ValidationError("This asset is already assigned to someone.")

        return cleaned_data