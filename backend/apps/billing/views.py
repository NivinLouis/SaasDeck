"""Invoice actions and billing trigger views."""

from django.http import Http404, HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import Invoice
from .services import InvoiceDocumentValidationError, render_tax_invoice_html


class TaxInvoiceHTMLView(APIView):
    """Render a final GST tax invoice as print-ready HTML."""

    permission_classes = [IsAuthenticated]

    def get_invoice(self, request, uuid):
        invoice = (
            Invoice.objects.select_related("customer")
            .prefetch_related("lines")
            .filter(uuid=uuid)
            .first()
        )
        if invoice is None:
            raise Http404
        if request.user.is_internal_staff:
            return invoice
        if request.user.is_customer and invoice.customer.user_id == request.user.id:
            return invoice
        raise Http404

    def get(self, request, uuid):
        invoice = self.get_invoice(request, uuid)
        try:
            html = render_tax_invoice_html(invoice, strict=True)
        except InvoiceDocumentValidationError as exc:
            raise ValidationError({"invoice": [str(exc)]}) from exc
        response = HttpResponse(html, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = f'inline; filename="tax-invoice-{invoice.invoice_number}.html"'
        return response
