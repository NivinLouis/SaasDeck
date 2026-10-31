from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import TaxRule, Product, ProductVariant


class CatalogModelTests(TestCase):
    def test_create_tax_rule(self):
        tax = TaxRule.objects.create(name="GST 18%", rate_percent=Decimal("18.00"))
        self.assertEqual(str(tax), "GST 18% (18.00%)")
        self.assertTrue(tax.is_active)

    def test_create_product_and_variants(self):
        tax = TaxRule.objects.create(name="GST 18%", rate_percent=Decimal("18.00"))
        product = Product.objects.create(
            name="Cloud Instance",
            sku="CLOUD-STD",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("600.00"),
            tax_rule=tax,
        )
        self.assertEqual(str(product), "Cloud Instance [CLOUD-STD]")

        variant = ProductVariant.objects.create(
            product=product,
            attribute_name="Tier",
            variant_value="Enterprise",
            price_adjustment=Decimal("500.00"),
        )
        self.assertEqual(variant.final_price, Decimal("1500.00"))

    def test_product_unique_sku(self):
        Product.objects.create(name="Service A", sku="SRV-1", sales_price=Decimal("100.00"))
        with self.assertRaises(IntegrityError):
            Product.objects.create(name="Service B", sku="SRV-1", sales_price=Decimal("200.00"))
