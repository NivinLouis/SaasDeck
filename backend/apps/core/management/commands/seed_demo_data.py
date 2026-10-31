from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.customers.models import Customer
from apps.catalog.models import (
    Product,
    ProductAttribute,
    ProductAttributeValue,
    Tax,
    ProductTax,
)
from apps.plans.models import Plan, PaymentTerm
from apps.subscriptions.models import (
    QuotationTemplate,
    QuotationTemplateLine,
    Subscription,
    SubscriptionLine,
)


class Command(BaseCommand):
    help = "Seeds the database with realistic demonstration data for Brightloop / SaasDeck."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seeded subscriptions, products, and plans before seeding.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Starting Brightloop Demo Data Seed ==="))

        with transaction.atomic():
            if options.get("clear"):
                self.stdout.write(self.style.WARNING("Clearing existing demonstration records..."))
                SubscriptionLine.objects.all().delete()
                Subscription.objects.all().delete()
                QuotationTemplateLine.objects.all().delete()
                QuotationTemplate.objects.all().delete()
                ProductTax.objects.all().delete()
                ProductAttributeValue.objects.all().delete()
                ProductAttribute.objects.all().delete()
                Product.objects.all().delete()
                Plan.objects.all().delete()
                PaymentTerm.objects.all().delete()
                Tax.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("Existing demonstration records cleared."))

            # 1. Admin & Staff Users
            admin_user, staff_user, cust_users = self._seed_users()

            # 2. Customers
            customers = self._seed_customers(admin_user, cust_users)

            # 3. Taxes
            taxes = self._seed_taxes()

            # 4. Products, Attributes, and Variants (including +$560 Odoo variant)
            products, variants = self._seed_products_and_variants(taxes)

            # 5. Payment Terms & Plans
            payment_terms, plans = self._seed_plans_and_terms(products)

            # 6. Quotation Templates
            templates = self._seed_quotation_templates(plans, products, variants)

            # 7. Customer Subscriptions (DRAFT, QUOTATION, ACTIVE, PAUSED)
            self._seed_subscriptions(customers, plans, templates, products, variants, taxes, admin_user)

        self.stdout.write(self.style.SUCCESS("\n=== Demo Data Seed Completed Successfully! ==="))
        self.stdout.write(self.style.SUCCESS(
            "\nDefault Credentials:\n"
            "  Admin:    admin@brightloop.io     / Admin@Brightloop123!\n"
            "  Staff:    staff@brightloop.io     / Staff@Brightloop123!\n"
            "  Customer: acme.corp@example.com   / Customer@Brightloop123!\n"
            "  Customer: globex@example.com      / Customer@Brightloop123!\n"
            "  Customer: initech@example.com     / Customer@Brightloop123!\n"
        ))

    def _seed_users(self):
        self.stdout.write("\n[1/7] Seeding Users...")

        # Admin
        admin_email = "admin@brightloop.io"
        admin_pass = "Admin@Brightloop123!"
        admin_user = User.objects.filter(email=admin_email).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password=admin_pass,
                full_name="Brightloop System Administrator",
            )
            self.stdout.write(f"  + Created Admin: {admin_email}")
        else:
            admin_user.set_password(admin_pass)
            admin_user.full_name = "Brightloop System Administrator"
            admin_user.role = User.Role.ADMIN
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(f"  ~ Updated Admin: {admin_email}")

        # Staff
        staff_email = "staff@brightloop.io"
        staff_pass = "Staff@Brightloop123!"
        staff_user = User.objects.filter(email=staff_email).first()
        if not staff_user:
            staff_user = User.objects.create_user(
                email=staff_email,
                password=staff_pass,
                full_name="Operations Staff Member",
                role=User.Role.STAFF,
                is_staff=True,
            )
            self.stdout.write(f"  + Created Staff: {staff_email}")
        else:
            staff_user.set_password(staff_pass)
            staff_user.full_name = "Operations Staff Member"
            staff_user.role = User.Role.STAFF
            staff_user.is_staff = True
            staff_user.save()
            self.stdout.write(f"  ~ Updated Staff: {staff_email}")

        # Customer users
        cust_emails = [
            ("acme.corp@example.com", "Acme Corporation", "Customer@Brightloop123!"),
            ("globex@example.com", "Globex Industries", "Customer@Brightloop123!"),
            ("initech@example.com", "Initech Solutions", "Customer@Brightloop123!"),
        ]
        cust_users = {}
        for email, name, pwd in cust_emails:
            u = User.objects.filter(email=email).first()
            if not u:
                u = User.objects.create_user(
                    email=email,
                    password=pwd,
                    full_name=name,
                    role=User.Role.CUSTOMER,
                )
                self.stdout.write(f"  + Created Customer User: {email}")
            else:
                u.set_password(pwd)
                u.full_name = name
                u.role = User.Role.CUSTOMER
                u.save()
                self.stdout.write(f"  ~ Updated Customer User: {email}")
            cust_users[email] = u

        return admin_user, staff_user, cust_users

    def _seed_customers(self, admin_user, cust_users):
        self.stdout.write("\n[2/7] Seeding Customer Profiles...")
        customers_data = [
            {
                "email": "acme.corp@example.com",
                "name": "Acme Corporation",
                "company": "Acme Corp Ltd.",
                "phone": "+1-555-0199",
                "billing_address": "100 Innovation Way, Suite 400",
                "city": "San Francisco",
                "state": "California",
                "country": "United States",
                "postal_code": "94105",
                "tax_id": "US-EIN-98765432",
            },
            {
                "email": "globex@example.com",
                "name": "Globex Industries",
                "company": "Globex Global Pvt Ltd",
                "phone": "+91-80-23456789",
                "billing_address": "Plot 42, Electronics City Phase 1",
                "city": "Bengaluru",
                "state": "Karnataka",
                "country": "India",
                "postal_code": "560100",
                "tax_id": "29AAAAA0000A1Z5",
            },
            {
                "email": "initech@example.com",
                "name": "Initech Solutions",
                "company": "Initech Enterprise Ltd",
                "phone": "+44-20-79460912",
                "billing_address": "25 Finsbury Square",
                "city": "London",
                "state": "Greater London",
                "country": "United Kingdom",
                "postal_code": "EC2A 1DX",
                "tax_id": "GB-VAT-123456789",
            },
        ]
        customers = {}
        for data in customers_data:
            user = cust_users.get(data["email"])
            customer, created = Customer.objects.update_or_create(
                email=data["email"],
                defaults={
                    "user": user,
                    "name": data["name"],
                    "company": data["company"],
                    "phone": data["phone"],
                    "billing_address": data["billing_address"],
                    "city": data["city"],
                    "state": data["state"],
                    "country": data["country"],
                    "postal_code": data["postal_code"],
                    "tax_id": data["tax_id"],
                    "created_by": admin_user,
                },
            )
            customers[data["email"]] = customer
            action = "+" if created else "~"
            self.stdout.write(f"  {action} Customer Profile: {customer.name} ({customer.email})")

        return customers

    def _seed_taxes(self):
        self.stdout.write("\n[3/7] Seeding Taxes...")
        taxes_data = [
            {"name": "GST 18%", "rate": Decimal("18.00"), "is_inclusive": False},
            {"name": "VAT 20%", "rate": Decimal("20.00"), "is_inclusive": False},
            {"name": "Zero Tax 0%", "rate": Decimal("0.00"), "is_inclusive": False},
        ]
        taxes = {}
        for t in taxes_data:
            tax, created = Tax.objects.update_or_create(
                name=t["name"],
                defaults={
                    "rate": t["rate"],
                    "is_inclusive": t["is_inclusive"],
                    "is_active": True,
                },
            )
            taxes[t["name"]] = tax
            action = "+" if created else "~"
            self.stdout.write(f"  {action} Tax: {tax.name} ({tax.rate}%)")

        return taxes

    def _seed_plans_and_terms(self, products):
        self.stdout.write("\n[5/7] Seeding Payment Terms & Plans...")

        # Payment terms
        terms_data = [
            {"name": "Immediate Payment", "days": 0, "description": "Payment due immediately upon invoice generation."},
            {"name": "Net 15", "days": 15, "description": "Payment due within 15 calendar days."},
            {"name": "Net 30", "days": 30, "description": "Payment due within 30 calendar days."},
        ]
        payment_terms = {}
        for term in terms_data:
            obj, created = PaymentTerm.objects.update_or_create(
                name=term["name"],
                defaults={
                    "days": term["days"],
                    "description": term["description"],
                    "is_active": True,
                },
            )
            payment_terms[term["name"]] = obj
            action = "+" if created else "~"
            self.stdout.write(f"  {action} Payment Term: {obj.name}")

        # Plans across all intervals: Daily, Weekly, Monthly, Yearly
        plans_data = [
            {
                "code": "starter-daily",
                "name": "Starter Daily",
                "product": products["erp"],
                "currency": "INR",
                "billing_interval": Plan.BillingInterval.DAILY,
                "interval_count": 1,
                "price": Decimal("49.00"),
                "minimum_quantity": 1,
                "payment_term": payment_terms["Immediate Payment"],
                "trial_period_days": 1,
                "description": "Daily pay-as-you-go metered computing and basic CRM access.",
            },
            {
                "code": "growth-weekly",
                "name": "Growth Weekly",
                "product": products["erp"],
                "currency": "INR",
                "billing_interval": Plan.BillingInterval.WEEKLY,
                "interval_count": 1,
                "price": Decimal("199.00"),
                "minimum_quantity": 1,
                "payment_term": payment_terms["Immediate Payment"],
                "trial_period_days": 3,
                "description": "Weekly sprint subscription plan for rapidly scaling agile teams.",
            },
            {
                "code": "pro-monthly",
                "name": "Professional Monthly",
                "product": products["erp"],
                "currency": "INR",
                "billing_interval": Plan.BillingInterval.MONTHLY,
                "interval_count": 1,
                "price": Decimal("799.00"),
                "minimum_quantity": 1,
                "payment_term": payment_terms["Net 15"],
                "trial_period_days": 14,
                "description": "Comprehensive monthly SaaS package with standard ERP and storage.",
            },
            {
                "code": "enterprise-yearly",
                "name": "Enterprise Yearly",
                "product": products["erp"],
                "currency": "INR",
                "billing_interval": Plan.BillingInterval.YEARLY,
                "interval_count": 1,
                "price": Decimal("7999.00"),
                "minimum_quantity": 5,
                "payment_term": payment_terms["Net 30"],
                "trial_period_days": 30,
                "description": "Annual enterprise contract with dedicated cluster, SLA, and custom integration.",
            },
        ]
        plans = {}
        for p in plans_data:
            plan, created = Plan.objects.update_or_create(
                code=p["code"],
                defaults={
                    "name": p["name"],
                    "product": p["product"],
                    "currency": p["currency"],
                    "billing_interval": p["billing_interval"],
                    "interval_count": p["interval_count"],
                    "price": p["price"],
                    "minimum_quantity": p["minimum_quantity"],
                    "payment_term": p["payment_term"],
                    "trial_period_days": p["trial_period_days"],
                    "description": p["description"],
                    "auto_close_on_expiry": True,
                    "allow_early_closure": True,
                    "allow_pause": True,
                    "allow_auto_renewal": True,
                    "is_active": True,
                },
            )
            plans[p["code"]] = plan
            action = "+" if created else "~"
            self.stdout.write(f"  {action} Plan: {plan.name} (${plan.price} / {plan.billing_interval})")

        return payment_terms, plans

    def _seed_products_and_variants(self, taxes):
        self.stdout.write("\n[5/7] Seeding Products, Attributes, and Variants...")

        # Product Attributes
        attr_brand, _ = ProductAttribute.objects.update_or_create(
            name="Platform Edition / Brand",
            defaults={"description": "Software brand or edition tier."}
        )
        attr_storage, _ = ProductAttribute.objects.update_or_create(
            name="Storage Capacity",
            defaults={"description": "Allocated cloud volume quota."}
        )
        attr_api, _ = ProductAttribute.objects.update_or_create(
            name="API Throughput",
            defaults={"description": "Concurrent API request rate limits."}
        )
        attr_sla, _ = ProductAttribute.objects.update_or_create(
            name="Support SLA",
            defaults={"description": "Guaranteed response time level."}
        )

        products = {}
        variants = {}

        # 1. Service: Cloud ERP Core Service (includes the +$560 Odoo variant!)
        prod_erp, created = Product.objects.update_or_create(
            sku="PROD-ERP-CORE",
            defaults={
                "name": "Cloud ERP Core Service",
                "description": "Enterprise Cloud ERP core platform covering Accounting, Inventory, and CRM.",
                "product_type": Product.ProductType.SERVICE,
                "sales_price": Decimal("1200.00"),
                "cost_price": Decimal("300.00"),
                "is_active": True,
            },
        )
        ProductTax.objects.get_or_create(product=prod_erp, tax=taxes["GST 18%"])
        ProductTax.objects.get_or_create(product=prod_erp, tax=taxes["VAT 20%"])
        products["erp"] = prod_erp

        var_erp_std, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_erp,
            attribute=attr_brand,
            value="Standard Edition",
            defaults={"price_extra": Decimal("0.00")},
        )
        # Hackathon Brief requirement: +560 Odoo brand variant
        var_erp_odoo, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_erp,
            attribute=attr_brand,
            value="Odoo Enterprise Edition",
            defaults={"price_extra": Decimal("560.00")},
        )
        variants["erp_std"] = var_erp_std
        variants["erp_odoo"] = var_erp_odoo
        self.stdout.write(f"  + Product (Service): {prod_erp.name} [Odoo Variant: +$560.00]")

        # 2. Consumable: API Request Pack
        prod_api, _ = Product.objects.update_or_create(
            sku="PROD-API-PACK",
            defaults={
                "name": "API Request Pack (100k)",
                "description": "Pack of 100,000 automated API calls for data pipelines and webhook syncs.",
                "product_type": Product.ProductType.CONSUMABLE,
                "sales_price": Decimal("150.00"),
                "cost_price": Decimal("25.00"),
                "is_active": True,
            },
        )
        ProductTax.objects.get_or_create(product=prod_api, tax=taxes["GST 18%"])
        products["api"] = prod_api

        var_api_std, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_api,
            attribute=attr_api,
            value="Standard (100 req/s)",
            defaults={"price_extra": Decimal("0.00")},
        )
        var_api_burst, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_api,
            attribute=attr_api,
            value="Priority Burst (500 req/s)",
            defaults={"price_extra": Decimal("75.00")},
        )
        variants["api_std"] = var_api_std
        variants["api_burst"] = var_api_burst
        self.stdout.write(f"  + Product (Consumable): {prod_api.name}")

        # 3. Storage: Encrypted Cloud Storage
        prod_storage, _ = Product.objects.update_or_create(
            sku="PROD-STORAGE-SEC",
            defaults={
                "name": "Encrypted Cloud Storage",
                "description": "Compliant S3-compatible AES-256 encrypted object and backup storage.",
                "product_type": Product.ProductType.STORAGE,
                "sales_price": Decimal("80.00"),
                "cost_price": Decimal("15.00"),
                "is_active": True,
            },
        )
        ProductTax.objects.get_or_create(product=prod_storage, tax=taxes["GST 18%"])
        ProductTax.objects.get_or_create(product=prod_storage, tax=taxes["VAT 20%"])
        products["storage"] = prod_storage

        var_storage_250, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_storage,
            attribute=attr_storage,
            value="250 GB Tier",
            defaults={"price_extra": Decimal("0.00")},
        )
        var_storage_1tb, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_storage,
            attribute=attr_storage,
            value="1 TB Tier",
            defaults={"price_extra": Decimal("120.00")},
        )
        variants["storage_250"] = var_storage_250
        variants["storage_1tb"] = var_storage_1tb
        self.stdout.write(f"  + Product (Storage): {prod_storage.name}")

        # 4. Add-on: Dedicated Support & SLA
        prod_addon, _ = Product.objects.update_or_create(
            sku="PROD-ADDON-SLA",
            defaults={
                "name": "Premium Dedicated SLA",
                "description": "Named Technical Account Manager with 15-minute emergency response guarantee.",
                "product_type": Product.ProductType.SUBSCRIPTION_ADDON,
                "sales_price": Decimal("350.00"),
                "cost_price": Decimal("100.00"),
                "is_active": True,
            },
        )
        ProductTax.objects.get_or_create(product=prod_addon, tax=taxes["GST 18%"])
        products["addon"] = prod_addon

        var_sla_8x5, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_addon,
            attribute=attr_sla,
            value="Standard (8x5 Business)",
            defaults={"price_extra": Decimal("0.00")},
        )
        var_sla_247, _ = ProductAttributeValue.objects.update_or_create(
            product=prod_addon,
            attribute=attr_sla,
            value="Mission Critical (24x7 Dedicated)",
            defaults={"price_extra": Decimal("250.00")},
        )
        variants["sla_8x5"] = var_sla_8x5
        variants["sla_247"] = var_sla_247
        self.stdout.write(f"  + Product (Add-on): {prod_addon.name}")

        return products, variants

    def _seed_quotation_templates(self, plans, products, variants):
        self.stdout.write("\n[6/7] Seeding Quotation Templates...")
        templates = {}

        # Template 1: Standard SaaS Onboarding
        tmpl_std, created = QuotationTemplate.objects.update_or_create(
            name="Standard SaaS Onboarding Template",
            defaults={
                "plan": plans["pro-monthly"],
                "validity_days": 30,
                "terms_and_conditions": "30 days payment window. Includes standard SLA and daily automated backups.",
                "is_active": True,
            },
        )
        QuotationTemplateLine.objects.filter(template=tmpl_std).delete()
        QuotationTemplateLine.objects.create(
            template=tmpl_std,
            product=products["erp"],
            variant=variants["erp_std"],
            quantity=1,
            discount_percent=Decimal("0.00"),
        )
        QuotationTemplateLine.objects.create(
            template=tmpl_std,
            product=products["storage"],
            variant=variants["storage_250"],
            quantity=2,
            discount_percent=Decimal("0.00"),
        )
        templates["standard"] = tmpl_std
        self.stdout.write(f"  + Template: {tmpl_std.name}")

        # Template 2: Enterprise Odoo Migration
        tmpl_odoo, created = QuotationTemplate.objects.update_or_create(
            name="Enterprise Odoo Migration Template",
            defaults={
                "plan": plans["enterprise-yearly"],
                "validity_days": 45,
                "terms_and_conditions": (
                    "Annual commitment. Includes Odoo Enterprise Edition brand upgrade, "
                    "1 TB dedicated storage tier, and 24x7 Mission Critical SLA support."
                ),
                "is_active": True,
            },
        )
        QuotationTemplateLine.objects.filter(template=tmpl_odoo).delete()
        QuotationTemplateLine.objects.create(
            template=tmpl_odoo,
            product=products["erp"],
            variant=variants["erp_odoo"],
            quantity=5,
            discount_percent=Decimal("10.00"),
        )
        QuotationTemplateLine.objects.create(
            template=tmpl_odoo,
            product=products["storage"],
            variant=variants["storage_1tb"],
            quantity=2,
            discount_percent=Decimal("0.00"),
        )
        QuotationTemplateLine.objects.create(
            template=tmpl_odoo,
            product=products["addon"],
            variant=variants["sla_247"],
            quantity=1,
            discount_percent=Decimal("5.00"),
        )
        templates["enterprise_odoo"] = tmpl_odoo
        self.stdout.write(f"  + Template: {tmpl_odoo.name}")

        return templates

    def _seed_subscriptions(self, customers, plans, templates, products, variants, taxes, admin_user):
        self.stdout.write("\n[7/7] Seeding Subscriptions in Various Statuses (DRAFT, QUOTATION, ACTIVE, PAUSED)...")
        today = timezone.localdate()

        # 1. DRAFT Subscription
        sub_draft, _ = Subscription.objects.update_or_create(
            subscription_number="SUB-2026-0001",
            defaults={
                "customer": customers["acme.corp@example.com"],
                "plan": plans["starter-daily"],
                "status": Subscription.Status.DRAFT,
                "template": templates["standard"],
                "payment_terms": "Immediate Payment",
                "auto_renew": True,
                "created_by": admin_user,
            },
        )
        SubscriptionLine.objects.filter(subscription=sub_draft).delete()
        SubscriptionLine.objects.create(
            subscription=sub_draft,
            product=products["erp"],
            variant=variants["erp_std"],
            quantity=1,
            unit_price=Decimal("1200.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("0.00"),
        )
        SubscriptionLine.objects.create(
            subscription=sub_draft,
            product=products["api"],
            variant=variants["api_std"],
            quantity=2,
            unit_price=Decimal("150.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("0.00"),
        )
        self.stdout.write(f"  + [DRAFT] Subscription: {sub_draft.subscription_number} for {sub_draft.customer.name}")

        # 2. QUOTATION Subscription
        sub_quot, _ = Subscription.objects.update_or_create(
            subscription_number="SUB-2026-0002",
            defaults={
                "customer": customers["globex@example.com"],
                "plan": plans["growth-weekly"],
                "status": Subscription.Status.QUOTATION,
                "template": templates["enterprise_odoo"],
                "payment_terms": "Net 15",
                "auto_renew": True,
                "created_by": admin_user,
            },
        )
        SubscriptionLine.objects.filter(subscription=sub_quot).delete()
        # $1200 + $560 = $1760 unit price
        SubscriptionLine.objects.create(
            subscription=sub_quot,
            product=products["erp"],
            variant=variants["erp_odoo"],
            quantity=2,
            unit_price=Decimal("1760.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("5.00"),
        )
        SubscriptionLine.objects.create(
            subscription=sub_quot,
            product=products["storage"],
            variant=variants["storage_250"],
            quantity=1,
            unit_price=Decimal("80.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("0.00"),
        )
        self.stdout.write(f"  + [QUOTATION] Subscription: {sub_quot.subscription_number} for {sub_quot.customer.name}")

        # 3. ACTIVE Subscription
        sub_active, _ = Subscription.objects.update_or_create(
            subscription_number="SUB-2026-0003",
            defaults={
                "customer": customers["initech@example.com"],
                "plan": plans["pro-monthly"],
                "status": Subscription.Status.ACTIVE,
                "template": templates["enterprise_odoo"],
                "payment_terms": "Net 30",
                "start_date": today - timedelta(days=30),
                "current_period_start": today,
                "current_period_end": today + timedelta(days=30),
                "next_billing_date": today + timedelta(days=30),
                "expiry_date": today + timedelta(days=335),
                "auto_renew": True,
                "created_by": admin_user,
            },
        )
        SubscriptionLine.objects.filter(subscription=sub_active).delete()
        SubscriptionLine.objects.create(
            subscription=sub_active,
            product=products["erp"],
            variant=variants["erp_odoo"],
            quantity=5,
            unit_price=Decimal("1760.00"),
            tax_rule=taxes["VAT 20%"],
            discount_percent=Decimal("10.00"),
        )
        # $80 + $120 = $200 unit price
        SubscriptionLine.objects.create(
            subscription=sub_active,
            product=products["storage"],
            variant=variants["storage_1tb"],
            quantity=2,
            unit_price=Decimal("200.00"),
            tax_rule=taxes["VAT 20%"],
            discount_percent=Decimal("0.00"),
        )
        # $350 + $250 = $600 unit price
        SubscriptionLine.objects.create(
            subscription=sub_active,
            product=products["addon"],
            variant=variants["sla_247"],
            quantity=1,
            unit_price=Decimal("600.00"),
            tax_rule=taxes["VAT 20%"],
            discount_percent=Decimal("5.00"),
        )
        self.stdout.write(f"  + [ACTIVE] Subscription: {sub_active.subscription_number} for {sub_active.customer.name}")

        # 4. PAUSED Subscription
        sub_paused, _ = Subscription.objects.update_or_create(
            subscription_number="SUB-2026-0004",
            defaults={
                "customer": customers["acme.corp@example.com"],
                "plan": plans["enterprise-yearly"],
                "status": Subscription.Status.PAUSED,
                "template": templates["standard"],
                "payment_terms": "Net 30",
                "start_date": today - timedelta(days=90),
                "current_period_start": today - timedelta(days=30),
                "current_period_end": today + timedelta(days=275),
                "next_billing_date": today + timedelta(days=15),
                "expiry_date": today + timedelta(days=275),
                "auto_renew": False,
                "created_by": admin_user,
            },
        )
        SubscriptionLine.objects.filter(subscription=sub_paused).delete()
        SubscriptionLine.objects.create(
            subscription=sub_paused,
            product=products["erp"],
            variant=variants["erp_std"],
            quantity=3,
            unit_price=Decimal("1200.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("0.00"),
        )
        SubscriptionLine.objects.create(
            subscription=sub_paused,
            product=products["storage"],
            variant=variants["storage_1tb"],
            quantity=1,
            unit_price=Decimal("200.00"),
            tax_rule=taxes["GST 18%"],
            discount_percent=Decimal("0.00"),
        )
        self.stdout.write(f"  + [PAUSED] Subscription: {sub_paused.subscription_number} for {sub_paused.customer.name}")
