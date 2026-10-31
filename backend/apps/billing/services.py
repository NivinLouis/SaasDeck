"""Invoice lifecycle operations and GST-safe document rendering."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
import re

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import BillingRun, Invoice, InvoiceLine

MONEY_PLACES = PAISE = Decimal("0.01")
GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$")
INVOICE_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9/-]{1,16}$")


class InvoiceDocumentValidationError(ValueError):
    """Raised when an invoice lacks a mandatory Rule 46 document detail."""


@dataclass(frozen=True)
class SupplierProfile:
    legal_name: str
    address: str
    gstin: str
    state_name: str
    state_code: str
    authorised_signatory: str


def money(value: Decimal) -> Decimal:
    return (value or Decimal("0.00")).quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def invoice_number() -> str:
    """Collision-resistant reference suitable for user-facing invoice documents."""
    from uuid import uuid4
    return f"INV-{timezone.localdate():%Y}-{uuid4().hex[:8].upper()}"


def _invoice_line_values(*, product, description, quantity, unit_price, discount_amount=Decimal("0.00"), tax_rule=None,
                         tax_rate_percent=Decimal("0.00"), hsn_sac="", unit="NOS"):
    taxable = money(Decimal(quantity) * unit_price - discount_amount)
    tax_amount = money(taxable * tax_rate_percent / Decimal("100"))
    return {
        "product": product, "description": description, "quantity": quantity, "unit_price": money(unit_price),
        "discount_amount": money(discount_amount), "tax_rule": tax_rule, "tax_rate_percent": money(tax_rate_percent),
        "tax_amount": tax_amount, "line_total": money(taxable + tax_amount), "hsn_sac": hsn_sac, "unit": unit,
    }


def subscription_discount_amount(subscription, subtotal):
    discount = subscription.applied_discount
    if not discount or not discount.is_currently_valid or subtotal < discount.minimum_purchase_amount:
        return Decimal("0.00")
    if discount.discount_type == "PERCENTAGE":
        return money(subtotal * discount.value / Decimal("100"))
    return min(money(discount.value), subtotal)


@transaction.atomic
def create_invoice(*, customer=None, subscription=None, issue_date=None, due_date=None, notes="", lines=None):
    """Create a draft invoice manually or from the current billing period of an active subscription."""
    from apps.subscriptions.models import Subscription

    issue_date = issue_date or timezone.localdate()
    lines = lines or []
    if subscription:
        subscription = Subscription.objects.select_related(
            "customer", "plan", "plan__product", "plan__payment_term"
        ).select_for_update(of=("self",)).get(pk=subscription.pk)
        if subscription.status != Subscription.Status.ACTIVE:
            raise ValidationError({"subscription": "Only active subscriptions can be invoiced."})
        if not subscription.current_period_start or not subscription.current_period_end:
            raise ValidationError({"subscription": "Subscription billing dates are required before invoicing."})
        if Invoice.objects.filter(
            subscription=subscription,
            billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end,
        ).exclude(status=Invoice.Status.CANCELLED).exists():
            raise ValidationError({"subscription": "An invoice already exists for this billing period."})
        customer = subscription.customer
        payment_term = subscription.plan.payment_term
        due_date = due_date or issue_date + timedelta(days=payment_term.days if payment_term else 0)
        invoice = Invoice.objects.create(
            invoice_number=invoice_number(), customer=customer, subscription=subscription, issue_date=issue_date,
            due_date=due_date, billing_period_start=subscription.current_period_start,
            billing_period_end=subscription.current_period_end, currency=subscription.plan.currency,
            payment_terms=subscription.payment_terms, notes=notes or "", customer_snapshot=customer_snapshot(customer),
        )
        subscription_lines = list(subscription.lines.select_related("product", "tax_rule").all())
        if subscription_lines:
            for line in subscription_lines:
                InvoiceLine.objects.create(invoice=invoice, **_invoice_line_values(
                    product=line.product, description=line.product.name, quantity=line.quantity, unit_price=line.unit_price,
                    discount_amount=money(line.unit_price * line.quantity * line.discount_percent / Decimal("100")),
                    tax_rule=line.tax_rule, tax_rate_percent=line.tax_rule.rate if line.tax_rule else Decimal("0.00"),
                ))
        else:
            product = subscription.plan.product
            if not product:
                raise ValidationError({"subscription": "The selected plan must have a product to create an invoice."})
            tax_link = product.product_taxes.select_related("tax").filter(tax__is_active=True).first()
            InvoiceLine.objects.create(invoice=invoice, **_invoice_line_values(
                product=product, description=subscription.plan.name, quantity=subscription.plan.minimum_quantity,
                unit_price=subscription.plan.price, discount_amount=subscription_discount_amount(subscription, money(subscription.plan.price * subscription.plan.minimum_quantity)), tax_rule=tax_link.tax if tax_link else None,
                tax_rate_percent=tax_link.tax.rate if tax_link else Decimal("0.00"),
                unit="MONTH" if subscription.plan.billing_interval == "monthly" else subscription.plan.billing_interval.upper(),
            ))
    else:
        if not customer:
            raise ValidationError({"customer": "A customer is required for a manual invoice."})
        if not lines:
            raise ValidationError({"lines": "At least one line is required for a manual invoice."})
        if not due_date:
            raise ValidationError({"due_date": "A due date is required for a manual invoice."})
        invoice = Invoice.objects.create(
            invoice_number=invoice_number(), customer=customer, issue_date=issue_date, due_date=due_date,
            notes=notes or "", customer_snapshot=customer_snapshot(customer),
        )
        for line in lines:
            InvoiceLine.objects.create(invoice=invoice, **_invoice_line_values(**line))

    return recalculate_invoice_totals(invoice.id)


def _advance_subscription_period(subscription):
    """Advance a successfully billed subscription to its next recurring period."""
    from apps.subscriptions.services import add_billing_interval

    next_period_start = subscription.current_period_end + timedelta(days=1)
    next_period_end = add_billing_interval(next_period_start, subscription.plan) - timedelta(days=1)
    subscription.current_period_start = next_period_start
    subscription.current_period_end = next_period_end
    subscription.next_billing_date = next_period_end + timedelta(days=1)


def _close_after_current_period(subscription):
    """Return whether the current period is the subscription's final billable period."""
    if not subscription.expiry_date:
        return not subscription.auto_renew
    next_period_start = subscription.current_period_end + timedelta(days=1)
    return next_period_start > subscription.expiry_date and (
        subscription.plan.auto_close_on_expiry or not subscription.auto_renew
    )


