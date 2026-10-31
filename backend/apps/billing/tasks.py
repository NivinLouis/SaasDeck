"""Celery tasks for scheduled billing, email, and PDF generation."""
from celery import shared_task

from .services import generate_invoice_pdf


@shared_task(name="billing.generate_invoice_pdf")
def generate_invoice_pdf_task(invoice_id):
    """Generate and persist a document after an invoice reaches a final billable state."""
    generate_invoice_pdf(invoice_id)
