from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import BrightloopUserCreationForm
from .models import User


@admin.register(User)
class BrightloopUserAdmin(UserAdmin):
    model = User
    add_form = BrightloopUserCreationForm
    list_display = ("email", "full_name", "role", "is_active", "is_staff")
    ordering = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "first_name", "last_name")}),
        ("Brightloop", {"fields": ("role", "created_by")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "full_name", "role", "password1", "password2")} ),)
    search_fields = ("email", "full_name")
