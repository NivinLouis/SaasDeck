from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.customers.models import Customer
from apps.payments.models import Payment


class PaymentApiTests(APITestCase):
    def setUp(self):
        self.customer_user = User.objects.create_user(
            email="customer@example.com", full_name="Customer", password="SafePassword!1"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF
        )
        self.customer = Customer.objects.create(user=self.customer_user, name="Customer", email=self.customer_user.email)
        self.invoice = Invoice.objects.create(
            invoice_number="INV-PAY-001",
            customer=self.customer,
            status=Invoice.Status.CONFIRMED,
            issue_date=date(2026, 1, 1),
            due_date=date(2026, 1, 31),
            total_amount=Decimal("100.00"),
        )

    def record(self, amount):
        self.client.force_authenticate(self.staff)
        return self.client.post(
            reverse("payment-list"),
            {
                "invoice": self.invoice.id,
                "amount": amount,
                "payment_method": Payment.PaymentMethod.UPI,
                "transaction_reference": "UPI-123",
            },
            format="json",
        )

    def test_partial_then_full_payment_updates_invoice(self):
        partial = self.record("40.00")
        self.assertEqual(partial.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("40.00"))
        self.assertEqual(self.invoice.payment_status, Invoice.PaymentStatus.PARTIAL)
        self.assertEqual(self.invoice.status, Invoice.Status.CONFIRMED)

        full = self.record("60.00")
        self.assertEqual(full.status_code, status.HTTP_201_CREATED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("100.00"))
        self.assertEqual(self.invoice.payment_status, Invoice.PaymentStatus.PAID)
        self.assertEqual(self.invoice.status, Invoice.Status.PAID)
        self.assertIsNotNone(self.invoice.paid_at)

    def test_overpayment_is_rejected(self):
        response = self.record("100.01")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data["fields"])
        self.assertEqual(Payment.objects.count(), 0)

    def test_refund_reopens_a_paid_invoice(self):
        payment_response = self.record("100.00")
        refund_response = self.client.post(
            reverse("payment-refund", kwargs={"uuid": payment_response.data["uuid"]}), {}, format="json"
        )

        self.assertEqual(refund_response.status_code, status.HTTP_200_OK)
        self.assertEqual(refund_response.data["status"], Payment.Status.REFUNDED)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.amount_paid, Decimal("0.00"))
        self.assertEqual(self.invoice.payment_status, Invoice.PaymentStatus.UNPAID)
        self.assertEqual(self.invoice.status, Invoice.Status.CONFIRMED)
        self.assertIsNone(self.invoice.paid_at)

    def test_customer_can_view_own_payment_but_cannot_record_or_refund(self):
        payment_response = self.record("40.00")
        self.client.force_authenticate(self.customer_user)
        listed = self.client.get(reverse("payment-list"))
        create = self.client.post(
            reverse("payment-list"), {"invoice": self.invoice.id, "amount": "1.00"}, format="json"
        )
        refund = self.client.post(
            reverse("payment-refund", kwargs={"uuid": payment_response.data["uuid"]}), {}, format="json"
        )

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(listed.data["count"], 1)
        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(refund.status_code, status.HTTP_403_FORBIDDEN)
