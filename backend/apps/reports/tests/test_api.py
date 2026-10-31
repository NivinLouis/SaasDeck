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
