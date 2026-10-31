from django.urls import path
from .views import DashboardSummaryView, InvoiceReportExportView

urlpatterns = [
    path("reports/dashboard", DashboardSummaryView.as_view(), name="reports-dashboard"),
    path("reports/invoices.csv", InvoiceReportExportView.as_view(), name="reports-invoices-export"),
]
