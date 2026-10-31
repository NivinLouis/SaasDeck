from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.customers.models import Customer
from apps.billing.models import Invoice
from apps.payments.models import Payment


class PaymentModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Stark Industries", email="tony@stark.com")
        self.invoice = Invoice.objects.create(
            invoice_number="INV-STARK-01",
            customer=self.customer,
            issue_date=date(2026, 4, 1),
            due_date=date(2026, 5, 1),
            total_amount=Decimal("500.00"),
        )

    def test_payment_creation(self):
        payment = Payment.objects.create(
            payment_number="PAY-2026-0001",
            invoice=self.invoice,
            customer=self.customer,
            payment_method=Payment.PaymentMethod.UPI,
            amount=Decimal("500.00"),
            status=Payment.Status.COMPLETED,
        )
        self.assertEqual(payment.status, "COMPLETED")
        self.assertEqual(payment.amount, Decimal("500.00"))
        self.assertIn("PAY-2026-0001", str(payment))

    def test_payment_unique_number(self):
        Payment.objects.create(
            payment_number="PAY-DUP",
            invoice=self.invoice,
            customer=self.customer,
            amount=Decimal("100.00"),
        )
        with self.assertRaises(IntegrityError):
            Payment.objects.create(
                payment_number="PAY-DUP",
                invoice=self.invoice,
                customer=self.customer,
                amount=Decimal("100.00"),
            )
