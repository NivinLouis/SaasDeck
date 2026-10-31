"""Celery tasks for invoice, reminder, and expiry notifications."""
from celery import shared_task
from django.utils import timezone

from apps.billing.models import Invoice
from .services import deliver_overdue_reminder


@shared_task(name="notifications.send_overdue_reminders")
def send_overdue_reminders():
    invoices = Invoice.objects.select_related("customer__user").filter(
        due_date__lt=timezone.localdate(), overdue_reminder_sent_at__isnull=True,
    ).exclude(status=Invoice.Status.CANCELLED).exclude(payment_status=Invoice.PaymentStatus.PAID)
    return {"sent": sum(1 for invoice in invoices if deliver_overdue_reminder(invoice))}
