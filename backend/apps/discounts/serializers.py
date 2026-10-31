"""Discount rule serializers."""
from rest_framework import serializers

from .models import DiscountRule


class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = ("uuid", "code", "name", "description", "discount_type", "value", "scope", "minimum_purchase_amount", "minimum_quantity", "valid_from", "valid_until", "max_uses", "times_used", "is_active", "applicable_products", "applicable_plans", "created_at", "updated_at")
        read_only_fields = ("uuid", "times_used", "created_at", "updated_at")

    def validate_code(self, value):
        return value.strip().upper()

    def validate(self, attrs):
        scope = attrs.get("scope", getattr(self.instance, "scope", None))
        if scope == DiscountRule.Scope.SPECIFIC_PRODUCTS and "applicable_products" in attrs and not attrs["applicable_products"]:
            raise serializers.ValidationError({"applicable_products": "Select at least one product."})
        if scope == DiscountRule.Scope.SPECIFIC_PLANS and "applicable_plans" in attrs and not attrs["applicable_plans"]:
            raise serializers.ValidationError({"applicable_plans": "Select at least one plan."})
        return attrs
