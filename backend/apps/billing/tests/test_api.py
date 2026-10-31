from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import Invoice, InvoiceLine
from apps.customers.models import Customer
from apps.plans.models import Plan

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
