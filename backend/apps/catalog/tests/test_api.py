from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product, ProductTax, Tax


class ProductApiTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="customer@example.com", full_name="Customer", password="SafePassword!1"
        )
        self.staff = User.objects.create_user(
            email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF
        )
        self.active_product = Product.objects.create(
            name="Pro", sku="PRO", sales_price=Decimal("99.00")
        )
        self.inactive_product = Product.objects.create(
            name="Legacy", sku="LEGACY", sales_price=Decimal("10.00"), is_active=False
        )

    def test_customer_only_sees_active_products(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(reverse("product-list"))
        detail_response = self.client.get(
            reverse("product-detail", kwargs={"pk": self.inactive_product.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "PRO")
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_can_create_product_with_taxes(self):
        tax = Tax.objects.create(name="GST", rate=Decimal("18.00"))
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            reverse("product-list"),
            {
                "name": "Business plan",
                "sku": "business-2026",
                "product_type": "service",
                "sales_price": "499.00",
                "cost_price": "99.00",
                "taxes": [tax.id],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "BUSINESS-2026")
        self.assertNotIn("cost_price", response.data)
        self.assertEqual(response.data["applied_taxes"][0]["id"], tax.id)
        self.assertTrue(ProductTax.objects.filter(product_id=response.data["id"], tax=tax).exists())

    def test_customer_cannot_create_or_archive_product(self):
        self.client.force_authenticate(self.customer)
        create_response = self.client.post(
            reverse("product-list"),
            {"name": "Nope", "sku": "NOPE", "sales_price": "1.00"},
            format="json",
        )
        archive_response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.active_product.id}),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(archive_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_archive_instead_of_deleting(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            reverse("product-detail", kwargs={"pk": self.active_product.id}),
            {"is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.active_product.refresh_from_db()
        self.assertFalse(self.active_product.is_active)
