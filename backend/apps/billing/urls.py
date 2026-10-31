from django.urls import path

from .views import InvoiceCancelView, InvoiceConfirmView, InvoiceDetailView, InvoiceListView, InvoicePdfView

urlpatterns = [
    path("invoices", InvoiceListView.as_view(), name="invoice-list"),
    path("invoices/<uuid:uuid>", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoices/<uuid:uuid>/confirm", InvoiceConfirmView.as_view(), name="invoice-confirm"),
    path("invoices/<uuid:uuid>/cancel", InvoiceCancelView.as_view(), name="invoice-cancel"),
    path("invoices/<uuid:uuid>/pdf", InvoicePdfView.as_view(), name="invoice-pdf"),
]
