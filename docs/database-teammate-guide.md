# Database teammate guide

## Goal

Build the Brightloop PostgreSQL schema through Django models and committed
migrations. The schema must protect financial and subscription data even if an API
or background job is retried. Do not create or alter tables manually in pgAdmin.

## Before starting

1. Pull the latest `main` branch and create a branch named
   `feature/database-schema`.
2. Read `docs/backend-app-ownership.md` and coordinate field names with the
   backend developer before writing migrations.
3. Start the local stack from the repository root:

   ```powershell
   docker compose up -d db redis
   ```

4. Keep model changes in the Django app that owns the domain. Do not modify
   `accounts.User` or `customers.Customer` without agreement from the backend
   owner.

## Model implementation order

### 1. Catalog: `backend/apps/catalog/models.py`

- `Product`: name, type, sales price, cost price, notes, active state.
- `ProductAttribute`: product and attribute name.
- `ProductAttributeValue`: attribute, value, optional extra price.
- `Tax`: name, percent/fixed kind, rate, active state, validity dates.
- `ProductTax`: product-to-tax relationship.

### 2. Plans: `backend/apps/plans/models.py`

- `Plan`: price, daily/weekly/monthly/yearly billing period, minimum quantity,
  availability dates, and pause/renew/close behaviour flags.
- `PaymentTerm`: name and non-negative due-days value.

### 3. Subscriptions: `backend/apps/subscriptions/models.py`

- `QuotationTemplate` and `QuotationTemplateLine`.
- `Subscription`: customer, plan, unique number, lifecycle status, billing dates,
  payment term, salesperson, cached totals, and closing details.
- `SubscriptionLine`, selected variants, and selected taxes.
- `SubscriptionStatusLog`: immutable record of every lifecycle transition.

### 4. Billing: `backend/apps/billing/models.py`

- `Invoice`: customer and subscription references, billing period, status, dates,
  financial totals, customer JSON snapshot, and lifecycle timestamps.
- `InvoiceLine` and `InvoiceLineTax`: immutable price/tax snapshots.
- `BillingRun` and `BillingRunError`: safe scheduled/manual billing history.

### 5. Payments and discounts

- `payments.Payment`: invoice, amount, payment method/date/reference, recorder.
- `discounts.Discount`: rule values, dates, thresholds, target scope and usage limit.
- Discount target joins and `DiscountRedemption` records.

### 6. Optional after core flow works

- `reports.DailyMetric` for dashboard rollups.
- `notifications.NotificationLog` for delivery history.
- `core.AuditLog` and `core.DocumentSequence` for auditing and safe document numbers.

## Required database conventions

- Use `BigAutoField` primary keys and timezone-aware `DateTimeField` timestamps.
- Money uses `DecimalField(max_digits=12, decimal_places=2)`; never use `float`.
- Tax rates use a decimal field, not floating-point values.
- Use `DateField` for billing/expiry calendar dates.
- Add `created_at` and `updated_at` to mutable records.
- Prefer `PROTECT` for financial history. Deactivate products/plans instead of
  deleting records referenced by subscriptions or invoices.
- Use `SET_NULL` only where losing the related user must not destroy history, such
  as a creator/actor reference.

## Required integrity rules

Implement these at the database level with `UniqueConstraint`, `CheckConstraint`,
and indexes. API validation alone is not sufficient.

| Rule | Implementation |
| --- | --- |
| Subscription number is unique | `UniqueConstraint` on `Subscription.number` |
| Invoice number is unique | `UniqueConstraint` on `Invoice.number` |
| A billing period is invoiced once | unique `(subscription, period_start)` on `Invoice` |
| A discount applies once per invoice | unique `(discount, invoice)` on `DiscountRedemption` |
| Quantity is valid | check `quantity > 0` |
| Payment is valid | check `amount > 0` |
| Plan minimum quantity is valid | check `min_quantity >= 1` |
| Plan dates are valid | check `available_to >= available_from` when both exist |
| Invoice paid amount is valid | check `amount_paid <= total` |

Add indexes for the queries the product needs:

- `Subscription(status, next_billing_date)` for scheduled billing.
- `Subscription(customer, status)` for the customer portal.
- `Invoice(status, due_date)` for outstanding/overdue lists.
- `Invoice(customer, -invoice_date)` for the customer invoice list.
- `Payment(invoice)` and `Payment(payment_date, method)` for collections reports.
- `Discount(is_active, start_date, end_date)` for eligibility lookups.

## Migration workflow

After each small model batch, generate, inspect, and apply the migration:

```powershell
docker compose run --rm backend python manage.py makemigrations catalog plans
docker compose run --rm backend python manage.py sqlmigrate catalog 0001
docker compose run --rm backend python manage.py migrate
docker compose run --rm backend python manage.py check
```

Replace app names and migration numbers as appropriate. Inspect generated migration
files before committing. Once a migration is shared or merged, do not edit it;
create a new migration for corrections.

## Tests required before pull request

- Create related records and verify every foreign key relationship.
- Verify invalid prices, quantities, dates, and payment values fail.
- Verify uniqueness constraints fail on duplicate subscription/invoice periods.
- Verify protected financial records cannot be accidentally deleted.
- Run:

  ```powershell
  docker compose run --rm backend python manage.py test
  docker compose run --rm backend python manage.py check
  ```

## Pull request checklist

- Include model files and generated migrations together.
- Include an updated ER diagram or relationship notes if relationships changed.
- Explain every important constraint and index in the PR description.
- Do not commit `.env`, database dumps, passwords, or local PostgreSQL data.
- Request backend review before merging.
