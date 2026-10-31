from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.customers.models import Customer

User = get_user_model()


class CustomerPermissionTests(APITestCase):
    def setUp(self):
        self.password = "Correct!Pass9"
        self.customer_user = User.objects.create_user(email="customer@example.com", full_name="Customer", password=self.password)
        self.customer = Customer.objects.create(user=self.customer_user, name="Customer", email="customer@example.com")

    def test_customer_cannot_list_backoffice_customers(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.get("/api/v1/customers")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_retrieve_only_own_portal_profile(self):
        self.client.force_authenticate(self.customer_user)
        response = self.client.get("/api/v1/portal/profile")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.customer.id)
