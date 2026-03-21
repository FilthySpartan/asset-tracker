from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomRegistrationForm


class RegisterView(CreateView):
    form_class = CustomRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")