"""Notification log serializers."""
from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("uuid", "title", "body", "category", "read_at", "created_at")
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ("email_overdue_reminders", "in_app_overdue_reminders")
