import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# custom form for registering new users and admins
class CustomRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    admin_code = forms.CharField(
        max_length=50,
        required=False,
        label="Admin code (optional)",
        help_text="Enter the admin code if you have been given one."
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "password1", "password2", "admin_code"]

    def clean_first_name(self):
        name = self.cleaned_data.get("first_name")
        if not name.strip():
            raise forms.ValidationError("First name is required.")
        if re.search(r'[0-9]', name):
            raise forms.ValidationError("First name cannot contain numbers.")
        if re.search(r'[^a-zA-Z\s\-\']', name):
            raise forms.ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        return name.strip()

    def clean_last_name(self):
        name = self.cleaned_data.get("last_name")
        if not name.strip():
            raise forms.ValidationError("Last name is required.")
        if re.search(r'[0-9]', name):
            raise forms.ValidationError("Last name cannot contain numbers.")
        if re.search(r'[^a-zA-Z\s\-\']', name):
            raise forms.ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        return name.strip()

    def clean_admin_code(self):
        code = self.cleaned_data.get("admin_code")
        if code and code != "vuepoint-admin-2026":
            raise forms.ValidationError("Invalid admin code.")
        return code

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if self.cleaned_data.get("admin_code") == "vuepoint-admin-2026":
            user.is_staff = True
        if commit:
            user.save()
        return user