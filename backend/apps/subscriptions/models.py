from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel
from apps.customers.models import Customer
from apps.plans.models import Plan
from apps.catalog.models import Product, ProductVariant, TaxRule
from apps.discounts.models import DiscountRule


class QuotationTemplate(PublicUUIDModel, TimeStampedModel):
    """
    Reusable preset template containing a predefined plan and line items.
    Used to quickly generate customer quotations.
    """
    name = models.CharField(max_length=255, unique=True)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="quotation_templates")
    validity_days = models.PositiveIntegerField(
        default=30,
        help_text=_("Number of days generated quotations remain valid.")
    )
    terms_and_conditions = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = _("quotation template")
        verbose_name_plural = _("quotation templates")

    def __str__(self):
        return self.name


class QuotationTemplateLine(TimeStampedModel):
    """
    Line items bundled inside a Quotation Template.
    """
    template = models.ForeignKey(
        QuotationTemplate,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        verbose_name = _("quotation template line")
        verbose_name_plural = _("quotation template lines")


class Subscription(PublicUUIDModel, TimeStampedModel):
    """
    Core Subscription entity tracking the lifecycle from quotation to active recurring billing.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        QUOTATION = "QUOTATION", _("Quotation Sent")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        ACTIVE = "ACTIVE", _("Active")
        PAUSED = "PAUSED", _("Paused")
        CLOSED = "CLOSED", _("Closed")

    subscription_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Unique human-readable reference, e.g. SUB-2026-0001")
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        help_text=_("Customer who owns this subscription.")
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    template = models.ForeignKey(
        QuotationTemplate,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subscriptions",
        help_text=_("Originating quotation template if created from one.")
    )
    applied_discount = models.ForeignKey(
        DiscountRule,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subscriptions"
    )

    start_date = models.DateField(blank=True, null=True, help_text=_("Date subscription officially started."))
    expiry_date = models.DateField(blank=True, null=True, help_text=_("Overall contract expiry or renewal target date."))

    # Recurring Billing Schedule Markers
    current_period_start = models.DateField(blank=True, null=True, help_text=_("Start of current billing cycle."))
    current_period_end = models.DateField(blank=True, null=True, help_text=_("End of current billing cycle."))
    next_billing_date = models.DateField(blank=True, null=True, db_index=True, help_text=_("Target date to trigger next invoice."))

    payment_terms = models.CharField(
        max_length=100,
        default="Immediate Payment",
        help_text=_("Payment terms e.g. Net 15, Net 30, Immediate")
    )
    auto_renew = models.BooleanField(default=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_subscriptions"
    )

    class Meta:
        verbose_name = _("subscription")
        verbose_name_plural = _("subscriptions")
        indexes = [
            models.Index(fields=["customer", "status"], name="idx_sub_cust_status"),
            models.Index(fields=["status", "next_billing_date"], name="idx_sub_status_next_bill"),
            models.Index(fields=["current_period_end"], name="idx_sub_period_end"),
        ]
        constraints = [
            CheckConstraint(
                check=Q(expiry_date__isnull=True) | Q(start_date__isnull=True) | Q(expiry_date__gte=models.F("start_date")),
                name="chk_sub_expiry_gte_start"
            ),
        ]

    def __str__(self):
        return f"{self.subscription_number} - {self.customer} [{self.get_status_display()}]"


class SubscriptionLine(TimeStampedModel):
    """
    Individual product line items attached to a subscription.
    """
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="subscription_lines"
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="subscription_lines"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Base unit price snapshot at time of line creation.")
    )
    tax_rule = models.ForeignKey(
        TaxRule,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    class Meta:
        verbose_name = _("subscription line")
        verbose_name_plural = _("subscription lines")
        constraints = [
            CheckConstraint(
                check=Q(quantity__gte=1),
                name="chk_sub_line_qty_gte_1"
            ),
            CheckConstraint(
                check=Q(unit_price__gte=Decimal("0.00")),
                name="chk_sub_line_unit_price_positive"
            ),
        ]

    def __str__(self):
        return f"{self.subscription.subscription_number}: {self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        gross = self.unit_price * self.quantity
        if self.discount_percent > Decimal("0.00"):
            discount = gross * (self.discount_percent / Decimal("100.00"))
            return gross - discount
        return gross
