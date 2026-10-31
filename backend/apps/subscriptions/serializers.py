"""Subscription command and response serializers."""
from datetime import timedelta

from rest_framework import serializers

from apps.customers.models import Customer
from apps.plans.models import Plan

from .models import QuotationTemplate, QuotationTemplateLine, Subscription, SubscriptionLine
from .services import create_quotation_from_template, create_subscription, validate_plan_for_subscription


class CustomerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ("id", "name", "company", "email")


class PlanSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ("id", "name", "code", "price", "currency", "billing_interval", "interval_count")


class SubscriptionLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variant_value = serializers.CharField(source="variant.value", read_only=True, allow_null=True)

    class Meta:
        model = SubscriptionLine
        fields = ("id", "product", "product_name", "variant", "variant_value", "quantity", "unit_price", "discount_percent")


class QuotationTemplateLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    variant_value = serializers.CharField(source="variant.value", read_only=True, allow_null=True)

    class Meta:
        model = QuotationTemplateLine
        fields = ("id", "product", "product_name", "variant", "variant_value", "quantity", "discount_percent")
        read_only_fields = ("id", "product_name", "variant_value")

    def validate(self, attrs):
        product = attrs.get("product", getattr(self.instance, "product", None))
        variant = attrs.get("variant", getattr(self.instance, "variant", None))
        if variant and variant.product_id != product.id:
            raise serializers.ValidationError({"variant": "The selected variant must belong to this product."})
        return attrs


class QuotationTemplateSerializer(serializers.ModelSerializer):
    plan_detail = PlanSummarySerializer(source="plan", read_only=True)
    lines = QuotationTemplateLineSerializer(many=True, required=False)

    class Meta:
        model = QuotationTemplate
        fields = ("uuid", "name", "plan", "plan_detail", "validity_days", "terms_and_conditions", "is_active", "lines", "created_at", "updated_at")
        read_only_fields = ("uuid", "plan_detail", "created_at", "updated_at")

    def create(self, validated_data):
        lines = validated_data.pop("lines", [])
        template = QuotationTemplate.objects.create(**validated_data)
        QuotationTemplateLine.objects.bulk_create([
            QuotationTemplateLine(template=template, **line) for line in lines
        ])
        return template

    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            QuotationTemplateLine.objects.bulk_create([
                QuotationTemplateLine(template=instance, **line) for line in lines
            ])
        return instance


class QuotationFromTemplateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    start_date = serializers.DateField(required=False)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    auto_renew = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if attrs.get("start_date") and attrs.get("expiry_date") and attrs["expiry_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"expiry_date": "Must be on or after start_date."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_quotation_from_template(template=self.context["template"], created_by=request.user, **validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    customer_detail = CustomerSummarySerializer(source="customer", read_only=True)
    plan_detail = PlanSummarySerializer(source="plan", read_only=True)
    template_detail = serializers.SerializerMethodField()
    quotation_valid_until = serializers.SerializerMethodField()
    lines = SubscriptionLineSerializer(many=True, read_only=True)

    def get_template_detail(self, subscription):
        if not subscription.template_id:
            return None
        return {"uuid": str(subscription.template.uuid), "name": subscription.template.name, "validity_days": subscription.template.validity_days}

    def get_quotation_valid_until(self, subscription):
        if not subscription.template_id or subscription.status not in {Subscription.Status.QUOTATION, Subscription.Status.CONFIRMED}:
            return None
        return subscription.created_at.date() + timedelta(days=subscription.template.validity_days)

    class Meta:
        model = Subscription
        fields = (
            "uuid", "subscription_number", "customer", "customer_detail", "plan", "plan_detail",
            "applied_discount",
            "template", "template_detail", "quotation_valid_until", "lines",
            "status", "start_date", "expiry_date", "current_period_start", "current_period_end",
            "next_billing_date", "payment_terms", "auto_renew", "cancellation_reason", "closed_at",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "uuid", "subscription_number", "customer_detail", "plan_detail", "template", "template_detail", "quotation_valid_until", "lines", "status",
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
