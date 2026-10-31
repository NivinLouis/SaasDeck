from django.contrib import admin
from apps.catalog.models import Product, ProductAttribute, ProductAttributeValue, Tax, ProductTax


class ProductTaxInline(admin.TabularInline):
    model = ProductTax
    extra = 1


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "product_type", "sales_price", "cost_price", "is_active")
    list_filter = ("product_type", "is_active")
    search_fields = ("name", "sku")
    inlines = [ProductTaxInline, ProductAttributeValueInline]


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "is_inclusive", "is_active")
    list_filter = ("is_active", "is_inclusive")
    search_fields = ("name",)


@admin.register(ProductTax)
class ProductTaxAdmin(admin.ModelAdmin):
    list_display = ("product", "tax", "created_at")
    list_filter = ("tax",)
    search_fields = ("product__name", "tax__name")


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "created_at")
    search_fields = ("name",)


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ("product", "attribute", "value", "price_extra")
    list_filter = ("attribute",)
    search_fields = ("product__name", "value")
