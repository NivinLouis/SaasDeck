from django.urls import path
from .views import CustomerDetailView, CustomerListCreateView, PortalProfileView

urlpatterns = [
    path("customers", CustomerListCreateView.as_view(), name="customer-list"),
    path("customers/<int:pk>", CustomerDetailView.as_view(), name="customer-detail"),
    path("portal/profile", PortalProfileView.as_view(), name="portal-profile"),
]
