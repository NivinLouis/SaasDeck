from datetime import timedelta
from decimal import Decimal

from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import Invoice
from apps.customers.models import Customer
from apps.notifications.models import Notification
from apps.notifications.tasks import send_overdue_reminders


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="customer@example.com", full_name="Customer", password="SafePassword!1")
        self.customer = Customer.objects.create(user=self.user, name="Customer", email=self.user.email)

    def test_customer_can_save_reminder_preferences(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(reverse("notification-preferences"), {"email_overdue_reminders": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["email_overdue_reminders"])

    def test_task_sends_one_reminder_and_creates_notification(self):
        today = timezone.localdate()
        invoice = Invoice.objects.create(
            invoice_number="INV-REMINDER", customer=self.customer, status=Invoice.Status.CONFIRMED,
            issue_date=today - timedelta(days=2), due_date=today - timedelta(days=1),
            total_amount=Decimal("100.00"), amount_paid=Decimal("0.00"), payment_status=Invoice.PaymentStatus.UNPAID,
        )
        self.assertEqual(send_overdue_reminders(), {"sent": 1})
        invoice.refresh_from_db()
        self.assertIsNotNone(invoice.overdue_reminder_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(Notification.objects.filter(recipient=self.user, category="overdue_invoice").exists())
        self.assertEqual(send_overdue_reminders(), {"sent": 0})