@transaction.atomic
def bill_due_subscription(*, subscription_id: int, as_of=None):
    """Create one draft invoice for a due subscription and move its schedule forward.

    The row lock, period unique constraint, and one-period-at-a-time advancement make
    this operation safe to retry or run concurrently from multiple workers.
    """
    from apps.subscriptions.models import Subscription

    as_of = as_of or timezone.localdate()
    subscription = Subscription.objects.select_related(
        "customer", "plan", "plan__product", "plan__payment_term"
    ).select_for_update(of=("self",)).get(pk=subscription_id)
    if subscription.status != Subscription.Status.ACTIVE:
        return None
    if not subscription.next_billing_date or subscription.next_billing_date > as_of:
        return None
    if not subscription.current_period_start or not subscription.current_period_end:
        raise ValidationError({"subscription": "Subscription billing dates are required before recurring billing."})

    # A stale active subscription which has no billable period remaining is closed
    # without creating a future-period invoice.
    if subscription.expiry_date and subscription.current_period_start > subscription.expiry_date:
        subscription.status = Subscription.Status.CLOSED
        subscription.auto_renew = False
        subscription.closed_at = timezone.now()
        subscription.save(update_fields=["status", "auto_renew", "closed_at", "updated_at"])
        return None

    existing_invoice = Invoice.objects.filter(
        subscription=subscription,
        billing_period_start=subscription.current_period_start,
        billing_period_end=subscription.current_period_end,
    ).exclude(status=Invoice.Status.CANCELLED).first()
    invoice = existing_invoice or create_invoice(subscription=subscription, issue_date=as_of)
    if _close_after_current_period(subscription):
        subscription.status = Subscription.Status.CLOSED
        subscription.auto_renew = False
        subscription.closed_at = timezone.now()
    else:
        _advance_subscription_period(subscription)
    subscription.save(update_fields=[
        "status", "auto_renew", "closed_at", "current_period_start", "current_period_end",
        "next_billing_date", "updated_at",
    ])
    return None if existing_invoice else invoice


