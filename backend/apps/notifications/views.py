"""Private in-app notification views."""
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    filterset_fields = ("category", "read_at")
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationReadView(APIView):
    def post(self, request, uuid):
        notification = get_object_or_404(Notification, uuid=uuid, recipient=request.user)
        if not notification.read_at:
            notification.read_at = now()
            notification.save(update_fields=("read_at", "updated_at"))
        return Response(NotificationSerializer(notification).data)
