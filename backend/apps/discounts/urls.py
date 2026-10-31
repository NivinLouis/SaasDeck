from django.urls import path
from .views import DiscountRuleDetailView, DiscountRuleListCreateView

urlpatterns = [
    path("discounts", DiscountRuleListCreateView.as_view(), name="discount-list"),
    path("discounts/<uuid:uuid>", DiscountRuleDetailView.as_view(), name="discount-detail"),
]
