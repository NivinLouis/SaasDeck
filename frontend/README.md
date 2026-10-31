# SaasDeck frontend

The Vite + React + TypeScript client for SaasDeck. It is intentionally feature-based and connects to the Django REST API; it does not use mock production data.

## Run locally

1. Copy `.env.example` to `.env` if the API is not served from `http://localhost:8000/api/v1`.
2. Install dependencies with `npm install`.
3. Run `npm run dev` and open `http://localhost:5173`.

The backend must allow `http://localhost:5173` through `DJANGO_CORS_ALLOWED_ORIGINS`.

## Current routes

- `/login` - JWT sign-in
- `/register` - customer registration
- `/customers` - staff/admin customer directory
- `/portal/profile` - customer profile editing

Access tokens and refresh tokens are kept in memory only. A browser refresh ends the session until the backend offers an HttpOnly cookie refresh-token contract.
