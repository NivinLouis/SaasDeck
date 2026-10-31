from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel
from apps.customers.models import CustomerProfile
from apps.billing.models import Invoice


class Payment(PublicUUIDModel, TimeStampedModel):
    """
    Financial transaction record associated with an Invoice.
    """
    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = "CREDIT_CARD", _("Credit / Debit Card")
        BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer / NEFT / Wire")
        UPI = "UPI", _("UPI")
        CASH = "CASH", _("Cash")
        STRIPE = "STRIPE", _("Stripe")
        RAZORPAY = "RAZORPAY", _("Razorpay")
        OTHER = "OTHER", _("Other")

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")
        REFUNDED = "REFUNDED", _("Refunded")

    payment_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Unique reference number, e.g. PAY-2026-00001")
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
        help_text=_("Target invoice this payment is credited against.")
    )
    customer = models.ForeignKey(
        CustomerProfile,
        on_delete=models.PROTECT,
        related_name="payments"
    )
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.COMPLETED,
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Amount processed in this transaction.")
    )
    currency = models.CharField(max_length=3, default="INR")
    transaction_reference = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        help_text=_("External gateway reference or bank transaction ID.")
    )
    payment_date = models.DateTimeField(default=timezone.now, db_index=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="recorded_payments"
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _("payment")
        verbose_name_plural = _("payments")
        constraints = [
            CheckConstraint(
                check=Q(amount__gt=Decimal("0.00")),
                name="chk_payment_amount_positive"
            ),
        ]
        indexes = [
            models.Index(fields=["invoice", "status"], name="idx_pay_invoice_status"),
            models.Index(fields=["customer", "status"], name="idx_pay_cust_status"),
            models.Index(fields=["payment_date", "status"], name="idx_pay_date_status"),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency} for {self.invoice.invoice_number} [{self.get_status_display()}]"
