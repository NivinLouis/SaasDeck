from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import shutil

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import Invoice, InvoiceLine
from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.catalog.models import Product
from apps.subscriptions.models import Subscription

User = get_user_model()


class InvoiceApiTests(APITestCase):
    def setUp(self):
        self.password = "Correct!Pass9"
        self.staff = User.objects.create_user(email="staff@example.com", full_name="Staff", password=self.password, role="staff")
        self.customer_user = User.objects.create_user(email="customer@example.com", full_name="Customer", password=self.password)
        self.other_user = User.objects.create_user(email="other@example.com", full_name="Other", password=self.password)
        self.customer = Customer.objects.create(user=self.customer_user, name="Customer Co", email="customer@example.com")
        self.other_customer = Customer.objects.create(user=self.other_user, name="Other Co", email="other@example.com")
        self.plan = Plan.objects.create(name="Pro", code="pro", price=Decimal("100.00"))
        self.invoice = Invoice.objects.create(
            invoice_number="INV-2026-00001",
            customer=self.customer,
            due_date=date.today() + timedelta(days=14),
            total_amount=Decimal("100.00"),
        )
        InvoiceLine.objects.create(
            invoice=self.invoice,
            description="Pro plan",
            quantity=1,
            unit_price=Decimal("100.00"),
            line_total=Decimal("100.00"),
        )

    def test_customer_only_sees_own_invoice(self):
        Invoice.objects.create(
            invoice_number="INV-2026-00002",
            customer=self.other_customer,
            due_date=date.today() + timedelta(days=14),
            total_amount=Decimal("40.00"),
        )
        self.client.force_authenticate(self.customer_user)
        response = self.client.get("/api/v1/invoices")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["invoice_number"], self.invoice.invoice_number)

    def test_customer_cannot_confirm_invoice(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.post(f"/api/v1/invoices/{self.invoice.uuid}/confirm")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_confirm_snapshots_customer_for_pdf(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(f"/api/v1/invoices/{self.invoice.uuid}/confirm")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, Invoice.Status.CONFIRMED)
        self.assertEqual(self.invoice.customer_snapshot["name"], "Customer Co")
        self.assertEqual(self.invoice.total_amount, Decimal("100.00"))

    def test_pdf_endpoint_is_private_and_reports_pending_generation(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.get(f"/api/v1/invoices/{self.invoice.uuid}/pdf")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["code"], "pdf_not_ready")

    def test_staff_can_create_invoice_from_an_active_subscription(self):
        product = Product.objects.create(name="Pro service", sku="PRO-SERVICE", sales_price=Decimal("100.00"))
        plan = Plan.objects.create(name="Pro yearly", code="pro-yearly", product=product, price=Decimal("1200.00"), billing_interval="yearly")
        subscription = Subscription.objects.create(
            subscription_number="SUB-INV-001", customer=self.customer, plan=plan, status=Subscription.Status.ACTIVE,
            start_date=date(2026, 1, 1), current_period_start=date(2026, 1, 1), current_period_end=date(2026, 12, 31),
            next_billing_date=date(2027, 1, 1), payment_terms="Immediate Payment",
        )
        self.client.force_authenticate(self.staff)

        response = self.client.post("/api/v1/invoices", {"subscription": subscription.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_amount"], "1200.00")
        self.assertEqual(response.data["lines"][0]["description"], "Pro yearly")

    def test_confirmation_generates_a_downloadable_pdf(self):
        self.client.force_authenticate(self.staff)
        media_root = Path(settings.BASE_DIR) / ".test-invoice-media"
        shutil.rmtree(media_root, ignore_errors=True)
        try:
            with override_settings(MEDIA_ROOT=media_root, INVOICE_PDF_ASYNC=False):
                confirm = self.client.post(f"/api/v1/invoices/{self.invoice.uuid}/confirm")
                self.invoice.refresh_from_db()
                download = self.client.get(f"/api/v1/invoices/{self.invoice.uuid}/pdf")
                pdf_content = b"".join(download.streaming_content)
        finally:
            shutil.rmtree(media_root, ignore_errors=True)

        self.assertEqual(confirm.status_code, status.HTTP_200_OK)
        self.assertTrue(self.invoice.pdf_document.name.endswith(".pdf"))
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download["Content-Type"], "application/pdf")
        self.assertTrue(pdf_content.startswith(b"%PDF"))