def generate_due_invoices(*, as_of=None, batch_size=500):
    """Process due subscriptions in bounded batches and return an operational summary."""
    from apps.subscriptions.models import Subscription

    as_of = as_of or timezone.localdate()
    due_ids = list(
        Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            next_billing_date__isnull=False,
            next_billing_date__lte=as_of,
        )
        .order_by("next_billing_date", "id")
        .values_list("id", flat=True)[:batch_size]
    )
    summary = {"as_of": as_of.isoformat(), "eligible": len(due_ids), "created": 0, "closed": 0, "failures": []}
    for subscription_id in due_ids:
        try:
            invoice = bill_due_subscription(subscription_id=subscription_id, as_of=as_of)
            if invoice:
                summary["created"] += 1
            elif Subscription.objects.only("status").get(pk=subscription_id).status == Subscription.Status.CLOSED:
                summary["closed"] += 1
        except Exception as exc:  # A malformed record must not block the remaining due subscriptions.
            summary["failures"].append({"subscription_id": subscription_id, "message": str(exc)})
    return summary


def _normalise_gstin(value):
    return (value or "").strip().upper()


def _profile_from_settings():
    config = getattr(settings, "GST_INVOICE_SUPPLIER", {})
    return SupplierProfile(
        legal_name=(config.get("legal_name") or "").strip(), address=(config.get("address") or "").strip(),
        gstin=_normalise_gstin(config.get("gstin")), state_name=(config.get("state_name") or "").strip(),
        state_code=(config.get("state_code") or "").strip(),
        authorised_signatory=(config.get("authorised_signatory") or "").strip(),
    )


def customer_snapshot(customer) -> dict:
    return {
        "name": customer.name, "company": customer.company, "email": customer.email, "phone": customer.phone,
        "billing_address": customer.billing_address, "city": customer.city, "state": customer.state,
        "country": customer.country, "postal_code": customer.postal_code, "tax_id": customer.tax_id,
    }


def populate_invoice_gst_snapshots(invoice):
    """Copy party details to a draft before it is confirmed and saved."""
    profile, customer = _profile_from_settings(), invoice.customer
    invoice.supplier_legal_name = invoice.supplier_legal_name or profile.legal_name
    invoice.supplier_address = invoice.supplier_address or profile.address
    invoice.supplier_gstin = invoice.supplier_gstin or profile.gstin
    invoice.supplier_state_name = invoice.supplier_state_name or profile.state_name
    invoice.supplier_state_code = invoice.supplier_state_code or profile.state_code
    invoice.supplier_authorised_signatory = invoice.supplier_authorised_signatory or profile.authorised_signatory
    invoice.recipient_legal_name = invoice.recipient_legal_name or customer.company or customer.name
    invoice.recipient_address = invoice.recipient_address or "\n".join(
        part for part in (customer.billing_address, customer.city, customer.state, customer.country, customer.postal_code) if part
    )
    invoice.recipient_gstin = invoice.recipient_gstin or _normalise_gstin(customer.tax_id)
    invoice.recipient_state_name = invoice.recipient_state_name or customer.state
    if not invoice.place_of_supply_state_name:
        invoice.place_of_supply_state_name = invoice.recipient_state_name
    if not invoice.place_of_supply_state_code:
        invoice.place_of_supply_state_code = invoice.recipient_state_code
    return invoice


@transaction.atomic
def recalculate_invoice_totals(invoice_id: int) -> Invoice:
    invoice = Invoice.objects.select_for_update().select_related("customer").get(pk=invoice_id)
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only draft invoices can be recalculated.")
    lines = invoice.lines.all()
    invoice.subtotal_amount = money(sum((line.unit_price * line.quantity - line.discount_amount for line in lines), Decimal("0.00")))
    invoice.tax_amount = money(sum((line.tax_amount for line in lines), Decimal("0.00")))
    invoice.discount_amount = money(sum((line.discount_amount for line in lines), Decimal("0.00")))
    invoice.total_amount = money(sum((line.line_total for line in lines), Decimal("0.00")))
    if not invoice.customer_snapshot:
        invoice.customer_snapshot = customer_snapshot(invoice.customer)
    populate_invoice_gst_snapshots(invoice)
    invoice.save(update_fields=[
        "subtotal_amount", "tax_amount", "discount_amount", "total_amount", "customer_snapshot",
        "supplier_legal_name", "supplier_address", "supplier_gstin", "supplier_state_name", "supplier_state_code",
        "supplier_authorised_signatory", "recipient_legal_name", "recipient_address", "recipient_gstin",
        "recipient_state_name", "recipient_state_code", "place_of_supply_state_name", "place_of_supply_state_code", "updated_at",
    ])
    return invoice


