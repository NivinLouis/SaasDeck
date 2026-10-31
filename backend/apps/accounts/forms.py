from django.contrib.auth.forms import BaseUserCreationForm

from .models import User


class BrightloopUserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("email", "full_name", "role")
