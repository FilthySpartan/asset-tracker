from django import forms
from django.utils import timezone
from .models import Asset, AssetAssignment

# validate the asset forms
class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ["asset_name", "type", "last_pat_test", "end_of_warranty", "cost", "status"]
        widgets = {
            'last_pat_test': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'end_of_warranty': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'cost': forms.NumberInput(attrs={'placeholder': '£0.00', 'step': '0.01'})
        }

    # validate the cost field
    def clean_cost(self):
        cost = self.cleaned_data.get("cost")
        # check prevents entering any negative cost value
        if cost is not None and cost < 0:
            raise forms.ValidationError("Cost cannot be negative")
        return cost
    #validate the last pat test field
    def clean_last_pat_test(self):
        date = self.cleaned_data.get("last_pat_test")
        # check prevents the user entering a date in the future
        if date and date > timezone.now().date():
            raise forms.ValidationError("PAT test date cannot be in the future.")
        return date

#validate the asset assignments forms
class AssetAssignmentForm(forms.ModelForm):
    class Meta:
        model = AssetAssignment
        fields = ["user", "asset", "date_given"]
        widgets = {'date_given': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d')}

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