from django.urls import path
from .views import ChangePasswordView, LoginView, LogoutView, MeView, RefreshView, RegisterView, StaffCreateView, UserListView

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="register"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="refresh"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/password/change", ChangePasswordView.as_view(), name="password-change"),
    path("me", MeView.as_view(), name="me"),
    path("users/staff", StaffCreateView.as_view(), name="staff-create"),
    path("users", UserListView.as_view(), name="user-list"),
]
