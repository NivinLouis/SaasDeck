"""Subscription views delegate business mutations to services.py."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsCustomer, IsStaffOrAdmin

from .models import QuotationTemplate, Subscription
from .serializers import CancelSubscriptionSerializer, QuotationFromTemplateSerializer, QuotationTemplateSerializer, SubscriptionSerializer
from .services import run_subscription_lifecycle, transition_subscription


class SubscriptionQuerysetMixin:
    def get_queryset(self):
        queryset = Subscription.objects.select_related(
            "customer", "plan", "plan__product", "plan__payment_term", "template"
        ).prefetch_related("lines__product", "lines__variant")
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


class QuotationTemplateListCreateView(generics.ListCreateAPIView):
    serializer_class = QuotationTemplateSerializer
    permission_classes = [IsStaffOrAdmin]
    queryset = QuotationTemplate.objects.select_related("plan").prefetch_related("lines__product", "lines__variant")
    filterset_fields = ("plan", "is_active")
    search_fields = ("name", "plan__name")
    ordering_fields = ("name", "validity_days", "created_at")
    ordering = ("name",)


class QuotationTemplateDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = QuotationTemplateSerializer
    permission_classes = [IsStaffOrAdmin]
    lookup_field = "uuid"
    queryset = QuotationTemplate.objects.select_related("plan").prefetch_related("lines__product", "lines__variant")


class CreateQuotationFromTemplateView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, uuid):
        template = get_object_or_404(
            QuotationTemplate.objects.select_related("plan", "plan__product", "plan__payment_term").prefetch_related(
                "lines__product__product_taxes__tax", "lines__variant"
            ),
            uuid=uuid,
        )
        serializer = QuotationFromTemplateSerializer(data=request.data, context={"request": request, "template": template})
        serializer.is_valid(raise_exception=True)
        quotation = serializer.save()
        return Response(SubscriptionSerializer(quotation).data, status=status.HTTP_201_CREATED)


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


class CustomerSubscriptionActionView(SubscriptionQuerysetMixin, APIView):
    """Customer self-service actions scoped to the authenticated customer's records."""

    permission_classes = [IsCustomer]
    action = ""

    def post(self, request, uuid):
        subscription = get_object_or_404(self.get_queryset(), uuid=uuid)
        cancellation_reason = request.data.get("cancellation_reason", "") if self.action == "cancel" else ""
        updated = transition_subscription(
            subscription_id=subscription.id,
            action=self.action,
            cancellation_reason=cancellation_reason,
            customer_initiated=True,
        )
        return Response(SubscriptionSerializer(updated).data, status=status.HTTP_200_OK)


class SubscriptionLifecycleRunView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request):
        return Response(run_subscription_lifecycle())


class ActivateSubscriptionView(SubscriptionActionView):
    action = "activate"


class SendQuotationView(SubscriptionActionView):
    action = "send_quotation"


class ConfirmSubscriptionView(SubscriptionActionView):
    action = "confirm"


class PauseSubscriptionView(SubscriptionActionView):
    action = "pause"


class ResumeSubscriptionView(SubscriptionActionView):
    action = "resume"


class CancelSubscriptionView(SubscriptionActionView):
    action = "cancel"


class CustomerAcceptQuotationView(CustomerSubscriptionActionView):
    action = "confirm"


class CustomerPauseSubscriptionView(CustomerSubscriptionActionView):
    action = "pause"


class CustomerResumeSubscriptionView(CustomerSubscriptionActionView):
    action = "resume"


class CustomerCancelSubscriptionView(CustomerSubscriptionActionView):
    action = "cancel"
