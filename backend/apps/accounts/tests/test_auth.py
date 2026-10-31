from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from apps.customers.models import Customer

User = get_user_model()


class AuthenticationTests(APITestCase):
    password = "Correct!Pass9"

    def test_customer_registration_normalizes_email_and_assigns_customer_role(self):
        response = self.client.post("/api/v1/auth/register", {"email": "  TEST@Example.COM ", "full_name": "Test User", "password": self.password}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "customer")
        self.assertEqual(User.objects.get().email, "test@example.com")
        self.assertTrue(Customer.objects.filter(user__email="test@example.com").exists())

    def test_weak_password_returns_field_error(self):
        response = self.client.post("/api/v1/auth/register", {"email": "test@example.com", "full_name": "Test User", "password": "short"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["code"], "validation_error")
        self.assertIn("password", response.data["fields"])

    def test_only_admin_can_create_staff(self):
        staff = User.objects.create_user(email="staff@example.com", full_name="Staff User", password=self.password, role="staff")
        self.client.force_authenticate(staff)
        response = self.client.post("/api/v1/users/staff", {"email": "new@example.com", "full_name": "New Staff", "password": self.password}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
