"""Dashboard views backed by aggregate queries."""
import csv
from decimal import Decimal

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.core.permissions import IsStaffOrAdmin
from apps.subscriptions.models import Subscription
from .serializers import ReportFilterSerializer


class DashboardSummaryView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        filters = ReportFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        start_date = filters.validated_data.get("start_date")
        end_date = filters.validated_data.get("end_date")
        invoices = Invoice.objects.exclude(status=Invoice.Status.CANCELLED)
        if start_date:
            invoices = invoices.filter(issue_date__gte=start_date)
        if end_date:
            invoices = invoices.filter(issue_date__lte=end_date)
        statuses = {row["status"]: row["count"] for row in Subscription.objects.values("status").annotate(count=Count("id"))}
        outstanding = invoices.aggregate(value=Sum(F("total_amount") - F("amount_paid")))["value"] or Decimal("0.00")
        paid = invoices.aggregate(value=Sum("amount_paid"))["value"] or Decimal("0.00")
        overdue_count = invoices.filter(
            due_date__lt=timezone.localdate(),
        ).exclude(payment_status=Invoice.PaymentStatus.PAID).count()
        trend = list(invoices.annotate(month=TruncMonth("issue_date")).values("month").annotate(
            invoiced_total=Sum("total_amount"), paid_total=Sum("amount_paid"), invoice_count=Count("id"),
        ).order_by("month"))
        return Response({
            "filters": {"start_date": start_date, "end_date": end_date},
            "subscriptions": {"total": Subscription.objects.count(), "by_status": statuses},
            "invoices": {"total": invoices.count(), "paid_total": paid, "outstanding_total": outstanding, "overdue_count": overdue_count},
            "trend": trend,
        })


class InvoiceReportExportView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        filters = ReportFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        invoices = Invoice.objects.exclude(status=Invoice.Status.CANCELLED).select_related("customer")
        if filters.validated_data.get("start_date"):
            invoices = invoices.filter(issue_date__gte=filters.validated_data["start_date"])
        if filters.validated_data.get("end_date"):
            invoices = invoices.filter(issue_date__lte=filters.validated_data["end_date"])
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="invoice-report.csv"'
        writer = csv.writer(response)
        writer.writerow(("Invoice", "Customer", "Issue date", "Due date", "Status", "Payment status", "Currency", "Total", "Paid", "Outstanding"))
        for invoice in invoices.order_by("issue_date", "invoice_number"):
            writer.writerow((invoice.invoice_number, invoice.customer.name, invoice.issue_date, invoice.due_date, invoice.status, invoice.payment_status, invoice.currency, invoice.total_amount, invoice.amount_paid, invoice.amount_due))
        return response
