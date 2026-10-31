"""GST-safe invoice document rendering and validation services.

The document is intentionally rendered as HTML first.  It has page-size and print
styles so a PDF engine can use the exact same source without a second layout.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone


PAISE = Decimal("0.01")
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


def _money(value):
    return Decimal(value or 0).quantize(PAISE, rounding=ROUND_HALF_UP)


def _normalise_gstin(value):
    return (value or "").strip().upper()


def _profile_from_settings():
    config = getattr(settings, "GST_INVOICE_SUPPLIER", {})
    return SupplierProfile(
        legal_name=(config.get("legal_name") or "").strip(),
        address=(config.get("address") or "").strip(),
        gstin=_normalise_gstin(config.get("gstin")),
        state_name=(config.get("state_name") or "").strip(),
        state_code=(config.get("state_code") or "").strip(),
        authorised_signatory=(config.get("authorised_signatory") or "").strip(),
    )


def _recipient_details(invoice):
    """Return the recipient's immutable issue-time identity."""
    return {
        "legal_name": invoice.recipient_legal_name,
        "address": invoice.recipient_address,
        "gstin": _normalise_gstin(invoice.recipient_gstin),
        "state_name": invoice.recipient_state_name,
        "state_code": invoice.recipient_state_code,
    }


def _supplier_details(invoice):
    return {
        "legal_name": invoice.supplier_legal_name,
        "address": invoice.supplier_address,
        "gstin": _normalise_gstin(invoice.supplier_gstin),
        "state_name": invoice.supplier_state_name,
        "state_code": invoice.supplier_state_code,
        "authorised_signatory": invoice.supplier_authorised_signatory,
    }


def populate_invoice_gst_snapshots(invoice):
    """Copy party details to a draft before it is confirmed and saved."""
    profile = _profile_from_settings()
    customer = invoice.customer
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


def _line_context(line, inter_state):
    taxable_value = _money(Decimal(line.quantity) * line.unit_price - line.discount_amount)
    gst_amount = _money(line.tax_amount)
    cess_amount = _money(line.cess_amount)
    if inter_state:
        cgst = sgst = Decimal("0.00")
        igst = gst_amount
    else:
        cgst = (gst_amount / 2).quantize(PAISE, rounding=ROUND_HALF_UP)
        sgst = gst_amount - cgst
        igst = Decimal("0.00")
    return {
        "description": line.description,
        "hsn_sac": line.hsn_sac,
        "quantity": line.quantity,
        "unit": line.unit,
        "unit_price": _money(line.unit_price),
        "discount_amount": _money(line.discount_amount),
        "taxable_value": taxable_value,
        "tax_rate_percent": line.tax_rate_percent,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "cess_amount": cess_amount,
        "line_total": _money(line.line_total),
    }


def _amount_in_words(amount):
    """Small, dependency-free INR formatter for a document footer."""
    value = _money(amount)
    number = int(value)
    paise = int((value - number) * 100)
    words_0_19 = (
        "Zero One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve "
        "Thirteen Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen"
    ).split()
    tens = "Zero Ten Twenty Thirty Forty Fifty Sixty Seventy Eighty Ninety".split()

    def two_digits(value):
        if value < 20:
            return words_0_19[value]
        return tens[value // 10] + (" " + words_0_19[value % 10] if value % 10 else "")

    def three_digits(value):
        return (words_0_19[value // 100] + " Hundred" + (" " if value % 100 else "")) if value >= 100 else ""

    parts = []
    for divisor, label in ((10_000_000, "Crore"), (100_000, "Lakh"), (1_000, "Thousand")):
        if number >= divisor:
            count, number = divmod(number, divisor)
            parts.extend((two_digits(count), label))
    if number >= 100:
        parts.append(three_digits(number))
        number %= 100
    if number:
        parts.append(two_digits(number))
    result = "Rupees " + " ".join(parts or ["Zero"])
    if paise:
        result += f" and {two_digits(paise)} Paise"
    return result + " Only"


def validate_tax_invoice(invoice, lines, supplier, recipient):
    """Validate the template's mandatory Rule 46 information before publishing."""
    errors = []
    if invoice.status not in {invoice.Status.CONFIRMED, invoice.Status.PAID}:
        errors.append("Only confirmed or paid invoices can be issued as tax invoices.")
    if not INVOICE_NUMBER_PATTERN.fullmatch(invoice.invoice_number):
        errors.append("Invoice number must be 1–16 characters and use only letters, digits, '-' or '/'.")
    for label, party in (("Supplier", supplier), ("Recipient", recipient)):
        if not party["legal_name"]:
            errors.append(f"{label} legal name is required.")
        if not party["address"]:
            errors.append(f"{label} address is required.")
        if not party["state_name"] or not party["state_code"]:
            errors.append(f"{label} state name and GST state code are required.")
    if not GSTIN_PATTERN.fullmatch(supplier["gstin"]):
        errors.append("Supplier GSTIN is missing or invalid.")
    if recipient["gstin"] and not GSTIN_PATTERN.fullmatch(recipient["gstin"]):
        errors.append("Recipient GSTIN is invalid.")
    if not invoice.place_of_supply_state_name or not invoice.place_of_supply_state_code:
        errors.append("Place of supply state name and GST state code are required.")
    if not supplier["authorised_signatory"]:
        errors.append("An authorised signatory is required in GST_INVOICE_SUPPLIER settings.")
    if not lines:
        errors.append("At least one invoice line is required.")
    for position, line in enumerate(lines, start=1):
        if not line.hsn_sac:
            errors.append(f"Line {position} requires an HSN/SAC code.")
        if not line.unit:
            errors.append(f"Line {position} requires a unit/UQC.")
    if errors:
        raise InvoiceDocumentValidationError(" ".join(errors))


def build_tax_invoice_context(invoice, *, strict=True):
    """Build a complete, immutable-looking document context from an invoice."""
    lines = list(invoice.lines.all())
    supplier = _supplier_details(invoice)
    recipient = _recipient_details(invoice)
    inter_state = supplier["state_code"] != invoice.place_of_supply_state_code
    document_lines = [_line_context(line, inter_state) for line in lines]
    if strict:
        validate_tax_invoice(invoice, lines, supplier, recipient)

    totals = {
        "taxable_value": sum((line["taxable_value"] for line in document_lines), Decimal("0.00")),
        "cgst": sum((line["cgst"] for line in document_lines), Decimal("0.00")),
        "sgst": sum((line["sgst"] for line in document_lines), Decimal("0.00")),
        "igst": sum((line["igst"] for line in document_lines), Decimal("0.00")),
        "cess": sum((line["cess_amount"] for line in document_lines), Decimal("0.00")),
        "total": _money(invoice.total_amount),
    }
    return {
        "invoice": invoice,
        "supplier": supplier,
        "recipient": recipient,
        "lines": document_lines,
        "totals": totals,
        "inter_state": inter_state,
        "amount_in_words": _amount_in_words(invoice.total_amount),
        "generated_at": timezone.localtime(),
    }


def render_tax_invoice_html(invoice, *, strict=True):
    return render_to_string("billing/invoices/tax_invoice.html", build_tax_invoice_context(invoice, strict=strict))
