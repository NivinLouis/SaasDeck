from django.urls import path

from .views import PlanDetailView, PlanListCreateView


urlpatterns = [
    path("plans", PlanListCreateView.as_view(), name="plan-list"),
    path("plans/<int:pk>", PlanDetailView.as_view(), name="plan-detail"),
]
