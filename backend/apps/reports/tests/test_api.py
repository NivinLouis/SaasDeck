from datetime import date
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.customers.models import Customer


class DashboardApiTests(APITestCase):
    def test_staff_can_view_financial_summary(self):
        staff = User.objects.create_user(email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF)
        customer_user = User.objects.create_user(email="customer@example.com", full_name="Customer", password="SafePassword!1")
        customer = Customer.objects.create(user=customer_user, name="Customer", email="customer@example.com")
        Invoice.objects.create(invoice_number="INV-RPT", customer=customer, status="CONFIRMED", issue_date=date(2026, 1, 1), due_date=date(2026, 1, 2), total_amount=Decimal("100.00"), amount_paid=Decimal("40.00"), payment_status="PARTIALLY_PAID")
        self.client.force_authenticate(staff)
        response = self.client.get("/api/v1/reports/dashboard")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoices"]["outstanding_total"], Decimal("60.00"))
        self.assertEqual(response.data["invoices"]["overdue_count"], 1)
        self.assertEqual(response.data["trend"][0]["invoice_count"], 1)

    def test_date_filters_and_csv_export(self):
        staff = User.objects.create_user(email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF)
        customer_user = User.objects.create_user(email="customer@example.com", full_name="Customer", password="SafePassword!1")
        customer = Customer.objects.create(user=customer_user, name="Customer", email="customer@example.com")
        Invoice.objects.create(invoice_number="INV-OLD", customer=customer, status="CONFIRMED", issue_date=date(2025, 12, 1), due_date=date(2025, 12, 2), total_amount=Decimal("25.00"))
        Invoice.objects.create(invoice_number="INV-NEW", customer=customer, status="CONFIRMED", issue_date=date(2026, 2, 1), due_date=date(2026, 2, 2), total_amount=Decimal("50.00"))
        self.client.force_authenticate(staff)
        response = self.client.get("/api/v1/reports/dashboard?start_date=2026-01-01&end_date=2026-12-31")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["invoices"]["total"], 1)
        export = self.client.get("/api/v1/reports/invoices.csv?start_date=2026-01-01")
        self.assertEqual(export.status_code, status.HTTP_200_OK)
        self.assertIn("INV-NEW", export.content.decode())
        self.assertNotIn("INV-OLD", export.content.decode())
