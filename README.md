# SaasDeck

> Subscription management and recurring billing platform for the Odoo Hackathon.

SaasDeck is a Django and React application for managing customers, products,
subscription plans, quotations, invoices, payments, and recurring billing. It
uses PostgreSQL for persistence, Redis and Celery for background work, and
Docker Compose for local development.

## Current status

The project is actively being developed. The following are available in the
current `main` branch:

- JWT authentication with `admin`, `staff`, and `customer` roles, strong
  password validation, customer sign-up, token refresh/logout, and password
  change.
- Customer directory and customer self-service billing profile.
- Product, tax, product-attribute/variant, plan, and payment-term management.
- Quotation templates, draft subscriptions, quotation creation from a
  template, and the initial send-quotation, confirm, activate, pause, resume,
  and cancel lifecycle actions.
- Draft/confirmed/cancelled invoices, GST tax-invoice HTML, generated PDF
  downloads, and invoice email delivery.
- Partial and full payment recording with invoice balance updates and payment
  refunds.
- Daily, idempotent recurring billing runs through Celery, including billing
  run history and captured per-subscription failures.
- A staff dashboard summary and a private in-app notification inbox.
- React screens for authentication, customers, catalog/products, plans,
  subscriptions, invoices, payments, administration, and the dashboard.

Still in progress: detailed reports and CSV exports, subscription-line and
quotation-template-line APIs, discount redemption/application during billing,
dedicated customer portal subscription/invoice routes, additional account
administration, and broader frontend coverage for operations features.

## Stack

- Backend: Python 3.12, Django 5, Django REST Framework
- Frontend: React 19, TypeScript, Vite, TanStack Query
- Data and background work: PostgreSQL 16, Redis 7, Celery, Celery Beat
- Documents: ReportLab and Django templates for invoice PDFs and GST HTML
- Local orchestration: Docker Compose

## Run locally

### Prerequisites

- Docker Engine and Docker Compose
- Git

### Start the application

1. Create your local environment file.

   ```bash
   cp .env.example .env
   ```

   The example configuration is for local development only. Replace its
   database password, Django secret key, and email configuration before any
   shared or production deployment.

2. Build and start every service.

   ```bash
   docker compose up --build
   ```

   Docker starts PostgreSQL, Redis, the Django API, a Celery worker, Celery
   Beat, and the Vite frontend. Database migrations run automatically when the
   backend starts.

3. Open the application.

   - Frontend: http://localhost:5173
   - API health check: http://localhost:8000/health/
   - Django admin: http://localhost:8000/admin/

4. Stop the stack when finished.

   ```bash
   docker compose down
   ```

   Add `--volumes` only when you intentionally want to remove local database
   data.

### Useful commands

Create an administrator:

```bash
docker compose exec backend python manage.py createsuperuser
```

Run the backend tests:

```bash
docker compose exec backend python manage.py test
```

Run a one-off recurring billing run as an authenticated admin through the API,
or inspect the worker/Beat logs:

```bash
docker compose logs -f celery-worker celery-beat
```

## Demo data

Populate the database with demonstration users, catalog data, plans,
quotation templates, and subscriptions:

```bash
docker compose run --rm backend python manage.py seed_demo_data
```

Reset only seeded demonstration records before seeding again:

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

These credentials are intentionally for local demo data only.

## API

All business API routes begin with `/api/v1`. Protected routes use a JWT bearer
token:

```http
Authorization: Bearer <access-token>
```

Requests and validation errors use JSON. List endpoints support pagination via
`page` and `page_size`; many also support documented filters, search, and
ordering fields.

| Area | Available routes |
| --- | --- |
| Health | `GET /health/` |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/password/change`; `GET /me` |
| Users | `GET /users`; `POST /users/staff` |
| Customers | `GET, POST /customers`; `GET, PATCH /customers/{id}`; `GET, PATCH /portal/profile` |
| Catalog | `GET, POST /products`, `/taxes`, `/attributes`, `/variants`; `GET, PATCH` detail routes for each resource |
| Plans | `GET, POST /plans`, `/payment-terms`; `GET, PATCH` detail routes |
| Quotations and subscriptions | `GET, POST /quotation-templates`; `GET, PATCH /quotation-templates/{uuid}`; `POST /quotation-templates/{uuid}/quotations`; `GET, POST /subscriptions`; subscription detail and lifecycle action routes |
| Discounts | `GET, POST /discounts`; `GET, PATCH /discounts/{uuid}` |
| Invoices and billing | Invoice list/detail/create, confirm, cancel, send, PDF, GST tax-invoice HTML; `POST /billing/run`; billing run list/detail |
| Payments | `GET, POST /payments`; payment detail; `POST /payments/{uuid}/refund` |
| Reports | `GET /reports/dashboard` |
| Notifications | `GET /notifications`; `POST /notifications/{uuid}/read` |

Route definitions are the source of truth in `backend/apps/*/urls.py`.

## Recurring billing and email

Celery Beat schedules the daily billing task. Its run time is controlled in
`.env`:

```dotenv
BILLING_RUN_HOUR=1
BILLING_RUN_MINUTE=0
```

The task creates invoices only for due active subscriptions, preserves the
per-period uniqueness guarantee, advances a subscription only after a
successful invoice, and saves an auditable billing-run record.

Invoice email is asynchronous by default in the example configuration. The
default email backend writes messages to backend logs. Set an SMTP email backend
and its credentials in `.env` before sending real email.

## Repository layout

```text
SaasDeck/
├── backend/
│   ├── apps/             # Feature-oriented Django apps
│   └── config/           # Settings, URLs, Celery bootstrap
├── frontend/             # React + TypeScript application
├── docs/                 # Schema, GST invoice, testing, and handoff notes
├── docker-compose.yml    # Local service orchestration
└── .env.example          # Development configuration template
```

Useful project documents:

- [Backend app ownership](docs/backend-app-ownership.md)
- [Database teammate guide](docs/database-teammate-guide.md)
- [Database schema](docs/database_schema.md)
- [GST invoice notes](docs/gst-invoice.md)
- [Invoice PDF handoff](docs/invoice-pdf-handoff.md)
- [Billing test report](docs/billing-test-report.md)
