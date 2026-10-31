"""In-app notification delivery log."""
from django.conf import settings
from django.db import models

from apps.core.models import PublicUUIDModel, TimeStampedModel


class Notification(PublicUUIDModel, TimeStampedModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    category = models.CharField(max_length=32, default="system")
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("recipient", "read_at"), name="notif_recipient_read")]
