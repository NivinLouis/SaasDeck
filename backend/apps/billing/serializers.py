from rest_framework import serializers

from apps.catalog.models import Product, Tax
from apps.customers.models import Customer
from apps.subscriptions.models import Subscription

from .models import BillingRun, Invoice, InvoiceLine
from .services import create_invoice


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = (
            "id", "description", "quantity", "unit_price", "discount_amount",
            "tax_rate_percent", "tax_amount", "line_total",
        )


class InvoiceSerializer(serializers.ModelSerializer):
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "uuid", "invoice_number", "status", "payment_status", "issue_date", "due_date",
            "billing_period_start", "billing_period_end", "currency", "payment_terms", "notes",
            "customer_snapshot", "subtotal_amount", "discount_amount", "tax_amount", "total_amount",
            "amount_paid", "amount_due", "is_overdue", "pdf_document", "email_sent_at", "lines", "created_at", "updated_at",
        )
        read_only_fields = fields


class InvoiceLineInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False, allow_null=True)
    description = serializers.CharField(max_length=255)
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, default=0)
    tax_rule = serializers.PrimaryKeyRelatedField(queryset=Tax.objects.all(), required=False, allow_null=True)
    tax_rate_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100, default=0)
    hsn_sac = serializers.CharField(max_length=16, required=False, allow_blank=True)
    unit = serializers.CharField(max_length=16, required=False, default="NOS")


class InvoiceCreateSerializer(serializers.Serializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False)
    subscription = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.all(), required=False)
    issue_date = serializers.DateField(required=False)
    due_date = serializers.DateField(required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    lines = InvoiceLineInputSerializer(many=True, required=False)

    def validate(self, attrs):
        if attrs.get("subscription") and attrs.get("customer"):
            raise serializers.ValidationError("Provide either subscription or customer, not both.")
        if not attrs.get("subscription") and not attrs.get("customer"):
            raise serializers.ValidationError("Provide a subscription or a customer.")
        if not attrs.get("subscription") and not attrs.get("lines"):
            raise serializers.ValidationError({"lines": "At least one line is required for a manual invoice."})
        if attrs.get("issue_date") and attrs.get("due_date") and attrs["due_date"] < attrs["issue_date"]:
            raise serializers.ValidationError({"due_date": "Must be on or after issue_date."})
        return attrs

    def create(self, validated_data):
        return create_invoice(**validated_data)


class BillingRunRequestSerializer(serializers.Serializer):
    run_date = serializers.DateField(required=False)

    def validate_run_date(self, value):
        from django.utils import timezone

        if value > timezone.localdate():
            raise serializers.ValidationError("A billing run cannot be scheduled for a future date.")
        return value


class BillingRunSerializer(serializers.ModelSerializer):
    triggered_by_email = serializers.EmailField(source="triggered_by.email", read_only=True, allow_null=True)

    class Meta:
        model = BillingRun
        fields = (
            "uuid", "run_date", "status", "triggered_by_email", "finished_at",
            "subscriptions_considered", "invoices_created", "invoices_existing", "failures",
            "created_at", "updated_at",
        )
        read_only_fields = fields
