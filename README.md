# SaasDeck

> A subscription-management and recurring-billing platform built for the Odoo Hackathon.

SaasDeck provides a Django REST API and a React client for managing customers,
catalog items, plans, quotations, subscriptions, invoices, payments, and
recurring billing. PostgreSQL stores application data; Redis, Celery, and
Celery Beat handle asynchronous and scheduled work.

## Features

- JWT authentication, password reset, role-based access (`admin`, `staff`, and
  `customer`), and customer self-service profiles.
- Product, tax, attribute, variant, payment-term, plan, and discount management.
- Quotation templates and subscription lifecycle actions, including customer
  quotation acceptance, pausing, resuming, and cancellation.
- Invoice creation, confirmation, cancellation, PDF and GST tax-invoice output,
  email delivery, payments, refunds, and overdue reminders.
- Idempotent scheduled billing runs with auditable run history and per-subscription
  failure capture.
- Dashboard, CSV invoice export, notifications and preferences, plan requests,
  and append-only subscription audit events.
- A React 19 client for authentication, administration, catalog, plans,
  subscriptions, invoicing, payments, reports, and portal workflows.

## Stack

- Backend: Python, Django 5, Django REST Framework
- Frontend: React 19, TypeScript, Vite, TanStack Query
- Data and background work: PostgreSQL 16, Redis 7, Celery, Celery Beat
- Documents: ReportLab and Django templates for invoice PDFs and GST HTML
- Local environment: Docker Compose

## Run locally

### Prerequisites

- Docker Engine and Docker Compose
- Git

### Start the stack

1. Create your local configuration.

   ```bash
   cp .env.example .env
   ```

   The supplied values are for local development only. Set a unique database
   password, Django secret, and email configuration before any shared deployment.

2. Build and start the application.

   ```bash
   docker compose up --build
   ```

   Docker starts PostgreSQL, Redis, the Django API, a Celery worker, Celery
   Beat, and the Vite frontend. The backend applies migrations at startup.

3. Open the services.

   - Frontend: <http://localhost:5173>
   - API health check: <http://localhost:8000/health/>
   - Django admin: <http://localhost:8000/admin/>

4. Stop the stack when finished.

   ```bash
   docker compose down
   ```

   Add `--volumes` only when you intentionally want to remove local database data.

### Useful commands

Create an administrator:

```bash
docker compose exec backend python manage.py createsuperuser
```

Run backend tests:

```bash
docker compose exec backend python manage.py test
```

Inspect background services:

```bash
docker compose logs -f celery-worker celery-beat
```

## Demo data

Seed users, catalog data, plans, quotation templates, and subscriptions:

```bash
docker compose run --rm backend python manage.py seed_demo_data
```

To reset seeded demonstration records before reseeding:

```bash
docker compose run --rm backend python manage.py seed_demo_data --clear
```

Default development credentials:

| Role | Email | Password |
| --- | --- | --- |
| Admin | `admin@brightloop.io` | `Admin@Brightloop123!` |
| Staff | `staff@brightloop.io` | `Staff@Brightloop123!` |
| Customer | `acme.corp@example.com` | `Customer@Brightloop123!` |
| Customer | `globex@example.com` | `Customer@Brightloop123!` |
| Customer | `initech@example.com` | `Customer@Brightloop123!` |

These accounts are only for local demo data. Do not use their credentials in a
shared or production environment.

## API

All business endpoints begin with `/api/v1`. Protected routes use a JWT bearer
token:

```http
Authorization: Bearer <access-token>
```

| Area | Available routes |
| --- | --- |
| Health | `GET /health/` |
| Auth | `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, password change and reset, and `/me` |
| Users and customers | `/users`, `/users/staff`, `/customers`, and `/portal/profile` |
| Catalog and plans | `/products`, `/taxes`, `/attributes`, `/variants`, `/plans`, `/payment-terms`, and `/showcase/plans` |
| Subscriptions | `/quotation-templates`, `/subscriptions`, lifecycle actions, and customer portal subscription actions |
| Billing and payments | `/invoices`, `/billing/run`, `/billing/runs`, `/payments`, and payment refunds |
| Operations | `/discounts`, `/reports/dashboard`, `/reports/invoices.csv`, `/notifications`, and notification preferences |

Route definitions in `backend/apps/*/urls.py` are the source of truth. List
endpoints support pagination through `page` and `page_size`; many also support
filtering, search, and ordering.

## Scheduled billing and email

Celery Beat schedules recurring billing and overdue reminders. Configure their
run times in `.env`:

```dotenv
BILLING_RUN_HOUR=1
BILLING_RUN_MINUTE=0
OVERDUE_REMINDER_HOUR=9
```

Billing creates invoices only for due active subscriptions, preserves
per-period uniqueness, advances the subscription after a successful invoice,
and records each run for review. The example email backend writes messages to
backend logs; configure SMTP before delivering real email.

## Repository layout

```text
SaasDeck/
├── backend/                 # Django project and feature-oriented apps
├── frontend/                # React + TypeScript client
├── docs/                    # Schema, GST invoice, test, and handoff notes
├── scripts/                 # Operational helpers
├── docker-compose.yml       # Local services
├── docker-compose.production.yml
└── .env.example             # Development configuration template
```

Useful project documents:

- [Backend app ownership](docs/backend-app-ownership.md)
- [Database teammate guide](docs/database-teammate-guide.md)
- [Database schema](docs/database_schema.md)
- [GST invoice notes](docs/gst-invoice.md)
- [Invoice PDF handoff](docs/invoice-pdf-handoff.md)
- [Billing test report](docs/billing-test-report.md)

## Production checklist

Start the production container topology with:

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml up --build -d
```

Before deployment, set a real `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, public
allowed hosts and origins, `FRONTEND_URL`, SMTP credentials, and the GST issuer
profile. The production frontend is served by Nginx, while Django runs through
Gunicorn. Container logs are written to stdout; back up PostgreSQL with
`sh scripts/backup-postgres.sh` and schedule that operation outside the app
container.
