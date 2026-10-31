"""Dashboard views backed by aggregate queries."""
from decimal import Decimal

from django.db.models import Count, F, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Invoice
from apps.core.permissions import IsStaffOrAdmin
from apps.subscriptions.models import Subscription


class DashboardSummaryView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        invoices = Invoice.objects.exclude(status=Invoice.Status.CANCELLED)
        statuses = {row["status"]: row["count"] for row in Subscription.objects.values("status").annotate(count=Count("id"))}
        outstanding = invoices.aggregate(value=Sum(F("total_amount") - F("amount_paid")))["value"] or Decimal("0.00")
        paid = invoices.aggregate(value=Sum("amount_paid"))["value"] or Decimal("0.00")
        return Response({"subscriptions": {"total": Subscription.objects.count(), "by_status": statuses}, "invoices": {"total": invoices.count(), "paid_total": paid, "outstanding_total": outstanding, "overdue_count": sum(1 for invoice in invoices if invoice.is_overdue)}})
