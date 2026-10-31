"""Payment command and response serializers."""
from rest_framework import serializers

from apps.billing.models import Invoice

from .models import Payment
from .services import record_payment


class InvoiceSummarySerializer(serializers.ModelSerializer):
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Invoice
        fields = ("uuid", "invoice_number", "total_amount", "amount_paid", "amount_due", "currency", "payment_status")


class PaymentSerializer(serializers.ModelSerializer):
    invoice_detail = InvoiceSummarySerializer(source="invoice", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "uuid", "payment_number", "invoice", "invoice_detail", "payment_method", "status", "amount",
            "currency", "transaction_reference", "payment_date", "notes", "created_at", "updated_at",
        )
        read_only_fields = (
            "uuid", "payment_number", "invoice_detail", "status", "currency", "created_at", "updated_at",
        )

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return amount

    def create(self, validated_data):
        request = self.context["request"]
        return record_payment(
            invoice_id=validated_data["invoice"].id,
            amount=validated_data["amount"],
            payment_method=validated_data.get("payment_method", Payment.PaymentMethod.BANK_TRANSFER),
            transaction_reference=validated_data.get("transaction_reference", ""),
            payment_date=validated_data.get("payment_date"),
            notes=validated_data.get("notes", ""),
            recorded_by=request.user,
        )
