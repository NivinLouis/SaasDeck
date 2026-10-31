"""API serializers for plans and payment terms."""
from rest_framework import serializers

from apps.catalog.models import Product

from .models import PaymentTerm, Plan


class ProductSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "sku", "description", "product_type", "sales_price")


class PaymentTermSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ("id", "name", "days")


class PaymentTermSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTerm
        fields = ("id", "name", "days", "description", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class PlanSerializer(serializers.ModelSerializer):
    product_detail = ProductSummarySerializer(source="product", read_only=True)
    payment_term_detail = PaymentTermSummarySerializer(source="payment_term", read_only=True)

    class Meta:
        model = Plan
        fields = (
            "id", "product", "product_detail", "name", "code", "description",
            "billing_interval", "interval_count", "price", "currency", "minimum_quantity",
            "payment_term", "payment_term_detail", "trial_period_days", "auto_close_on_expiry",
            "allow_early_closure", "allow_pause", "allow_auto_renewal", "available_from",
            "available_until", "is_active", "created_at", "updated_at",
            "is_public",
        )
        read_only_fields = ("id", "product_detail", "payment_term_detail", "created_at", "updated_at")
        extra_kwargs = {"product": {"required": True, "allow_null": False}}

    def validate_code(self, value):
        return value.strip().lower()

    def validate_currency(self, value):
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise serializers.ValidationError("Use a three-letter ISO 4217 currency code, such as INR or USD.")
        return value

    def validate(self, attrs):
        available_from = attrs.get("available_from", getattr(self.instance, "available_from", None))
        available_until = attrs.get("available_until", getattr(self.instance, "available_until", None))
        if available_from and available_until and available_until < available_from:
            raise serializers.ValidationError({"available_until": "Must be on or after available_from."})
        return attrs
