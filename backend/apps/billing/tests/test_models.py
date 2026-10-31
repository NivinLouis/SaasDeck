from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.billing.models import Invoice, InvoiceLine


class BillingModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Globex Corp", email="billing@globex.com")
        self.plan = Plan.objects.create(name="Pro", code="pro-plan", price=Decimal("100.00"))
        self.subscription = Subscription.objects.create(
            subscription_number="SUB-GLX-001",
            customer=self.customer,
            plan=self.plan,
            status=Subscription.Status.ACTIVE,
        )

    def test_invoice_creation_and_snapshots(self):
        invoice = Invoice.objects.create(
            invoice_number="INV-2026-00001",
            customer=self.customer,
            subscription=self.subscription,
            status=Invoice.Status.CONFIRMED,
            billing_period_start=date(2026, 1, 1),
            billing_period_end=date(2026, 1, 31),
            issue_date=date(2026, 1, 31),
            due_date=date(2026, 2, 15),
            total_amount=Decimal("100.00"),
            amount_paid=Decimal("40.00"),
        )
        self.assertEqual(invoice.amount_due, Decimal("60.00"))
        # Due date Feb 15, 2026 is before current date, so it is overdue
        self.assertTrue(invoice.is_overdue)

        line = InvoiceLine.objects.create(
            invoice=invoice,
            description="Pro Plan (Jan 2026)",
            quantity=1,
            unit_price=Decimal("100.00"),
            line_total=Decimal("100.00"),
        )
        self.assertEqual(line.line_total, Decimal("100.00"))

    def test_idempotent_billing_prevents_duplicate_period_invoice(self):
        # First billing run succeeds
        Invoice.objects.create(
            invoice_number="INV-2026-00010",
            customer=self.customer,
            subscription=self.subscription,
            billing_period_start=date(2026, 3, 1),
            billing_period_end=date(2026, 3, 31),
            issue_date=date(2026, 3, 31),
            due_date=date(2026, 4, 15),
            total_amount=Decimal("100.00"),
        )

        # Repeated billing run for the exact same period must fail via database unique constraint
        with self.assertRaises(IntegrityError):
            Invoice.objects.create(
                invoice_number="INV-2026-00011",
                customer=self.customer,
                subscription=self.subscription,
                billing_period_start=date(2026, 3, 1),
                billing_period_end=date(2026, 3, 31),
                issue_date=date(2026, 3, 31),
                due_date=date(2026, 4, 15),
                total_amount=Decimal("100.00"),
            )
