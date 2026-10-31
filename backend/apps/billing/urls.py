from django.urls import path

from .views import (
    BillingRunDetailView, BillingRunListView, BillingRunTriggerView,
    InvoiceCancelView, InvoiceConfirmView, InvoiceDetailView, InvoiceListView,
    InvoicePdfView, InvoiceSendView, TaxInvoiceHTMLView,
)

urlpatterns = [
    path("invoices", InvoiceListView.as_view(), name="invoice-list"),
    path("invoices/<uuid:uuid>", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:uuid>/confirm", InvoiceConfirmView.as_view(), name="invoice-confirm"),
    path("invoices/<uuid:uuid>/cancel", InvoiceCancelView.as_view(), name="invoice-cancel"),
    path("invoices/<uuid:uuid>/send", InvoiceSendView.as_view(), name="invoice-send"),
    path("invoices/<uuid:uuid>/pdf", InvoicePdfView.as_view(), name="invoice-pdf"),
    path("invoices/<uuid:uuid>/tax-invoice", TaxInvoiceHTMLView.as_view(), name="tax-invoice-html"),
    path("billing/run", BillingRunTriggerView.as_view(), name="billing-run-trigger"),
    path("billing/runs", BillingRunListView.as_view(), name="billing-run-list"),
    path("billing/runs/<uuid:uuid>", BillingRunDetailView.as_view(), name="billing-run-detail"),
]
