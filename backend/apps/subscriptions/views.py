"""Subscription views delegate business mutations to services.py."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffOrAdmin

from .models import Subscription
from .serializers import CancelSubscriptionSerializer, SubscriptionSerializer
from .services import transition_subscription


class SubscriptionQuerysetMixin:
    def get_queryset(self):
        queryset = Subscription.objects.select_related("customer", "plan", "plan__product", "plan__payment_term")
        if self.request.user.role == "customer":
            return queryset.filter(customer__user=self.request.user)
        return queryset


class SubscriptionListCreateView(SubscriptionQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    filterset_fields = ("customer", "plan", "status", "auto_renew")
    search_fields = ("subscription_number", "customer__name", "customer__email", "plan__name")
    ordering_fields = ("created_at", "start_date", "next_billing_date", "status")
    ordering = ("-created_at",)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class SubscriptionDetailView(SubscriptionQuerysetMixin, generics.RetrieveUpdateAPIView):
    serializer_class = SubscriptionSerializer
    lookup_field = "uuid"

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH"}:
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class SubscriptionActionView(SubscriptionQuerysetMixin, APIView):
    permission_classes = [IsStaffOrAdmin]
    action = ""

    def post(self, request, uuid):
        subscription = get_object_or_404(self.get_queryset(), uuid=uuid)
        cancellation_reason = ""
        if self.action == "cancel":
            serializer = CancelSubscriptionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            cancellation_reason = serializer.validated_data.get("cancellation_reason", "")
        updated = transition_subscription(
            subscription_id=subscription.id,
            action=self.action,
            cancellation_reason=cancellation_reason,
        )
        return Response(SubscriptionSerializer(updated).data, status=status.HTTP_200_OK)


class ActivateSubscriptionView(SubscriptionActionView):
    action = "activate"


class PauseSubscriptionView(SubscriptionActionView):
    action = "pause"


class ResumeSubscriptionView(SubscriptionActionView):
    action = "resume"


class CancelSubscriptionView(SubscriptionActionView):
    action = "cancel"
