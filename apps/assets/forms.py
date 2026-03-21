from django import forms
from django.utils import timezone
from .models import Asset, AssetAssignment,User

class BaseAssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
        widgets = {
            'last_pat_test': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_of_warranty': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'cost': forms.NumberInput(attrs={'placeholder': '£0.00', 'step': '0.01'}),
        }

    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        if cost is not None and cost < 0:
            raise forms.ValidationError("Cost cannot be negative")
        return cost

    def clean_last_pat_test(self):
        date = self.cleaned_data.get("last_pat_test")
        if date and date > timezone.now().date():
            raise forms.ValidationError("PAT test date cannot be in the future.")
        return date

    def clean_asset_name(self):
        name = self.cleaned_data.get("asset_name")
        if name and not name.strip():
            raise forms.ValidationError("Asset name cannot be blank.")
        return name

# validate the asset forms
class AssetForm(BaseAssetForm):
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
        self.fields['assign_to'].label_from_instance = lambda obj: obj.get_full_name() or obj.username

    def clean(self):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['asset_name'] = self.instance.display_name()


#validate the asset assignments forms
class AssetAssignmentForm(forms.ModelForm):
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

    # check prevents the user entering a date in the future
    def clean_date_given(self):
        date = self.cleaned_data.get("date_given")
        if date and date > timezone.now().date():
            raise forms.ValidationError("Date given cannot be in the future.")
        return date

    #clean validates all fields of the form
    def clean(self):
        cleaned_data = super().clean()
        asset = cleaned_data.get("asset")
        date_given = cleaned_data.get("date_given")
        date_retrieved = cleaned_data.get("date_retrieved")

        if date_given and date_retrieved and date_retrieved < date_given:
            raise forms.ValidationError("Date retrieved cannot be before date given.")

        if date_retrieved and date_retrieved > timezone.now().date():
            raise forms.ValidationError("Date retrieved cannot be in the future.")

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

