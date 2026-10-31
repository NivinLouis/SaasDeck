from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.billing.models import Invoice
from apps.billing.services import InvoiceDocumentValidationError, build_tax_invoice_context, render_tax_invoice_html


SUPPLIER = {
    "legal_name": "SaaSDeck Technologies Private Limited",
    "address": "42 Example Road\nKochi, Kerala - 682001",
    "gstin": "32ABCDE1234F1Z5",
    "state_name": "Kerala",
    "state_code": "32",
    "authorised_signatory": "Accounts Team",
}


class InvoiceDocumentTests(SimpleTestCase):
    def invoice(self, *, place_of_supply="32", hsn_sac="998314"):
        customer = SimpleNamespace(
            name="Asha Nair",
            company="Acme Consulting Pvt Ltd",
            billing_address="15 Market Street",
            city="Bengaluru",
            state="Karnataka",
            country="India",
            postal_code="560001",
            tax_id="29ABCDE1234F1Z7",
        )
        line = SimpleNamespace(
            description="SaaSDeck Pro subscription — October 2026",
            hsn_sac=hsn_sac,
            quantity=1,
            unit="MONTH",
            unit_price=Decimal("1000.00"),
            discount_amount=Decimal("0.00"),
            tax_rate_percent=Decimal("18.00"),
            tax_amount=Decimal("180.00"),
            cess_amount=Decimal("0.00"),
            line_total=Decimal("1180.00"),
        )
        return SimpleNamespace(
            Status=Invoice.Status,
            status=Invoice.Status.CONFIRMED,
            customer=customer,
            supplier_legal_name="",
            supplier_address="",
            supplier_gstin="",
            supplier_state_name="",
            supplier_state_code="",
            supplier_authorised_signatory="",
            recipient_legal_name="",
            recipient_address="",
            recipient_gstin="",
            recipient_state_name="",
            recipient_state_code="29",
            place_of_supply_state_name="Kerala" if place_of_supply == "32" else "Karnataka",
            place_of_supply_state_code=place_of_supply,
            invoice_number="INV/2026-00001",
            issue_date=date(2026, 10, 31),
            due_date=date(2026, 11, 15),
            payment_terms="Net 15",
            reverse_charge=False,
            irn="",
            acknowledgement_number="",
            total_amount=Decimal("1180.00"),
            notes="Thank you for your business.",
            lines=SimpleNamespace(all=lambda: [line]),
        )

    def _complete_snapshots(self, invoice):
        invoice.supplier_legal_name = SUPPLIER["legal_name"]
        invoice.supplier_address = SUPPLIER["address"]
        invoice.supplier_gstin = SUPPLIER["gstin"]
        invoice.supplier_state_name = SUPPLIER["state_name"]
        invoice.supplier_state_code = SUPPLIER["state_code"]
        invoice.supplier_authorised_signatory = SUPPLIER["authorised_signatory"]
        invoice.recipient_legal_name = invoice.customer.company
        invoice.recipient_address = "15 Market Street\nBengaluru, Karnataka - 560001"
        invoice.recipient_gstin = invoice.customer.tax_id
        invoice.recipient_state_name = invoice.customer.state
        return invoice

    @override_settings(GST_INVOICE_SUPPLIER=SUPPLIER)
    def test_intra_state_tax_is_split_between_cgst_and_sgst(self):
        invoice = self._complete_snapshots(self.invoice())
        context = build_tax_invoice_context(invoice)

        self.assertFalse(context["inter_state"])
        self.assertEqual(context["totals"]["cgst"], Decimal("90.00"))
        self.assertEqual(context["totals"]["sgst"], Decimal("90.00"))
        self.assertIn("TAX INVOICE", render_tax_invoice_html(invoice))

    @override_settings(GST_INVOICE_SUPPLIER=SUPPLIER)
    def test_inter_state_tax_is_shown_as_igst(self):
        context = build_tax_invoice_context(self._complete_snapshots(self.invoice(place_of_supply="29")))

        self.assertTrue(context["inter_state"])
        self.assertEqual(context["totals"]["igst"], Decimal("180.00"))

    @override_settings(GST_INVOICE_SUPPLIER=SUPPLIER)
    def test_missing_hsn_sac_prevents_final_document(self):
        with self.assertRaisesRegex(InvoiceDocumentValidationError, "HSN/SAC"):
            build_tax_invoice_context(self._complete_snapshots(self.invoice(hsn_sac="")))
