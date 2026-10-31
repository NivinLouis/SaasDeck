from rest_framework import serializers

from .models import Invoice, InvoiceLine


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
            "amount_paid", "amount_due", "is_overdue", "pdf_document", "lines", "created_at", "updated_at",
        )
        read_only_fields = fields
