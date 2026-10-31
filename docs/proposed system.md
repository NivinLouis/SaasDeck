# SaasDeck Subscription Management System

Architecture, API design and database schema (v1)

## 1. Scope and design principles

One platform that runs the full subscription lifecycle: catalog, plans, quotations, subscriptions, automated invoicing, discounts, payments and finance reporting, for three kinds of users (admin, staff, customer).

Principles that shape every decision below:

- **Idempotent billing.** Nothing is billed twice or skipped. A database unique constraint, not application logic alone, enforces this.
- **Snapshot money.** Invoices copy prices, tax rates and discount amounts at creation time, so later catalog edits never change history.
- **Server-side RBAC.** Role and object-level checks live in the API layer; the UI only hides things.
- **Fast reads.** Every list is paginated and indexed; dashboards use aggregate queries plus a Redis cache so pages stay under 2 seconds with tens of thousands of subscriptions.
- **Auditable state machines.** Subscription and invoice transitions are explicit, validated and logged.

## 2. Technology stack

| Layer | Choice | Why |
| --- | --- | --- |
| API | Django 5 + Django REST Framework | Fast to build, strong ORM, built-in auth and admin |
| Database | PostgreSQL 16 (MySQL 8 also works) | Partial unique indexes, row locks with SKIP LOCKED, good aggregates |
| Async jobs | Celery + Celery Beat | Scheduled billing, emails, reminders |
| Broker and cache | Redis | Celery broker, dashboard cache, throttling |
| Auth | JWT (djangorestframework-simplejwt) | Stateless, works for SPA and mobile |
| PDF | WeasyPrint | Printable invoices from HTML templates |
| Email | SMTP or provider API (SES, SendGrid) | Reset links, invoices, reminders |
| Frontend | React (or Django templates for a thin portal) | Admin console, staff screens, customer portal |
| Packaging | Docker Compose: api, worker, beat, postgres, redis, nginx | One-command local and prod parity |

## 3. High-level architecture

```
  Browser (Admin / Staff / Customer portal)
              |  HTTPS
          [ Nginx ]
              |
     [ Django + DRF API ]  <---->  [ Redis ]  (cache, throttle, broker)
        |            |                   |
        |            +---- enqueue ----> [ Celery workers ]  <--- [ Celery Beat ]
        |                                   |   (billing, emails, PDFs, reminders)
        +-------------------+---------------+
                            |
                     [ PostgreSQL ]
```

### Django apps (modular monolith)

| App | Responsibility |
| --- | --- |
| accounts | Users, roles, auth, password reset, staff creation |
| customers | Customer profiles linked to portal users |
| catalog | Products, variants (attributes), taxes |
| plans | Plans, billing periods, plan behaviour flags |
| subscriptions | Quotation templates, subscriptions, lines, lifecycle |
| discounts | Discount rules, eligibility, redemptions |
| billing | Invoices, invoice lines, billing engine, numbering, PDFs |
| payments | Payment records, outstanding and overdue logic |
| reports | Dashboard aggregates, filters, exports |
| core | Audit log, notifications, sequences, shared utilities |

Each app owns its models and exposes a `services.py` with business logic. Views stay thin and call services. The billing engine only reads other apps through their services.