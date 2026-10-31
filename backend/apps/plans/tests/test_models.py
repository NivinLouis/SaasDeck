from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.plans.models import Plan, PaymentTerm


class PlanModelTests(TestCase):
    def test_create_payment_term(self):
        term = PaymentTerm.objects.create(name="Net 30", days=30)
        self.assertEqual(str(term), "Net 30 (30 days)")
        self.assertTrue(term.is_active)

    def test_create_plan_with_payment_term(self):
        term = PaymentTerm.objects.create(name="Immediate", days=0)
        plan = Plan.objects.create(
            name="Pro Monthly",
            code="pro-monthly",
            billing_interval=Plan.BillingInterval.MONTHLY,
            price=Decimal("49.99"),
            minimum_quantity=1,
            payment_term=term,
            available_from=date(2026, 1, 1),
            available_until=date(2026, 12, 31),
        )
        self.assertEqual(plan.billing_interval, "monthly")
        self.assertTrue(plan.allow_auto_renewal)
        self.assertEqual(plan.base_price, Decimal("49.99"))
        self.assertEqual(plan.payment_term, term)

        # Safe on_delete (SET_NULL on payment_term)
        term.delete()
        plan.refresh_from_db()
        self.assertIsNone(plan.payment_term)

    def test_plan_code_uniqueness(self):
        Plan.objects.create(name="Plan 1", code="plan-unique", price=Decimal("10.00"))
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name="Plan 2", code="plan-unique", price=Decimal("20.00"))

    def test_negative_plan_price_constraint(self):
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name="Negative Plan", code="neg-plan", price=Decimal("-10.00"))

    def test_invalid_minimum_quantity_constraint(self):
        with self.assertRaises(IntegrityError):
            Plan.objects.create(name="Zero Qty Plan", code="zero-qty", price=Decimal("10.00"), minimum_quantity=0)

    def test_invalid_plan_dates_constraint(self):
        with self.assertRaises(IntegrityError):
            Plan.objects.create(
                name="Invalid Dates Plan",
                code="invalid-dates",
                price=Decimal("10.00"),
                available_from=date(2026, 12, 31),
                available_until=date(2026, 1, 1),
            )
