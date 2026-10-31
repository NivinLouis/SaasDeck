"""Transactional payment recording, refunds, and invoice balance updates."""
from decimal import Decimal
from uuid import uuid4

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.billing.models import Invoice

from .models import Payment


def payment_number():
    """Generate a collision-resistant reference without a race-prone count query."""
    return f"PAY-{timezone.localdate():%Y}-{uuid4().hex[:8].upper()}"


def _validate_payable_invoice(invoice):
    if invoice.status not in {Invoice.Status.CONFIRMED, Invoice.Status.PAID}:
        raise ValidationError({"invoice": "Payments can only be recorded for confirmed invoices."})
    if invoice.payment_status == Invoice.PaymentStatus.PAID:
        raise ValidationError({"invoice": "This invoice is already fully paid."})


def _apply_invoice_balance(invoice, amount_change):
    invoice.amount_paid += amount_change
    if invoice.amount_paid < Decimal("0.00"):
        raise ValidationError({"amount": "Refund amount exceeds the recorded invoice balance."})

    if invoice.amount_paid == invoice.total_amount:
        invoice.payment_status = Invoice.PaymentStatus.PAID
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
    elif invoice.amount_paid > Decimal("0.00"):
        invoice.payment_status = Invoice.PaymentStatus.PARTIAL
        # A refund can reopen a fully paid invoice.
        if invoice.status == Invoice.Status.PAID:
            invoice.status = Invoice.Status.CONFIRMED
        invoice.paid_at = None
    else:
        invoice.payment_status = Invoice.PaymentStatus.UNPAID
        if invoice.status == Invoice.Status.PAID:
            invoice.status = Invoice.Status.CONFIRMED
        invoice.paid_at = None

    invoice.save(update_fields=["amount_paid", "payment_status", "status", "paid_at", "updated_at"])
    return invoice


@transaction.atomic
def record_payment(*, invoice_id, amount, payment_method, transaction_reference, payment_date, notes, recorded_by):
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    _validate_payable_invoice(invoice)
    if amount > invoice.amount_due:
        raise ValidationError({"amount": f"Amount cannot exceed the remaining balance of {invoice.amount_due}."})

    payment = Payment.objects.create(
        payment_number=payment_number(),
        invoice=invoice,
        customer=invoice.customer,
        amount=amount,
        currency=invoice.currency,
        payment_method=payment_method,
        transaction_reference=transaction_reference or None,
        payment_date=payment_date or timezone.now(),
        notes=notes or None,
        status=Payment.Status.COMPLETED,
        recorded_by=recorded_by,
    )
    _apply_invoice_balance(invoice, amount)
    return payment


@transaction.atomic
def refund_payment(*, payment_id):
    payment = Payment.objects.select_for_update().get(pk=payment_id)
    if payment.status != Payment.Status.COMPLETED:
        raise ValidationError({"status": "Only completed payments can be refunded."})

    invoice = Invoice.objects.select_for_update().get(pk=payment.invoice_id)
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=["status", "updated_at"])
    _apply_invoice_balance(invoice, -payment.amount)
    return payment
