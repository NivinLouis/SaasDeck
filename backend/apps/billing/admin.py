"""Django admin registrations for billing models."""

from django.contrib import admin

from .models import Invoice, InvoiceLine


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0
    readonly_fields = ("line_total",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer", "issue_date", "total_amount", "currency", "status", "payment_status")
    list_filter = ("status", "payment_status", "currency", "issue_date")
    search_fields = ("invoice_number", "customer__name", "customer__company", "supplier_gstin", "recipient_gstin")
    readonly_fields = ("uuid", "created_at", "updated_at", "amount_due")
    inlines = (InvoiceLineInline,)


@admin.register(InvoiceLine)
class InvoiceLineAdmin(admin.ModelAdmin):
    list_display = ("invoice", "description", "hsn_sac", "quantity", "unit", "line_total")
    search_fields = ("invoice__invoice_number", "description", "hsn_sac")