@transaction.atomic
def confirm_invoice(invoice_id: int) -> Invoice:
    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only draft invoices can be confirmed.")
    if not invoice.lines.exists():
        raise ValidationError("An invoice requires at least one line before confirmation.")
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
    """Stable, snapshot-only contract for a generic PDF renderer."""
    snapshot, lines = invoice.customer_snapshot or customer_snapshot(invoice.customer), invoice.lines.all().order_by("id")
    return {
        "invoice": {"number": invoice.invoice_number, "status": invoice.status, "issue_date": invoice.issue_date,
                    "due_date": invoice.due_date, "billing_period_start": invoice.billing_period_start,
                    "billing_period_end": invoice.billing_period_end, "currency": invoice.currency,
                    "payment_terms": invoice.payment_terms, "notes": invoice.notes, "subtotal_amount": invoice.subtotal_amount,
                    "discount_amount": invoice.discount_amount, "tax_amount": invoice.tax_amount,
                    "total_amount": invoice.total_amount, "amount_paid": invoice.amount_paid, "amount_due": invoice.amount_due},
        "customer": snapshot,
        "lines": [{"description": line.description, "hsn_sac": line.hsn_sac, "unit": line.unit, "quantity": line.quantity,
                   "unit_price": line.unit_price, "discount_amount": line.discount_amount, "tax_rate_percent": line.tax_rate_percent,
                   "tax_amount": line.tax_amount, "cess_amount": line.cess_amount, "line_total": line.line_total} for line in lines],
    }


def _recipient_details(invoice):
    return {"legal_name": invoice.recipient_legal_name, "address": invoice.recipient_address,
            "gstin": _normalise_gstin(invoice.recipient_gstin), "state_name": invoice.recipient_state_name,
            "state_code": invoice.recipient_state_code}


def _supplier_details(invoice):
    return {"legal_name": invoice.supplier_legal_name, "address": invoice.supplier_address,
            "gstin": _normalise_gstin(invoice.supplier_gstin), "state_name": invoice.supplier_state_name,
            "state_code": invoice.supplier_state_code, "authorised_signatory": invoice.supplier_authorised_signatory}


def _line_context(line, inter_state):
    taxable_value, gst_amount, cess_amount = money(Decimal(line.quantity) * line.unit_price - line.discount_amount), money(line.tax_amount), money(line.cess_amount)
    if inter_state:
        cgst = sgst = Decimal("0.00")
        igst = gst_amount
    else:
        cgst = (gst_amount / 2).quantize(PAISE, rounding=ROUND_HALF_UP)
        sgst, igst = gst_amount - cgst, Decimal("0.00")
    return {"description": line.description, "hsn_sac": line.hsn_sac, "quantity": line.quantity, "unit": line.unit,
            "unit_price": money(line.unit_price), "discount_amount": money(line.discount_amount), "taxable_value": taxable_value,
            "tax_rate_percent": line.tax_rate_percent, "cgst": cgst, "sgst": sgst, "igst": igst,
            "cess_amount": cess_amount, "line_total": money(line.line_total)}


