from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Invoice
from .serializers import InvoiceSerializer
from .services import cancel_invoice, confirm_invoice


def invoice_queryset_for(user):
    queryset = Invoice.objects.select_related("customer", "subscription").prefetch_related("lines")
    if user.is_internal_staff:
        return queryset
    return queryset.filter(customer__user=user)


class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "payment_status", "currency", "customer"]
    search_fields = ["invoice_number"]
    ordering_fields = ["issue_date", "due_date", "total_amount", "created_at"]
    ordering = ["-issue_date", "-created_at"]

    def get_queryset(self):
        return invoice_queryset_for(self.request.user)


class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"

    def get_queryset(self):
        return invoice_queryset_for(self.request.user)


class InvoiceActionView(APIView):
    permission_classes = [IsAuthenticated]

    def get_invoice(self, request, uuid):
        try:
            return invoice_queryset_for(request.user).get(uuid=uuid)
        except Invoice.DoesNotExist as exc:
            raise NotFound("Invoice not found.") from exc


class InvoiceConfirmView(InvoiceActionView):
    def post(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not request.user.is_internal_staff:
            return Response({"code": "permission_denied", "message": "Only staff can confirm invoices."}, status=status.HTTP_403_FORBIDDEN)
        return Response(InvoiceSerializer(confirm_invoice(invoice.id)).data)


class InvoiceCancelView(InvoiceActionView):
    def post(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not request.user.is_internal_staff:
            return Response({"code": "permission_denied", "message": "Only staff can cancel invoices."}, status=status.HTTP_403_FORBIDDEN)
        return Response(InvoiceSerializer(cancel_invoice(invoice.id)).data)


class InvoicePdfView(InvoiceActionView):
    """Download a generated document. PDF generation is owned by the PDF feature branch."""
    def get(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not invoice.pdf_document:
            return Response(
                {"code": "pdf_not_ready", "message": "The invoice PDF has not been generated yet."},
                status=status.HTTP_409_CONFLICT,
            )
        return FileResponse(invoice.pdf_document.open("rb"), content_type="application/pdf", filename=f"{invoice.invoice_number}.pdf")
