"""Discount administration views."""
from rest_framework import generics

from apps.core.permissions import IsStaffOrAdmin
from .models import DiscountRule
from .serializers import DiscountRuleSerializer


class DiscountRuleListCreateView(generics.ListCreateAPIView):
    serializer_class = DiscountRuleSerializer
    permission_classes = [IsStaffOrAdmin]
    filterset_fields = ("discount_type", "scope", "is_active")
    search_fields = ("code", "name")
    ordering_fields = ("code", "valid_from", "created_at")
    queryset = DiscountRule.objects.prefetch_related("applicable_products", "applicable_plans")


class DiscountRuleDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = DiscountRuleSerializer
    permission_classes = [IsStaffOrAdmin]
    lookup_field = "uuid"
    queryset = DiscountRule.objects.prefetch_related("applicable_products", "applicable_plans")