def _amount_in_words(amount):
    value = money(amount)
    number, paise = int(value), int((value - int(value)) * 100)
    words = "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen".split()
    tens = "Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()
    def two_digits(value):
        return words[value] if value < 20 else tens[value // 10] + (" " + words[value % 10] if value % 10 else "")
    parts = []
    for divisor, label in ((10_000_000, "Crore"), (100_000, "Lakh"), (1_000, "Thousand")):
        if number >= divisor:
            count, number = divmod(number, divisor)
            parts.extend((two_digits(count), label))
    if number >= 100:
        parts.append(words[number // 100] + " Hundred")
        number %= 100
    if number:
        parts.append(two_digits(number))
    result = "Rupees " + " ".join(parts or ["Zero"])
    return result + (f" and {two_digits(paise)} Paise" if paise else "") + " Only"


def validate_tax_invoice(invoice, lines, supplier, recipient):
    errors = []
    if invoice.status not in {invoice.Status.CONFIRMED, invoice.Status.PAID}:
        errors.append("Only confirmed or paid invoices can be issued as tax invoices.")
    if not INVOICE_NUMBER_PATTERN.fullmatch(invoice.invoice_number):
        errors.append("Invoice number must be 1–16 characters and use only letters, digits, '-' or '/'.")
    for label, party in (("Supplier", supplier), ("Recipient", recipient)):
        if not party["legal_name"]: errors.append(f"{label} legal name is required.")
        if not party["address"]: errors.append(f"{label} address is required.")
        if not party["state_name"] or not party["state_code"]: errors.append(f"{label} state name and GST state code are required.")
    if not GSTIN_PATTERN.fullmatch(supplier["gstin"]): errors.append("Supplier GSTIN is missing or invalid.")
    if recipient["gstin"] and not GSTIN_PATTERN.fullmatch(recipient["gstin"]): errors.append("Recipient GSTIN is invalid.")
    if not invoice.place_of_supply_state_name or not invoice.place_of_supply_state_code: errors.append("Place of supply state name and GST state code are required.")
    if not supplier["authorised_signatory"]: errors.append("Supplier authorised signatory is required.")
    if not lines: errors.append("At least one invoice line is required.")
    for position, line in enumerate(lines, start=1):
        if not line.hsn_sac: errors.append(f"Line {position} requires an HSN/SAC code.")
        if not line.unit: errors.append(f"Line {position} requires a unit/UQC.")
    if errors: raise InvoiceDocumentValidationError(" ".join(errors))


def build_tax_invoice_context(invoice, *, strict=True):
    lines = list(invoice.lines.all())
    supplier, recipient = _supplier_details(invoice), _recipient_details(invoice)
    inter_state = supplier["state_code"] != invoice.place_of_supply_state_code
    document_lines = [_line_context(line, inter_state) for line in lines]
    if strict: validate_tax_invoice(invoice, lines, supplier, recipient)
    totals = {"taxable_value": sum((line["taxable_value"] for line in document_lines), Decimal("0.00")),
              "cgst": sum((line["cgst"] for line in document_lines), Decimal("0.00")),
              "sgst": sum((line["sgst"] for line in document_lines), Decimal("0.00")),
              "igst": sum((line["igst"] for line in document_lines), Decimal("0.00")),
              "cess": sum((line["cess_amount"] for line in document_lines), Decimal("0.00")), "total": money(invoice.total_amount)}
    return {"invoice": invoice, "supplier": supplier, "recipient": recipient, "lines": document_lines, "totals": totals,
            "inter_state": inter_state, "amount_in_words": _amount_in_words(invoice.total_amount), "generated_at": timezone.localtime()}


def render_tax_invoice_html(invoice, *, strict=True):
    return render_to_string("billing/invoices/tax_invoice.html", build_tax_invoice_context(invoice, strict=strict))


@transaction.atomic
def generate_invoice_pdf(invoice_id: int) -> Invoice:
    """Render a durable, downloadable PDF from immutable invoice snapshots."""
    invoice = Invoice.objects.select_for_update().select_related("customer").prefetch_related("lines").get(pk=invoice_id)
    if invoice.status not in {Invoice.Status.CONFIRMED, Invoice.Status.PAID}:
        raise ValidationError("Only confirmed or paid invoices can generate a PDF.")

    snapshot = invoice.customer_snapshot or customer_snapshot(invoice.customer)
    styles = getSampleStyleSheet()
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    story = [
        Paragraph("TAX INVOICE", styles["Title"]),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Invoice:</b> {invoice.invoice_number}<br/><b>Issue date:</b> {invoice.issue_date:%d %b %Y}<br/><b>Due date:</b> {invoice.due_date:%d %b %Y}", styles["Normal"]),
        Spacer(1, 4 * mm),
        Paragraph(f"<b>Bill to:</b> {snapshot.get('company') or snapshot.get('name', '')}<br/>{snapshot.get('billing_address', '')}<br/>{snapshot.get('email', '')}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]
    rows = [["Description", "Qty", "Unit price", "Tax", "Total"]]
    for line in invoice.lines.all():
        rows.append([line.description, str(line.quantity), f"{invoice.currency} {line.unit_price:.2f}", f"{line.tax_rate_percent:.2f}%", f"{invoice.currency} {line.line_total:.2f}"])
    rows.extend([
        ["", "", "", "Subtotal", f"{invoice.currency} {invoice.subtotal_amount:.2f}"],
        ["", "", "", "Tax", f"{invoice.currency} {invoice.tax_amount:.2f}"],
        ["", "", "", "Total", f"{invoice.currency} {invoice.total_amount:.2f}"],
    ])
    table = Table(rows, colWidths=[70 * mm, 15 * mm, 30 * mm, 20 * mm, 35 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24324B")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D7E2")), ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (3, -3), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (3, -1), (-1, -1), colors.HexColor("#EAF0F8")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([table, Spacer(1, 6 * mm), Paragraph("This is a system-generated invoice.", styles["Italic"])])
    document.build(story)
    invoice.pdf_document.save(f"{invoice.invoice_number}.pdf", ContentFile(buffer.getvalue()), save=False)
    invoice.save(update_fields=["pdf_document", "updated_at"])
    return invoice


def _recover_or_create_due_invoice(subscription, run_date):
    """Return whether a new invoice was created for the subscription's current period."""
    existing_invoice = Invoice.objects.filter(
        subscription=subscription,
        billing_period_start=subscription.current_period_start,
        billing_period_end=subscription.current_period_end,
    ).exclude(status=Invoice.Status.CANCELLED).first()
    if existing_invoice:
        return False

    create_invoice(subscription=subscription, issue_date=run_date)
    return True


def _process_due_subscription(subscription_id, run_date):
    """Invoice every missed period for one subscription in one locked transaction."""
    from apps.subscriptions.models import Subscription
    from apps.subscriptions.services import advance_subscription_billing_period

    created = existing = 0
    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().select_related("plan").get(pk=subscription_id)
        while (
            subscription.status == Subscription.Status.ACTIVE
            and subscription.next_billing_date
            and subscription.next_billing_date <= run_date
        ):
            if _recover_or_create_due_invoice(subscription, run_date):
                created += 1
            else:
                existing += 1
            subscription = advance_subscription_billing_period(subscription_id=subscription.id)
    return created, existing


def run_recurring_billing(*, run_date=None, triggered_by=None) -> BillingRun:
    """Generate outstanding recurring invoices and persist a complete run audit.

    Each subscription is processed in an isolated transaction so a malformed
    subscription cannot prevent other customers from being invoiced. Re-running
    a date is safe: existing invoices are retained and their subscriptions are
    advanced without creating duplicates.
    """
    from apps.subscriptions.models import Subscription

    run_date = run_date or timezone.localdate()
    billing_run = BillingRun.objects.create(run_date=run_date, triggered_by=triggered_by)
    candidate_ids = list(
        Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            next_billing_date__isnull=False,
            next_billing_date__lte=run_date,
        ).values_list("id", flat=True)
    )
    failures = []
    invoices_created = invoices_existing = 0

    for subscription_id in candidate_ids:
        try:
            created, existing = _process_due_subscription(subscription_id, run_date)
            invoices_created += created
            invoices_existing += existing
        except Exception as exc:
            failures.append({"subscription_id": subscription_id, "error": str(exc)})

    if failures:
        final_status = BillingRun.Status.PARTIAL if invoices_created or invoices_existing else BillingRun.Status.FAILED
    else:
        final_status = BillingRun.Status.COMPLETED

    billing_run.subscriptions_considered = len(candidate_ids)
    billing_run.invoices_created = invoices_created
    billing_run.invoices_existing = invoices_existing
    billing_run.failures = failures
    billing_run.status = final_status
    billing_run.finished_at = timezone.now()
    billing_run.save(update_fields=[
        "subscriptions_considered", "invoices_created", "invoices_existing", "failures", "status", "finished_at", "updated_at",
    ])
    return billing_run


@transaction.atomic
def send_invoice_email(invoice_id: int) -> Invoice:
    """Email a final invoice with its generated PDF attached."""
    invoice = Invoice.objects.select_for_update().select_related("customer").get(pk=invoice_id)
    if invoice.status not in {Invoice.Status.CONFIRMED, Invoice.Status.PAID}:
        raise ValidationError("Only confirmed or paid invoices can be sent.")
    if not invoice.customer.email:
        raise ValidationError({"invoice": "The invoice customer does not have an email address."})

    if not invoice.pdf_document:
        generate_invoice_pdf(invoice.id)
        invoice.refresh_from_db()

    message = EmailMessage(
        subject=f"Invoice {invoice.invoice_number}",
        body=(
            f"Hello {invoice.customer.name},\n\n"
            f"Your invoice {invoice.invoice_number} for {invoice.currency} {invoice.total_amount:.2f} is attached.\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[invoice.customer.email],
    )
    with invoice.pdf_document.open("rb") as document:
        message.attach(f"{invoice.invoice_number}.pdf", document.read(), "application/pdf")
    message.send(fail_silently=False)
    invoice.email_sent_at = timezone.now()
    invoice.save(update_fields=["email_sent_at", "updated_at"])
    return invoice
