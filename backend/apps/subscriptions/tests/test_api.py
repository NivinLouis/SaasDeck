from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.subscriptions.models import QuotationTemplate, QuotationTemplateLine, Subscription, SubscriptionAuditEvent
from apps.subscriptions.services import run_subscription_lifecycle


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
        send_quotation = self.client.post(reverse("subscription-send-quotation", kwargs=detail), {}, format="json")
        confirm = self.client.post(reverse("subscription-confirm", kwargs=detail), {}, format="json")
        activate = self.client.post(reverse("subscription-activate", kwargs=detail), {}, format="json")
        pause = self.client.post(reverse("subscription-pause", kwargs=detail), {}, format="json")
        resume = self.client.post(reverse("subscription-resume", kwargs=detail), {}, format="json")
        cancel = self.client.post(
            reverse("subscription-cancel", kwargs=detail), {"cancellation_reason": "No longer needed"}, format="json"
        )
        invalid_pause = self.client.post(reverse("subscription-pause", kwargs=detail), {}, format="json")

        self.assertEqual(send_quotation.data["status"], Subscription.Status.QUOTATION)
        self.assertEqual(confirm.data["status"], Subscription.Status.CONFIRMED)
        self.assertEqual(activate.status_code, status.HTTP_200_OK)
        self.assertEqual(activate.data["status"], Subscription.Status.ACTIVE)
        self.assertEqual(pause.data["status"], Subscription.Status.PAUSED)
        self.assertEqual(resume.data["status"], Subscription.Status.ACTIVE)
        self.assertEqual(cancel.data["status"], Subscription.Status.CANCELLED)
        self.assertEqual(cancel.data["cancellation_reason"], "No longer needed")
        self.assertEqual(invalid_pause.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SubscriptionAuditEvent.objects.filter(subscription__uuid=created["uuid"]).count(), 7)

    def test_staff_creates_quotation_from_template_with_snapshot_lines(self):
        template = QuotationTemplate.objects.create(name="Cloud offer", plan=self.plan, validity_days=14)
        QuotationTemplateLine.objects.create(template=template, product=self.product, quantity=3, discount_percent=Decimal("10.00"))
        self.client.force_authenticate(self.staff)

        response = self.client.post(
            reverse("quotation-template-create-quotation", kwargs={"uuid": template.uuid}),
            {"customer": self.customer.id, "start_date": "2026-02-01"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Subscription.Status.QUOTATION)
        self.assertEqual(response.data["template"], template.id)
        self.assertEqual(response.data["lines"][0]["quantity"], 3)
        self.assertEqual(response.data["lines"][0]["discount_percent"], "10.00")

    def test_draft_cannot_be_activated_without_quotation_confirmation(self):
        created = self.create_subscription()
        self.client.force_authenticate(self.staff)

        response = self.client.post(reverse("subscription-activate", kwargs={"uuid": created["uuid"]}), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def test_customer_can_request_an_available_plan(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.post(reverse("portal-plan-request"), {"plan": self.plan.id}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Subscription.Status.DRAFT)
        self.assertEqual(response.data["customer"], self.customer.id)
        self.assertEqual(response.data["plan"], self.plan.id)

    def test_archived_plan_cannot_be_used(self):
        self.plan.is_active = False
        self.plan.save(update_fields=["is_active"])
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("subscription-list"), {"customer": self.customer.id, "plan": self.plan.id}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data["fields"])

    def test_customer_can_accept_only_their_own_quotation(self):
        template = QuotationTemplate.objects.create(name="Portal offer", plan=self.plan)
        QuotationTemplateLine.objects.create(template=template, product=self.product)
        self.client.force_authenticate(self.staff)
        quotation = self.client.post(
            reverse("quotation-template-create-quotation", kwargs={"uuid": template.uuid}),
            {"customer": self.customer.id}, format="json",
        ).data
        self.client.force_authenticate(self.customer_user)

        accepted = self.client.post(reverse("portal-subscription-accept", kwargs={"uuid": quotation["uuid"]}), {}, format="json")
        hidden = self.client.post(reverse("portal-subscription-accept", kwargs={"uuid": Subscription.objects.create(subscription_number="SUB-OTHER-QUOTE", customer=self.other_customer, plan=self.plan, status=Subscription.Status.QUOTATION).uuid}), {}, format="json")

        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.data["status"], Subscription.Status.CONFIRMED)
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)

    def test_lifecycle_task_activates_completed_trials_and_closes_expired_subscriptions(self):
        trial_plan = Plan.objects.create(product=self.product, name="Trial plan", code="trial-plan", price=Decimal("99.00"), trial_period_days=7)
        trial = Subscription.objects.create(
            subscription_number="SUB-TRIAL", customer=self.customer, plan=trial_plan, status=Subscription.Status.TRIAL,
            start_date=date(2026, 1, 1), current_period_start=date(2026, 1, 1), current_period_end=date(2026, 1, 7),
        )
        expired = Subscription.objects.create(
            subscription_number="SUB-EXPIRED", customer=self.customer, plan=self.plan, status=Subscription.Status.ACTIVE,
            start_date=date(2026, 1, 1), expiry_date=date(2026, 1, 31), current_period_start=date(2026, 1, 1),
            current_period_end=date(2026, 1, 31), next_billing_date=date(2026, 2, 1),
        )

        summary = run_subscription_lifecycle(as_of=date(2026, 2, 1))
        trial.refresh_from_db()
        expired.refresh_from_db()

        self.assertEqual(summary["trials_activated"], 1)
        self.assertEqual(trial.status, Subscription.Status.ACTIVE)
        self.assertEqual(trial.current_period_start, date(2026, 1, 8))
        self.assertEqual(trial.next_billing_date, date(2026, 2, 8))
        self.assertEqual(summary["closed"], 1)
        self.assertEqual(expired.status, Subscription.Status.CLOSED)
