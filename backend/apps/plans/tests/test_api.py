from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils.timezone import localdate
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product
from apps.plans.models import Plan


class PlanApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com", full_name="Customer", password="SafePassword!1"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF
        )
        self.product = Product.objects.create(name="Cloud", sku="CLOUD", sales_price=Decimal("100.00"))
        self.active_plan = Plan.objects.create(
            product=self.product, name="Cloud Monthly", code="cloud-monthly", price=Decimal("99.00"), is_public=True,
        )
        self.archived_plan = Plan.objects.create(
            product=self.product, name="Legacy", code="legacy", price=Decimal("10.00"), is_active=False
        )

    def test_customer_only_sees_available_active_plans(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("plan-list"))
        archived_detail = self.client.get(reverse("plan-detail", kwargs={"pk": self.archived_plan.id}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["code"], "cloud-monthly")
        self.assertEqual(archived_detail.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_showcase_only_lists_available_active_plans(self):
        response = self.client.get(reverse("public-plan-showcase"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["code"], "cloud-monthly")

    def test_staff_can_create_a_product_linked_plan(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("plan-list"),
            {
                "product": self.product.id,
                "name": "Cloud Annual",
                "code": "CLOUD-ANNUAL",
                "price": "999.00",
                "currency": "inr",
                "billing_interval": "yearly",
                "trial_period_days": 14,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "cloud-annual")
        self.assertEqual(response.data["currency"], "INR")
        self.assertEqual(response.data["product_detail"]["sku"], "CLOUD")

    def test_customer_cannot_create_or_archive_plan(self):
        self.client.force_authenticate(self.customer)
        create_response = self.client.post(
            reverse("plan-list"),
            {"product": self.product.id, "name": "Nope", "code": "nope", "price": "1.00"},
            format="json",
        )
        archive_response = self.client.patch(
            reverse("plan-detail", kwargs={"pk": self.active_plan.id}),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(archive_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_archive_plan(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            reverse("plan-detail", kwargs={"pk": self.active_plan.id}),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_plan.refresh_from_db()
        self.assertFalse(self.active_plan.is_active)

    def test_invalid_availability_dates_are_rejected(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("plan-list"),
            {
                "product": self.product.id,
                "name": "Invalid availability",
                "code": "invalid-availability",
                "price": "10.00",
                "available_from": localdate().isoformat(),
                "available_until": (localdate() - timedelta(days=1)).isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available_until", response.data["fields"])
