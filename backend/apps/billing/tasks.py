"""Celery tasks for scheduled billing, email, and PDF generation."""
from celery import shared_task

from .services import generate_invoice_pdf, run_recurring_billing, send_invoice_email


@shared_task(name="billing.generate_invoice_pdf")
def generate_invoice_pdf_task(invoice_id):
    """Generate and persist a document after an invoice reaches a final billable state."""
    generate_invoice_pdf(invoice_id)


@shared_task(name="billing.run_daily_billing")
def run_daily_billing_task():
    """Create invoices for all subscriptions due on or before today's business date."""
    return str(run_recurring_billing().uuid)


@shared_task(name="billing.send_invoice_email")
def send_invoice_email_task(invoice_id):
    """Send a final invoice from a worker when asynchronous email is enabled."""
    send_invoice_email(invoice_id)
