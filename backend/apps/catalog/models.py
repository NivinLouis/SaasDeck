from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, PublicUUIDModel


class TaxRule(PublicUUIDModel, TimeStampedModel):
    """
    Tax rule applied to products, subscription lines, and invoices.
    """
    name = models.CharField(max_length=100, unique=True, help_text=_("e.g. GST 18%, VAT 20%"))
    rate_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))],
        help_text=_("Tax rate percentage (0.00 to 100.00)")
    )
    is_inclusive = models.BooleanField(
        default=False,
        help_text=_("Whether the sales price already includes this tax.")
    )
    is_active = models.BooleanField(default=True, db_index=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("tax rule")
        verbose_name_plural = _("tax rules")
        constraints = [
            CheckConstraint(
                check=Q(rate_percent__gte=Decimal("0.00")) & Q(rate_percent__lte=Decimal("100.00")),
                name="chk_tax_rate_percent_range"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.rate_percent}%)"


class Product(PublicUUIDModel, TimeStampedModel):
    """
    Product or service available in the SaaS platform catalog.
    """
    class ProductType(models.TextChoices):
        SERVICE = "SERVICE", _("Service")
        CONSUMABLE = "CONSUMABLE", _("Consumable")
        SUBSCRIPTION_ADDON = "ADDON", _("Subscription Add-on")
        STORAGE = "STORAGE", _("Storage / Quota")

    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.SERVICE
    )
    sales_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Base selling price before variant adjustments.")
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text=_("Internal unit cost price.")
    )
    tax_rule = models.ForeignKey(
        TaxRule,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="products",
        help_text=_("Default tax rate applicable to this product.")
    )
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        constraints = [
            CheckConstraint(
                check=Q(sales_price__gte=Decimal("0.00")),
                name="chk_product_sales_price_positive"
            ),
            CheckConstraint(
                check=Q(cost_price__gte=Decimal("0.00")),
                name="chk_product_cost_price_positive"
            ),
        ]
        indexes = [
            models.Index(fields=["name", "is_active"], name="idx_product_name_active"),
            models.Index(fields=["product_type", "is_active"], name="idx_product_type_active"),
        ]

    def __str__(self):
        return f"{self.name} [{self.sku}]"


class ProductVariant(PublicUUIDModel, TimeStampedModel):
    """
    Product variant representing attributes (e.g. Tier: Pro/Enterprise, Region: US/EU/IN).
    Allows price adjustments on top of the base product price.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )
    attribute_name = models.CharField(max_length=100, help_text=_("Attribute name, e.g. Tier, Region, Storage"))
    variant_value = models.CharField(max_length=100, help_text=_("Value, e.g. Enterprise, US-East, 100GB"))
    sku_extension = models.CharField(max_length=50, blank=True, null=True)
    price_adjustment = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Delta adjustment applied to product sales_price (can be negative or positive).")
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("product variant")
        verbose_name_plural = _("product variants")
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute_name", "variant_value"],
                name="unique_product_attribute_variant"
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.attribute_name}: {self.variant_value} ({'+' if self.price_adjustment >= 0 else ''}{self.price_adjustment})"

    @property
    def final_price(self):
        return max(Decimal("0.00"), self.product.sales_price + self.price_adjustment)
