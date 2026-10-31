from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel
from apps.customers.models import CustomerProfile
from apps.subscriptions.models import Subscription
from apps.catalog.models import Product, TaxRule


class Invoice(PublicUUIDModel, TimeStampedModel):
    """
    Invoice entity with immutable monetary snapshots and idempotent recurring billing protection.
    """
    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        PAID = "PAID", _("Paid")
        CANCELLED = "CANCELLED", _("Cancelled")

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", _("Unpaid")
        PARTIAL = "PARTIALLY_PAID", _("Partially Paid")
        PAID = "PAID", _("Fully Paid")

    invoice_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Unique sequential invoice code, e.g. INV-2026-00001")
    )
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.PROTECT,
        related_name="invoices",
        help_text=_("Billing recipient.")
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="invoices",
        help_text=_("Originating subscription if generated from recurring billing.")
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        db_index=True
    )

    # Billing Period Boundaries for Recurring Subscriptions
    billing_period_start = models.DateField(blank=True, null=True)
    billing_period_end = models.DateField(blank=True, null=True)

    issue_date = models.DateField(default=timezone.now, db_index=True)
    due_date = models.DateField(db_index=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    # Monetary Snapshots (never modified by catalog updates)
    subtotal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    currency = models.CharField(max_length=3, default="INR")
    payment_terms = models.CharField(max_length=100, default="Immediate")
    pdf_document = models.FileField(upload_to="invoices/%Y/%m/", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        constraints = [
            # IDEMPOTENCY: Guarantees no two invoices exist for the exact same subscription billing cycle
            UniqueConstraint(
                fields=["subscription", "billing_period_start", "billing_period_end"],
                condition=Q(subscription__isnull=False) & ~Q(status="CANCELLED"),
                name="unique_active_subscription_billing_period"
            ),
            CheckConstraint(
                check=Q(due_date__gte=models.F("issue_date")),
                name="chk_invoice_due_date_gte_issue_date"
            ),
            CheckConstraint(
                check=Q(total_amount__gte=Decimal("0.00")),
                name="chk_invoice_total_positive"
            ),
            CheckConstraint(
                check=Q(amount_paid__gte=Decimal("0.00")),
                name="chk_invoice_amount_paid_positive"
            ),
        ]
        indexes = [
            models.Index(fields=["customer", "status"], name="idx_inv_cust_status"),
            models.Index(fields=["status", "due_date"], name="idx_inv_status_due_date"),
            models.Index(fields=["payment_status", "due_date"], name="idx_inv_paystatus_due_date"),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer} ({self.total_amount} {self.currency})"

    @property
    def amount_due(self):
        return max(Decimal("0.00"), self.total_amount - self.amount_paid)

    @property
    def is_overdue(self):
        return (
            self.payment_status != self.PaymentStatus.PAID
            and self.status != self.Status.CANCELLED
            and self.due_date < timezone.now().date()
        )


class InvoiceLine(TimeStampedModel):
    """
    Immutable line item snapshot copied onto the invoice.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="invoice_lines"
    )
    description = models.CharField(max_length=255, help_text=_("Snapshot item name and variant attributes."))
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Historical snapshot price.")
    )
    tax_rule = models.ForeignKey(
        TaxRule,
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    tax_rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Net line total = (quantity * unit_price) - discount_amount + tax_amount")
    )

    class Meta:
        verbose_name = _("invoice line")
        verbose_name_plural = _("invoice lines")
        constraints = [
            CheckConstraint(
                check=Q(quantity__gte=1),
                name="chk_inv_line_qty_gte_1"
            ),
            CheckConstraint(
                check=Q(unit_price__gte=Decimal("0.00")),
                name="chk_inv_line_unit_price_positive"
            ),
            CheckConstraint(
                check=Q(line_total__gte=Decimal("0.00")),
                name="chk_inv_line_total_positive"
            ),
        ]

    def __str__(self):
        return f"{self.invoice.invoice_number}: {self.description} ({self.quantity} x {self.unit_price})"
