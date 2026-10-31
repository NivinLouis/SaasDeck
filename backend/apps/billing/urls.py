from django.urls import path

from .views import TaxInvoiceHTMLView


urlpatterns = [
    path("invoices/<uuid:uuid>/tax-invoice", TaxInvoiceHTMLView.as_view(), name="tax-invoice-html"),
]
