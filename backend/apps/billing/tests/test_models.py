from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.customers.models import Customer
from apps.catalog.models import Product
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.billing.models import Invoice, InvoiceLine
from apps.billing.services import generate_due_invoices


class BillingModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Globex Corp", email="billing@globex.com")
        self.product = Product.objects.create(name="Pro service", sku="PRO-SERVICE", sales_price=Decimal("100.00"))
        self.plan = Plan.objects.create(name="Pro", code="pro-plan", product=self.product, price=Decimal("100.00"))
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

    def test_due_billing_creates_one_invoice_and_advances_the_period(self):
        self.subscription.current_period_start = date(2026, 1, 1)
        self.subscription.current_period_end = date(2026, 1, 31)
        self.subscription.next_billing_date = date(2026, 2, 1)
        self.subscription.save(update_fields=["current_period_start", "current_period_end", "next_billing_date"])

        first_run = generate_due_invoices(as_of=date(2026, 2, 1))
        self.subscription.refresh_from_db()

        self.assertEqual(first_run["created"], 1)
        self.assertEqual(Invoice.objects.filter(subscription=self.subscription).count(), 1)
        self.assertEqual(self.subscription.current_period_start, date(2026, 2, 1))
        self.assertEqual(self.subscription.current_period_end, date(2026, 2, 28))
        self.assertEqual(self.subscription.next_billing_date, date(2026, 3, 1))

        repeated_run = generate_due_invoices(as_of=date(2026, 2, 1))
        self.assertEqual(repeated_run["created"], 0)
        self.assertEqual(Invoice.objects.filter(subscription=self.subscription).count(), 1)

    def test_non_renewing_subscription_closes_after_its_final_billing_period(self):
        self.subscription.auto_renew = False
        self.subscription.current_period_start = date(2026, 1, 1)
        self.subscription.current_period_end = date(2026, 1, 31)
        self.subscription.next_billing_date = date(2026, 2, 1)
        self.subscription.save(update_fields=["auto_renew", "current_period_start", "current_period_end", "next_billing_date"])

        generate_due_invoices(as_of=date(2026, 2, 1))
        self.subscription.refresh_from_db()

        self.assertEqual(self.subscription.status, Subscription.Status.CLOSED)
        self.assertEqual(Invoice.objects.filter(subscription=self.subscription).count(), 1)
