from django import forms
from django.utils import timezone
from .models import Asset, AssetAssignment,User

# validate the asset forms
class AssetForm(forms.ModelForm):
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
    class Meta:
        model = Asset
        fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
        widgets = {
            'last_pat_test': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_of_warranty': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'cost': forms.NumberInput(attrs={'placeholder': '£0.00', 'step': '0.01'})
        }

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

        return cleaned_data

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

class AssetUpdateForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
        widgets = {
            'last_pat_test': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_of_warranty': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'cost': forms.NumberInput(attrs={'placeholder': '£0.00', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['asset_name'] = self.instance.display_name()

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
        # we check the database to see if the selected asset is already assigned
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