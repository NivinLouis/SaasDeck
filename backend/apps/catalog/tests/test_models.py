from decimal import Decimal
from django.db import IntegrityError
from django.test import TestCase

from apps.catalog.models import Tax, Product, ProductTax, ProductAttribute, ProductAttributeValue


class CatalogModelTests(TestCase):
    def test_create_tax(self):
        tax = Tax.objects.create(name="GST 18%", rate=Decimal("18.00"))
        self.assertEqual(str(tax), "GST 18% (18.00%)")
        self.assertTrue(tax.is_active)
        self.assertEqual(tax.rate_percent, Decimal("18.00"))

    def test_create_product_attributes_and_taxes(self):
        product = Product.objects.create(
            name="Cloud Instance",
            sku="CLOUD-STD",
            sales_price=Decimal("1000.00"),
            cost_price=Decimal("600.00"),
        )
        self.assertEqual(str(product), "Cloud Instance [CLOUD-STD]")

        tax = Tax.objects.create(name="VAT 20%", rate=Decimal("20.00"))
        prod_tax = ProductTax.objects.create(product=product, tax=tax)
        self.assertEqual(str(prod_tax), "Cloud Instance -> VAT 20%")

        attr = ProductAttribute.objects.create(name="Storage Tier")
        attr_val = ProductAttributeValue.objects.create(
            product=product,
            attribute=attr,
            value="100GB SSD",
            price_extra=Decimal("250.00"),
        )
        self.assertEqual(attr_val.final_price, Decimal("1250.00"))

    def test_product_unique_sku(self):
        Product.objects.create(name="Service A", sku="SRV-1", sales_price=Decimal("100.00"))
        with self.assertRaises(IntegrityError):
            Product.objects.create(name="Service B", sku="SRV-1", sales_price=Decimal("200.00"))

    def test_negative_sales_price_constraint(self):
        with self.assertRaises(IntegrityError):
            Product.objects.create(name="Negative Price", sku="NEG-1", sales_price=Decimal("-10.00"))

    def test_duplicate_product_tax_constraint(self):
        product = Product.objects.create(name="SaaS Pro", sku="SAAS-PRO", sales_price=Decimal("50.00"))
        tax = Tax.objects.create(name="State Tax", rate=Decimal("5.00"))
        ProductTax.objects.create(product=product, tax=tax)
        with self.assertRaises(IntegrityError):
            ProductTax.objects.create(product=product, tax=tax)
