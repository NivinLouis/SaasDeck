from django.urls import path

from .views import PaymentTermDetailView, PaymentTermListCreateView, PlanDetailView, PlanListCreateView, PublicPlanShowcaseView


urlpatterns = [
    path("payment-terms", PaymentTermListCreateView.as_view(), name="payment-term-list"),
    path("payment-terms/<int:pk>", PaymentTermDetailView.as_view(), name="payment-term-detail"),
    path("plans", PlanListCreateView.as_view(), name="plan-list"),
    path("plans/<int:pk>", PlanDetailView.as_view(), name="plan-detail"),
    path("showcase/plans", PublicPlanShowcaseView.as_view(), name="public-plan-showcase"),
]
