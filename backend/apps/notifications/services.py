"""Reusable email and in-app notification delivery operations."""
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.billing.models import Invoice
from .models import Notification, NotificationPreference


def deliver_overdue_reminder(invoice: Invoice) -> bool:
    """Deliver one overdue-invoice reminder respecting the recipient preferences."""
    if invoice.overdue_reminder_sent_at or not invoice.customer.user_id:
        return False
    recipient = invoice.customer.user
    preference, _ = NotificationPreference.objects.get_or_create(user=recipient)
    subject = f"Payment reminder: {invoice.invoice_number} is overdue"
    body = f"Invoice {invoice.invoice_number} has {invoice.amount_due} {invoice.currency} outstanding and was due on {invoice.due_date:%d %b %Y}."
    if preference.in_app_overdue_reminders:
        Notification.objects.create(recipient=recipient, title=subject, body=body, category="overdue_invoice")
    if preference.email_overdue_reminders:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient.email], fail_silently=False)
    invoice.overdue_reminder_sent_at = timezone.now()
    invoice.save(update_fields=("overdue_reminder_sent_at", "updated_at"))
    return True
