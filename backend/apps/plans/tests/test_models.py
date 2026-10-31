from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.plans.models import Plan


class PlanModelTests(TestCase):
    def test_create_plan(self):
        plan = Plan.objects.create(
            name="Pro Monthly",
            code="pro-monthly",
            billing_interval=Plan.BillingInterval.MONTHLY,
            base_price=Decimal("49.99"),
            minimum_quantity=1,
        )
        self.assertEqual(plan.billing_interval, "MONTHLY")
        self.assertTrue(plan.allow_auto_renewal)
        self.assertIn("Pro Monthly", str(plan))

    def test_plan_code_uniqueness(self):
        Plan.objects.create(name="Plan 1", code="plan-unique", base_price=Decimal("10.00"))
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name="Plan 2", code="plan-unique", base_price=Decimal("20.00"))
