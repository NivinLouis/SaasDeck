# Backend app ownership

Each Django app owns its models, API serializers/views, services, background tasks,
admin registration, migrations, and tests. Keep API views thin: write operations
should delegate to the app's `services.py` and financial operations must use database
transactions and constraints.

| App | Owns | Initial owner |
| --- | --- | --- |
| `core` | Shared permissions, pagination, error handling, audit and sequences | Backend |
| `accounts` | Users, roles and authentication | Backend |
| `customers` | Customer profiles and portal ownership boundary | Backend |
| `catalog` | Products, variants and taxes | Database + backend |
| `plans` | Plans and payment terms | Database + backend |
| `subscriptions` | Quotations, subscription lines and state history | Backend |
| `discounts` | Discount rules and redemptions | Backend |
| `billing` | Invoices, billing runs and immutable snapshots | Backend |
| `payments` | Payments and reversals | Backend |
| `reports` | Dashboard aggregates and exports | Backend + frontend |
| `notifications` | Delivery logs and background communications | Backend |

Do not add a model migration until the relevant schema has been reviewed. Do not
manually change PostgreSQL tables outside Django migrations.

The database teammate's step-by-step implementation and migration checklist is in
[`database-teammate-guide.md`](database-teammate-guide.md).
