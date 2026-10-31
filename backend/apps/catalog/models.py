from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint, UniqueConstraint
from django.utils.translation import gettext_lazy as _


class Tax(models.Model):
    """
    Tax rate definition (e.g., GST 18%, VAT 20%).
    """
    name = models.CharField(max_length=128, unique=True, help_text=_("e.g. GST 18%, VAT 20%"))
    rate = models.DecimalField(
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("tax")
        verbose_name_plural = _("taxes")
        ordering = ["name"]
        constraints = [
            CheckConstraint(
                check=Q(rate__gte=Decimal("0.00")) & Q(rate__lte=Decimal("100.00")),
                name="chk_tax_rate_range"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    @property
    def rate_percent(self):
        """Compatibility property for rate percentage."""
        return self.rate


# Alias for backwards-compatibility
TaxRule = Tax


class Product(models.Model):
    """
    Product or service available in the platform catalog.
    """
    class ProductType(models.TextChoices):
        SERVICE = "service", _("Service")
        CONSUMABLE = "consumable", _("Consumable")
        SUBSCRIPTION_ADDON = "addon", _("Subscription Add-on")
        STORAGE = "storage", _("Storage / Quota")

    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    product_type = models.CharField(
        max_length=32,
        choices=ProductType.choices,
        default=ProductType.SERVICE,
        db_index=True
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
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("product")
        verbose_name_plural = _("products")
        ordering = ["name"]
        constraints = [
            CheckConstraint(
                check=Q(sales_price__gte=Decimal("0.00")),
                name="chk_product_sales_price_gte_0"
            ),
            CheckConstraint(
                check=Q(cost_price__gte=Decimal("0.00")),
                name="chk_product_cost_price_gte_0"
            ),
        ]
        indexes = [
            models.Index(fields=["name", "is_active"], name="idx_product_name_active"),
            models.Index(fields=["product_type", "is_active"], name="idx_product_type_active"),
            models.Index(fields=["created_at"], name="idx_product_created_at"),
        ]

    def __str__(self):
        return f"{self.name} [{self.sku}]"


class ProductTax(models.Model):
    """
    Associates products with applicable taxes.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_taxes"
    )
    tax = models.ForeignKey(
        Tax,
        on_delete=models.PROTECT,
        related_name="product_taxes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("product tax")
        verbose_name_plural = _("product taxes")
        constraints = [
            UniqueConstraint(
                fields=["product", "tax"],
                name="unique_product_tax"
            )
        ]

    def __str__(self):
        return f"{self.product.name} -> {self.tax.name}"


class ProductAttribute(models.Model):
    """
    Product attribute dimension (e.g. Color, Brand, Storage, Region, Tier).
    """
    name = models.CharField(max_length=128, unique=True, help_text=_("Attribute name, e.g. Tier, Storage, Region"))
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("product attribute")
        verbose_name_plural = _("product attributes")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """
    Specific value of an attribute associated with a product, with optional price delta.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="attribute_values"
    )
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.PROTECT,
        related_name="attribute_values"
    )
    value = models.CharField(max_length=128, help_text=_("Attribute value, e.g. 100GB, Enterprise, US-East"))
    price_extra = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Price adjustment delta applied to product sales_price.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("product attribute value")
        verbose_name_plural = _("product attribute values")
        constraints = [
            UniqueConstraint(
                fields=["product", "attribute", "value"],
                name="unique_product_attribute_val"
            )
        ]
        indexes = [
            models.Index(fields=["product", "attribute"], name="idx_prod_attr_val"),
        ]

    def __str__(self):
        extra_str = f" (+{self.price_extra})" if self.price_extra > Decimal("0.00") else ""
        return f"{self.product.name} - {self.attribute.name}: {self.value}{extra_str}"

    @property
    def final_price(self):
        return max(Decimal("0.00"), self.product.sales_price + self.price_extra)

    @property
    def price_adjustment(self):
        """Compatibility property for variant price adjustment."""
        return self.price_extra


# Alias for backwards-compatibility
ProductVariant = ProductAttributeValue
