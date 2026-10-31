"""Payment recording and refund views."""
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsStaffOrAdmin

from .models import Payment
from .serializers import PaymentSerializer
from .services import refund_payment


class PaymentQuerysetMixin:
    def get_queryset(self):
        queryset = Payment.objects.select_related("invoice", "customer", "recorded_by")
        if self.request.user.role == "customer":
            return queryset.filter(customer__user=self.request.user)
        return queryset


class PaymentListCreateView(PaymentQuerysetMixin, generics.ListCreateAPIView):
    serializer_class = PaymentSerializer
    filterset_fields = ("invoice", "customer", "payment_method", "status", "currency")
    search_fields = ("payment_number", "transaction_reference", "invoice__invoice_number", "customer__name")
    ordering_fields = ("payment_date", "amount", "created_at")
    ordering = ("-payment_date",)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsStaffOrAdmin()]
        return super().get_permissions()


class PaymentDetailView(PaymentQuerysetMixin, generics.RetrieveAPIView):
    serializer_class = PaymentSerializer
    lookup_field = "uuid"


class PaymentRefundView(PaymentQuerysetMixin, APIView):
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, uuid):
        payment = get_object_or_404(self.get_queryset(), uuid=uuid)
        refunded_payment = refund_payment(payment_id=payment.id)
        return Response(PaymentSerializer(refunded_payment).data, status=status.HTTP_200_OK)
