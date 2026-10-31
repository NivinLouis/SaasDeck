from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel


class Plan(PublicUUIDModel, TimeStampedModel):
    """
    SaaS Subscription Plan defining recurring billing cycles, pricing, and lifecycle policies.
    """
    class BillingInterval(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        YEARLY = "YEARLY", _("Yearly")

    name = models.CharField(max_length=255, unique=True, db_index=True)
    code = models.SlugField(max_length=100, unique=True, db_index=True, help_text=_("Unique identifier, e.g. pro-monthly"))
    description = models.TextField(blank=True, null=True)

    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
        db_index=True
    )
    interval_count = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Number of intervals per billing cycle (e.g. 3 with MONTHLY = quarterly).")
    )
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Base recurring subscription fee per interval.")
    )
    minimum_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Minimum seats or quantity required to subscribe to this plan.")
    )
    trial_period_days = models.PositiveIntegerField(
        default=0,
        help_text=_("Trial period duration in days before billing starts.")
    )

    # Lifecycle & Behavioral Policy Flags
    auto_close_on_expiry = models.BooleanField(
        default=True,
        help_text=_("Automatically transition subscription to CLOSED when expiry date is reached without renewal.")
    )
    allow_early_closure = models.BooleanField(
        default=True,
        help_text=_("Allow customers or staff to terminate subscription before end of billing cycle.")
    )
    allow_pause = models.BooleanField(
        default=True,
        help_text=_("Allow subscription to be temporarily paused.")
    )
    allow_auto_renewal = models.BooleanField(
        default=True,
        help_text=_("Allow automatic renewal of active subscriptions.")
    )

    # Availability constraints
    available_from = models.DateField(
        blank=True,
        null=True,
        help_text=_("Date from which this plan becomes available for new subscriptions.")
    )
    available_until = models.DateField(
        blank=True,
        null=True,
        help_text=_("Date after which new subscriptions cannot select this plan.")
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = _("plan")
        verbose_name_plural = _("plans")
        constraints = [
            CheckConstraint(
                check=Q(base_price__gte=Decimal("0.00")),
                name="chk_plan_base_price_positive"
            ),
            CheckConstraint(
                check=Q(interval_count__gte=1),
                name="chk_plan_interval_count_gte_1"
            ),
            CheckConstraint(
                check=Q(minimum_quantity__gte=1),
                name="chk_plan_minimum_quantity_gte_1"
            ),
            CheckConstraint(
                check=Q(available_until__isnull=True) | Q(available_from__isnull=True) | Q(available_until__gte=models.F("available_from")),
                name="chk_plan_available_dates_valid"
            ),
        ]
        indexes = [
            models.Index(fields=["billing_interval", "is_active"], name="idx_plan_interval_active"),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_billing_interval_display()} - {self.base_price})"
