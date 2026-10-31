"""Invoice API and GST tax-invoice HTML view."""

from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsAdmin

from .models import BillingRun, Invoice
from .serializers import BillingRunRequestSerializer, BillingRunSerializer, InvoiceCreateSerializer, InvoiceSerializer
from .services import (
    InvoiceDocumentValidationError,
    cancel_invoice,
    confirm_invoice,
    render_tax_invoice_html,
    run_recurring_billing,
    send_invoice_email,
)
from .tasks import generate_invoice_pdf_task, send_invoice_email_task


def invoice_queryset_for(user):
    queryset = Invoice.objects.select_related("customer", "subscription").prefetch_related("lines")
    return queryset if user.is_internal_staff else queryset.filter(customer__user=user)


class InvoiceListView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "payment_status", "currency", "customer"]
    search_fields = ["invoice_number"]
    ordering_fields = ["issue_date", "due_date", "total_amount", "created_at"]
    ordering = ["-issue_date", "-created_at"]

    def get_queryset(self):
        return invoice_queryset_for(self.request.user)

    def get_permissions(self):
        if self.request.method == "POST":
            from apps.core.permissions import IsStaffOrAdmin
            return [IsStaffOrAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        return InvoiceCreateSerializer if self.request.method == "POST" else InvoiceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        return Response(InvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


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
        confirmed = confirm_invoice(invoice.id)
        if settings.INVOICE_PDF_ASYNC:
            generate_invoice_pdf_task.delay(confirmed.id)
        else:
            generate_invoice_pdf_task(confirmed.id)
        confirmed.refresh_from_db()
        return Response(InvoiceSerializer(confirmed).data)


class InvoiceCancelView(InvoiceActionView):
    def post(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not request.user.is_internal_staff:
            return Response({"code": "permission_denied", "message": "Only staff can cancel invoices."}, status=status.HTTP_403_FORBIDDEN)
        return Response(InvoiceSerializer(cancel_invoice(invoice.id)).data)


class InvoicePdfView(InvoiceActionView):
    def get(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not invoice.pdf_document:
            return Response({"code": "pdf_not_ready", "message": "The invoice PDF has not been generated yet."}, status=status.HTTP_409_CONFLICT)
        return FileResponse(invoice.pdf_document.open("rb"), content_type="application/pdf", filename=f"{invoice.invoice_number}.pdf")


class InvoiceSendView(InvoiceActionView):
    """Send a confirmed invoice to its customer's billing address."""

    def post(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        if not request.user.is_internal_staff:
            return Response({"code": "permission_denied", "message": "Only staff can send invoices."}, status=status.HTTP_403_FORBIDDEN)
        if invoice.status not in {Invoice.Status.CONFIRMED, Invoice.Status.PAID}:
            raise ValidationError("Only confirmed or paid invoices can be sent.")
        if not invoice.customer.email:
            raise ValidationError({"invoice": "The invoice customer does not have an email address."})
        if settings.INVOICE_EMAIL_ASYNC:
            send_invoice_email_task.delay(invoice.id)
            return Response({"message": "Invoice email has been queued."}, status=status.HTTP_202_ACCEPTED)
        return Response(InvoiceSerializer(send_invoice_email(invoice.id)).data)


class TaxInvoiceHTMLView(InvoiceActionView):
    """Render a final GST tax invoice as print-ready HTML for a PDF worker."""

    def get(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        try:
            html = render_tax_invoice_html(invoice, strict=True)
        except InvoiceDocumentValidationError as exc:
            raise ValidationError({"invoice": [str(exc)]}) from exc
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = f'inline; filename="tax-invoice-{invoice.invoice_number}.html"'
        return response


class BillingRunTriggerView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = BillingRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        billing_run = run_recurring_billing(
            run_date=serializer.validated_data.get("run_date"),
            triggered_by=request.user,
        )
        return Response(BillingRunSerializer(billing_run).data, status=status.HTTP_201_CREATED)


class BillingRunListView(generics.ListAPIView):
    serializer_class = BillingRunSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ("status", "run_date")
    ordering_fields = ("run_date", "created_at", "finished_at", "status")
    ordering = ("-created_at",)
    queryset = BillingRun.objects.select_related("triggered_by")


class BillingRunDetailView(generics.RetrieveAPIView):
    serializer_class = BillingRunSerializer
    permission_classes = [IsAdmin]
    lookup_field = "uuid"
    queryset = BillingRun.objects.select_related("triggered_by")
