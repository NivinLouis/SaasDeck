from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription


class SubscriptionApiTests(APITestCase):
    def setUp(self):
        self.customer_user = User.objects.create_user(
            email="customer@example.com", full_name="Customer", password="SafePassword!1"
        )
        self.other_customer_user = User.objects.create_user(
            email="other@example.com", full_name="Other", password="SafePassword!1"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF
        )
        self.customer = Customer.objects.create(user=self.customer_user, name="Customer", email=self.customer_user.email)
        self.other_customer = Customer.objects.create(user=self.other_customer_user, name="Other", email=self.other_customer_user.email)
        self.product = Product.objects.create(name="Cloud", sku="CLOUD", sales_price=Decimal("100.00"))
        self.plan = Plan.objects.create(product=self.product, name="Cloud Monthly", code="cloud-monthly", price=Decimal("99.00"))

    def create_subscription(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("subscription-list"),
            {"customer": self.customer.id, "plan": self.plan.id, "start_date": "2026-01-31"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data

    def test_staff_creates_draft_and_billing_dates_are_calculated(self):
        created = self.create_subscription()

        self.assertEqual(created["status"], Subscription.Status.DRAFT)
        self.assertEqual(created["current_period_start"], "2026-01-31")
        self.assertEqual(created["current_period_end"], "2026-02-27")
        self.assertEqual(created["next_billing_date"], "2026-02-28")
        self.assertTrue(created["subscription_number"].startswith("SUB-"))

    def test_customer_only_sees_own_subscriptions(self):
        created = self.create_subscription()
        Subscription.objects.create(subscription_number="SUB-OTHER", customer=self.other_customer, plan=self.plan)
        self.client.force_authenticate(self.customer_user)

        response = self.client.get(reverse("subscription-list"))
        hidden = self.client.get(reverse("subscription-detail", kwargs={"uuid": Subscription.objects.get(subscription_number="SUB-OTHER").uuid}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["uuid"], created["uuid"])
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_lifecycle_transitions_and_invalid_pause(self):
        created = self.create_subscription()
        detail = {"uuid": created["uuid"]}
        activate = self.client.post(reverse("subscription-activate", kwargs=detail), {}, format="json")
        pause = self.client.post(reverse("subscription-pause", kwargs=detail), {}, format="json")
        resume = self.client.post(reverse("subscription-resume", kwargs=detail), {}, format="json")
        cancel = self.client.post(
            reverse("subscription-cancel", kwargs=detail), {"cancellation_reason": "No longer needed"}, format="json"
        )
        invalid_pause = self.client.post(reverse("subscription-pause", kwargs=detail), {}, format="json")

        self.assertEqual(activate.status_code, status.HTTP_200_OK)
        self.assertEqual(activate.data["status"], Subscription.Status.ACTIVE)
        self.assertEqual(pause.data["status"], Subscription.Status.PAUSED)
        self.assertEqual(resume.data["status"], Subscription.Status.ACTIVE)
        self.assertEqual(cancel.data["status"], Subscription.Status.CANCELLED)
        self.assertEqual(cancel.data["cancellation_reason"], "No longer needed")
        self.assertEqual(invalid_pause.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_create_or_change_lifecycle(self):
        self.client.force_authenticate(self.customer_user)
        create = self.client.post(
            reverse("subscription-list"), {"customer": self.customer.id, "plan": self.plan.id}, format="json"
        )
        sub = Subscription.objects.create(subscription_number="SUB-CUSTOMER", customer=self.customer, plan=self.plan)
        activate = self.client.post(
            reverse("subscription-activate", kwargs={"uuid": sub.uuid}), {}, format="json"
        )

        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(activate.status_code, status.HTTP_403_FORBIDDEN)

    def test_archived_plan_cannot_be_used(self):
        self.plan.is_active = False
        self.plan.save(update_fields=["is_active"])
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("subscription-list"), {"customer": self.customer.id, "plan": self.plan.id}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data["fields"])
