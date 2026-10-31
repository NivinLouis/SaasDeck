from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class TaxApiTests(APITestCase):
    def test_staff_can_create_tax(self):
        staff = User.objects.create_user(email="staff@example.com", full_name="Staff", password="SafePassword!1", role=User.Role.STAFF)
        self.client.force_authenticate(staff)
        response = self.client.post("/api/v1/taxes", {"name": "GST 18%", "rate": str(Decimal("18.00"))}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
