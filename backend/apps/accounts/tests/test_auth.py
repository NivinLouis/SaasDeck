from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
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

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", FRONTEND_URL="http://frontend.test")
    def test_password_reset_request_and_confirmation(self):
        user = User.objects.create_user(email="reset@example.com", full_name="Reset User", password=self.password)

        requested = self.client.post("/api/v1/auth/password/reset/request", {"email": user.email}, format="json")
        confirmed = self.client.post("/api/v1/auth/password/reset/confirm", {
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": default_token_generator.make_token(user),
            "new_password": "NewCorrect!Pass9",
        }, format="json")

        self.assertEqual(requested.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://frontend.test/reset-password", mail.outbox[0].body)
        self.assertEqual(confirmed.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewCorrect!Pass9"))
