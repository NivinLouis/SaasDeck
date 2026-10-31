"""Idempotent invoice generation, state operations, and PDF render contract."""

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Invoice

MONEY_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return (value or Decimal("0.00")).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def customer_snapshot(customer) -> dict:
    """Return only invoice-safe contact fields; never expose portal credentials."""
    return {
        "name": customer.name,
        "company": customer.company,
        "email": customer.email,
        "phone": customer.phone,
        "billing_address": customer.billing_address,
        "city": customer.city,
        "state": customer.state,
        "country": customer.country,
        "postal_code": customer.postal_code,
        "tax_id": customer.tax_id,
    }


@transaction.atomic
def recalculate_invoice_totals(invoice_id: int) -> Invoice:
    """Recalculate a draft invoice from immutable line-item snapshots only."""
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only draft invoices can be recalculated.")

    lines = invoice.lines.all()
    subtotal = sum((line.unit_price * line.quantity - line.discount_amount for line in lines), Decimal("0.00"))
    tax = sum((line.tax_amount for line in lines), Decimal("0.00"))
    discount = sum((line.discount_amount for line in lines), Decimal("0.00"))
    total = sum((line.line_total for line in lines), Decimal("0.00"))

    invoice.subtotal_amount = money(subtotal)
    invoice.tax_amount = money(tax)
    invoice.discount_amount = money(discount)
    invoice.total_amount = money(total)
    if not invoice.customer_snapshot:
        invoice.customer_snapshot = customer_snapshot(invoice.customer)
    invoice.save(update_fields=[
        "subtotal_amount", "tax_amount", "discount_amount", "total_amount",
        "customer_snapshot", "updated_at",
    ])
    return invoice


@transaction.atomic
def confirm_invoice(invoice_id: int) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only draft invoices can be confirmed.")
    if not invoice.lines.exists():
        raise ValidationError("An invoice requires at least one line before confirmation.")

    # recalculate_invoice_totals locks the same row within this transaction.
    invoice = recalculate_invoice_totals(invoice.id)
    invoice.status = Invoice.Status.CONFIRMED
    invoice.save(update_fields=["status", "updated_at"])
    return invoice


@transaction.atomic
def cancel_invoice(invoice_id: int) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status not in {Invoice.Status.DRAFT, Invoice.Status.CONFIRMED}:
        raise ValidationError("Only draft or confirmed invoices can be cancelled.")
    if invoice.amount_paid > Decimal("0.00") or invoice.payments.filter(status="COMPLETED").exists():
        raise ValidationError("Invoices with recorded payments cannot be cancelled.")
    invoice.status = Invoice.Status.CANCELLED
    invoice.save(update_fields=["status", "updated_at"])
    return invoice


def build_invoice_pdf_context(invoice: Invoice) -> dict:
    """Stable, snapshot-only contract for the PDF template and renderer.

    The PDF contributor should consume this function rather than querying product,
    tax, or customer records directly. This protects historical documents from
    future catalog/customer edits.
    """
    snapshot = invoice.customer_snapshot or customer_snapshot(invoice.customer)
    lines = invoice.lines.all().order_by("id")
    return {
        "invoice": {
            "number": invoice.invoice_number,
            "status": invoice.status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "billing_period_start": invoice.billing_period_start,
            "billing_period_end": invoice.billing_period_end,
            "currency": invoice.currency,
            "payment_terms": invoice.payment_terms,
            "notes": invoice.notes,
            "subtotal_amount": invoice.subtotal_amount,
            "discount_amount": invoice.discount_amount,
            "tax_amount": invoice.tax_amount,
            "total_amount": invoice.total_amount,
            "amount_paid": invoice.amount_paid,
            "amount_due": invoice.amount_due,
        },
        "customer": snapshot,
        "lines": [
            {
                "description": line.description,
                "quantity": line.quantity,
                "unit_price": line.unit_price,
                "discount_amount": line.discount_amount,
                "tax_rate_percent": line.tax_rate_percent,
                "tax_amount": line.tax_amount,
                "line_total": line.line_total,
            }
            for line in lines
        ],
    }
