from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.catalog.models import Product


class DiscountRuleApiTests(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user(email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF)
        self.customer = User.objects.create_user(email="customer@example.com", full_name="Customer", password="SafePassword!1")
        self.product = Product.objects.create(name="Pro", sku="PRO", sales_price=Decimal("100.00"))

    def test_staff_manages_discount_and_customer_is_forbidden(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post("/api/v1/discounts", {"code": "launch20", "name": "Launch", "discount_type": "PERCENTAGE", "value": "20.00", "scope": "PRODUCTS", "applicable_products": [self.product.id]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["code"], "LAUNCH20")
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.get("/api/v1/discounts").status_code, status.HTTP_403_FORBIDDEN)
