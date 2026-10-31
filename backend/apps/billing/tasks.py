"""Celery tasks for scheduled billing, email, and PDF generation."""
from celery import shared_task
from django.db import OperationalError

from .services import generate_due_invoices, generate_invoice_pdf


@shared_task(name="billing.generate_invoice_pdf")
def generate_invoice_pdf_task(invoice_id):
    """Generate and persist a document after an invoice reaches a final billable state."""
    generate_invoice_pdf(invoice_id)


@shared_task(
    name="billing.generate_due_invoices",
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_due_invoices_task():
    """Run the recurring billing sweep scheduled by Celery Beat."""
    return generate_due_invoices()
