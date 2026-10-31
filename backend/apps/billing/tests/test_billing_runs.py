from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import BillingRun, Invoice
from apps.catalog.models import Product
from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription


class BillingRunApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com", full_name="Admin", password="SafePassword!1", role=User.Role.ADMIN
        )
        customer_user = User.objects.create_user(
            email="customer@example.com", full_name="Customer", password="SafePassword!1"
        )
        self.customer = Customer.objects.create(user=customer_user, name="Customer", email=customer_user.email)
        product = Product.objects.create(name="Cloud", sku="CLOUD", sales_price=Decimal("100.00"))
        plan = Plan.objects.create(product=product, name="Cloud Monthly", code="cloud-monthly", price=Decimal("100.00"))
        today = localdate()
        self.subscription = Subscription.objects.create(
            subscription_number="SUB-BILLING-001",
            customer=self.customer,
            plan=plan,
            status=Subscription.Status.ACTIVE,
            start_date=today - timedelta(days=31),
            current_period_start=today - timedelta(days=31),
            current_period_end=today - timedelta(days=1),
            next_billing_date=today,
        )

    def test_admin_run_creates_invoice_and_advances_subscription(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(reverse("billing-run-trigger"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], BillingRun.Status.COMPLETED)
        self.assertEqual(response.data["invoices_created"], 1)
        self.assertEqual(Invoice.objects.filter(subscription=self.subscription).count(), 1)
        self.subscription.refresh_from_db()
        self.assertGreater(self.subscription.next_billing_date, localdate())

    def test_second_run_is_idempotent_after_the_subscription_advances(self):
        self.client.force_authenticate(self.admin)
        self.client.post(reverse("billing-run-trigger"), {}, format="json")

        response = self.client.post(reverse("billing-run-trigger"), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["invoices_created"], 0)
        self.assertEqual(Invoice.objects.filter(subscription=self.subscription).count(), 1)

    def test_runs_are_admin_only_and_expose_failures_in_detail(self):
        response = self.client.post(reverse("billing-run-trigger"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.admin)
        created = self.client.post(reverse("billing-run-trigger"), {}, format="json")
        listed = self.client.get(reverse("billing-run-list"))
        detail = self.client.get(reverse("billing-run-detail", kwargs={"uuid": created.data["uuid"]}))

        self.assertEqual(listed.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertIn("failures", detail.data)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_confirmed_invoice_can_be_emailed_with_a_pdf(self):
        invoice = Invoice.objects.create(
            invoice_number="INV-EMAIL-001",
            customer=self.customer,
            status=Invoice.Status.CONFIRMED,
            issue_date=localdate(),
            due_date=localdate(),
            total_amount=Decimal("100.00"),
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(reverse("invoice-send", kwargs={"uuid": invoice.uuid}), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertIsNotNone(invoice.email_sent_at)
        self.assertTrue(invoice.pdf_document)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.customer.email])
