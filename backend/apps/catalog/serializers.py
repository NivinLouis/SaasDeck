"""API serializers for product and tax resources."""
from rest_framework import serializers

from .models import Product, ProductTax, Tax


class TaxSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tax
        fields = ("id", "name", "rate", "is_inclusive")


class ProductSerializer(serializers.ModelSerializer):
    """Product representation used by both staff and customer-facing catalog pages."""

    taxes = serializers.PrimaryKeyRelatedField(
        source="taxes_to_assign",
        queryset=Tax.objects.filter(is_active=True),
        many=True,
        required=False,
        write_only=True,
    )
    applied_taxes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "sku", "description", "product_type", "sales_price",
            "cost_price", "is_active", "applied_taxes", "taxes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "applied_taxes")
        extra_kwargs = {
            "cost_price": {"write_only": True},
        }

    def get_applied_taxes(self, product):
        taxes = [product_tax.tax for product_tax in product.product_taxes.select_related("tax").all()]
        return TaxSummarySerializer(taxes, many=True).data

    def validate_sku(self, value):
        return value.strip().upper()

    def create(self, validated_data):
        taxes = validated_data.pop("taxes_to_assign", [])
        product = Product.objects.create(**validated_data)
        ProductTax.objects.bulk_create([ProductTax(product=product, tax=tax) for tax in taxes])
        return product

    def update(self, instance, validated_data):
        taxes = validated_data.pop("taxes_to_assign", None)
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        instance.save()

        if taxes is not None:
            instance.product_taxes.all().delete()
            ProductTax.objects.bulk_create([ProductTax(product=instance, tax=tax) for tax in taxes])
        return instance
