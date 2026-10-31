from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel
from apps.catalog.models import Product
from apps.plans.models import Plan


class DiscountRule(PublicUUIDModel, TimeStampedModel):
    """
    Promotional discounts and coupons applied to subscriptions and invoices.
    """
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", _("Percentage")
        FIXED_AMOUNT = "FIXED_AMOUNT", _("Fixed Amount")

    class Scope(models.TextChoices):
        WHOLE_SUBSCRIPTION = "SUBSCRIPTION", _("Entire Subscription")
        SPECIFIC_PRODUCTS = "PRODUCTS", _("Specific Products")
        SPECIFIC_PLANS = "PLANS", _("Specific Plans")

    code = models.CharField(max_length=50, unique=True, db_index=True, help_text=_("Coupon or promo code, e.g. HACKATHON2024"))
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text=_("Percentage (e.g. 15.00) or Fixed Amount (e.g. 500.00)")
    )
    scope = models.CharField(
        max_length=20,
        choices=Scope.choices,
        default=Scope.WHOLE_SUBSCRIPTION
    )

    minimum_purchase_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Minimum order / subtotal amount required to activate discount.")
    )
    minimum_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Minimum units or seats required.")
    )

    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(blank=True, null=True)

    max_uses = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text=_("Maximum total redemptions permitted across all customers. Null = unlimited.")
    )
    times_used = models.PositiveIntegerField(
        default=0,
        help_text=_("Count of times this discount has been redeemed.")
    )
    is_active = models.BooleanField(default=True, db_index=True)

    applicable_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="discount_rules",
        help_text=_("Products eligible when scope is SPECIFIC_PRODUCTS.")
    )
    applicable_plans = models.ManyToManyField(
        Plan,
        blank=True,
        related_name="discount_rules",
        help_text=_("Plans eligible when scope is SPECIFIC_PLANS.")
    )

    class Meta:
        verbose_name = _("discount rule")
        verbose_name_plural = _("discount rules")
        constraints = [
            CheckConstraint(
                check=Q(value__gt=Decimal("0.00")),
                name="chk_discount_value_positive"
            ),
            CheckConstraint(
                check=Q(discount_type="FIXED_AMOUNT") | (Q(discount_type="PERCENTAGE") & Q(value__lte=Decimal("100.00"))),
                name="chk_discount_percentage_max_100"
            ),
            CheckConstraint(
                check=Q(valid_until__isnull=True) | Q(valid_until__gte=models.F("valid_from")),
                name="chk_discount_validity_dates"
            ),
        ]
        indexes = [
            models.Index(fields=["code", "is_active"], name="idx_discount_code_active"),
            models.Index(fields=["valid_from", "valid_until"], name="idx_discount_dates"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.value}{'%' if self.discount_type == self.DiscountType.PERCENTAGE else ' OFF'})"

    @property
    def is_currently_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return False
        return True
