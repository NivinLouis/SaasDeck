from django.contrib import admin
from apps.plans.models import Plan, PaymentTerm


@admin.register(PaymentTerm)
class PaymentTermAdmin(admin.ModelAdmin):
    list_display = ("name", "days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "billing_interval", "price", "minimum_quantity", "payment_term", "is_active")
    list_filter = ("billing_interval", "is_active")
    search_fields = ("name", "code")
