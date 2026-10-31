from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.catalog.models import Product
from apps.subscriptions.models import Subscription, SubscriptionLine


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Acme Corp", email="contact@acme.com")
        self.plan = Plan.objects.create(name="Business Plan", code="biz-monthly", base_price=Decimal("199.00"))
        self.product = Product.objects.create(name="Seat License", sku="SEAT-LIC", sales_price=Decimal("50.00"))

    def test_subscription_creation_and_lifecycle(self):
        sub = Subscription.objects.create(
            subscription_number="SUB-2026-0001",
            customer=self.customer,
            plan=self.plan,
            status=Subscription.Status.ACTIVE,
            start_date=date(2026, 1, 1),
            next_billing_date=date(2026, 2, 1),
        )
        self.assertEqual(sub.status, "ACTIVE")
        self.assertIn("SUB-2026-0001", str(sub))

        line = SubscriptionLine.objects.create(
            subscription=sub,
            product=self.product,
            quantity=5,
            unit_price=Decimal("50.00"),
        )
        self.assertEqual(line.subtotal, Decimal("250.00"))

    def test_unique_subscription_number(self):
        Subscription.objects.create(subscription_number="SUB-DUP", customer=self.customer, plan=self.plan)
        with self.assertRaises(IntegrityError):
            Subscription.objects.create(subscription_number="SUB-DUP", customer=self.customer, plan=self.plan)
