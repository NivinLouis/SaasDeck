"""Subscription command and response serializers."""
from rest_framework import serializers

from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.discounts.models import DiscountRule

from .models import QuotationTemplate, Subscription
from .services import create_subscription, validate_plan_for_subscription


class CustomerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "company", "email")


class PlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "name", "code", "price", "currency", "billing_interval", "interval_count")


class SubscriptionSerializer(serializers.ModelSerializer):
    customer_detail = CustomerSummarySerializer(source="customer", read_only=True)
    plan_detail = PlanSummarySerializer(source="plan", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "uuid", "subscription_number", "customer", "customer_detail", "plan", "plan_detail",
            "applied_discount",
            "status", "start_date", "expiry_date", "current_period_start", "current_period_end",
            "next_billing_date", "payment_terms", "auto_renew", "cancellation_reason", "closed_at",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "uuid", "subscription_number", "customer_detail", "plan_detail", "status",
            "current_period_start", "current_period_end", "next_billing_date", "payment_terms",
            "cancellation_reason", "closed_at", "created_at", "updated_at",
        )

    def validate_plan(self, plan):
        validate_plan_for_subscription(plan)
        return plan

    def validate(self, attrs):
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        expiry_date = attrs.get("expiry_date", getattr(self.instance, "expiry_date", None))
        if start_date and expiry_date and expiry_date < start_date:
            raise serializers.ValidationError({"expiry_date": "Must be on or after start_date."})
        if self.instance and self.instance.status != Subscription.Status.DRAFT:
            for field in ("customer", "plan", "start_date"):
                if field in attrs and attrs[field] != getattr(self.instance, field):
                    raise serializers.ValidationError({field: "Can only be changed while the subscription is in DRAFT state."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_subscription(created_by=request.user, **validated_data)


class CancelSubscriptionSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class QuotationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationTemplate
        fields = ("uuid", "name", "plan", "validity_days", "terms_and_conditions", "is_active", "created_at", "updated_at")
        read_only_fields = ("uuid", "created_at", "updated_at")
