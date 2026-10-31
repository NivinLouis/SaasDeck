# Brightloop / SaasDeck Backend Foundation

> **Odoo Hackathon Project**
> A database-backed subscription management platform foundation. The backend is deliberately modular so the team can add catalog, subscriptions, billing, payments, reports, and portal features without reworking authentication or the data-access boundary.

[![Odoo](https://img.shields.io/badge/Odoo-v17.0%20%2F%20v18.0-purple?logo=odoo)](https://www.odoo.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?logo=postgresql)](https://www.postgresql.org/)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange)]()

---

## 📖 Overview

**SaasDeck** is a centralized control panel and orchestration layer designed to simplify the provisioning, lifecycle management, and monitoring of multi-tenant Odoo instances. Built for the Odoo Hackathon, it bridges developer operations with an intuitive user experience to deploy and manage SaaS environments seamlessly.

---

## What is implemented

- Django 5 + Django REST Framework project with PostgreSQL, Redis/Celery configuration, Docker Compose, health endpoint, and environment-based settings.
- Custom email-first user model with `admin`, `staff`, and `customer` roles; case-insensitive email uniqueness and Argon2 dependency.
- JWT register/login/refresh/logout, current-user endpoint, password-change endpoint, and admin-only staff creation.
- Strong server-side password validation: at least 9 characters, including uppercase, lowercase, and a special character.
- Customer billing profiles, staff/admin CRUD endpoints, and a customer-only profile endpoint. Permissions are enforced in the API, not merely hidden by the UI.
- Consistent JSON validation/error envelope, pagination, filtering, searching, ordering, Django admin, initial migrations, and regression tests for authentication and ownership boundaries.

## Deliberately left for feature branches

The foundation does **not** yet implement catalog, plans, subscriptions, invoices, payments, discounts, reporting, email, PDF generation, or scheduled billing. Add these as focused apps and call business operations from `services.py`; keep views thin and retain database constraints for financial invariants.


---

## 🛠️ Tech Stack

- **Backend / Core**: [Odoo](https://www.odoo.com) (Python 3.10+)
- **Database**: PostgreSQL
- **Containerization / Deployment**: Docker / Docker Compose

---

## Run locally

### Prerequisites

Ensure you have the following installed locally:
- **Python** 3.10 or higher
- **PostgreSQL** 14 or higher
- **Docker & Docker Compose** (optional for containerized setup)

### Local Setup

1. Copy `.env.example` to `.env` and replace the sample secrets.
2. From the repository root, start the dependencies and API:

   ```bash
   docker compose up --build
   ```

   Migrations run automatically. The API is available at `http://localhost:8000`, with `GET /health/` for a quick check.

3. To create an administrator:

   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

4. Run the tests:

   ```bash
   docker compose exec backend python manage.py test
   ```

## Foundation API

All API paths start with `/api/v1` and accept JSON.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/register` | Customer sign-up |
| POST | `/auth/login` | Return JWT access and refresh tokens |
| POST | `/auth/refresh` | Rotate a refresh token |
| POST | `/auth/logout` | Blacklist a refresh token |
| POST | `/auth/password/change` | Change the authenticated user's password |
| GET | `/me` | Authenticated user's profile and role |
| POST | `/users/staff` | Admin creates staff/admin user |
| GET | `/users` | Admin user list |
| GET, POST | `/customers` | Staff/admin list and create customers |
| GET, PATCH | `/customers/{id}` | Staff/admin customer record |
| GET, PATCH | `/portal/profile` | Customer's own billing profile |

Use `Authorization: Bearer <access-token>` for protected routes. List endpoints support `page`, `page_size`, `search`, and approved ordering/filter fields.

---

## Repository structure

```text
SaasDeck/
├── backend/
│   ├── config/           # Settings, URL composition, Celery bootstrap
│   └── apps/
│       ├── accounts/     # Custom user, JWT-facing auth, password policy
│       ├── customers/    # Customer profile and ownership boundary
│       └── core/         # Shared permissions and API error handling
├── docker-compose.yml
└── .env.example
```

The repository also contains pre-registered feature modules for `catalog`, `plans`,
`subscriptions`, `discounts`, `billing`, `payments`, `reports`, and `notifications`.
Each has dedicated models, serializers, views, services, tasks, migrations, and tests
locations so the team can build independently without collapsing business logic into
one app. See [`docs/backend-app-ownership.md`](docs/backend-app-ownership.md).
