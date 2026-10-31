from django.contrib import admin
from apps.subscriptions.models import (
    QuotationTemplate,
    QuotationTemplateLine,
    Subscription,
    SubscriptionLine,
)


class QuotationTemplateLineInline(admin.TabularInline):
    model = QuotationTemplateLine
    extra = 1
    fields = ("product", "variant", "quantity", "discount_percent")


@admin.register(QuotationTemplate)
class QuotationTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "plan", "validity_days", "is_active", "created_at")
    list_filter = ("is_active", "plan")
    search_fields = ("name",)
    inlines = [QuotationTemplateLineInline]


class SubscriptionLineInline(admin.TabularInline):
    model = SubscriptionLine
    extra = 0
    fields = ("product", "variant", "quantity", "unit_price", "tax_rule", "discount_percent")
    readonly_fields = ()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "subscription_number",
        "customer",
        "plan",
        "status",
        "current_period_start",
        "current_period_end",
        "next_billing_date",
        "auto_renew",
    )
    list_filter = ("status", "plan", "auto_renew")
    search_fields = ("subscription_number", "customer__name", "customer__email")
    inlines = [SubscriptionLineInline]
    readonly_fields = ("created_at", "updated_at")
