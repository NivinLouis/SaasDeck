# Billing invoice test report

**Scope:** invoice list/detail access, confirmation lifecycle, PDF handoff, GST tax-invoice HTML rendering, and non-mutating API load testing.

**Revision:** `f557bed` (`main`)  
**Prepared:** 31 October 2026

## Automated coverage in the repository

The billing suite contains nine tests.

| Area | Coverage |
| --- | --- |
| Invoice visibility | A customer receives only their own invoice. |
| Permission boundary | A customer cannot confirm an invoice. |
| Confirmation | Staff confirmation recalculates totals and captures the customer snapshot used by document rendering. |
| PDF handoff | The private PDF endpoint returns `409 pdf_not_ready` until a generated PDF is attached. |
| GST rendering | Intra-state supply splits GST into CGST and SGST; inter-state supply uses IGST. |
| GST validation | An invoice missing an HSN/SAC cannot be rendered as a final tax invoice. |

## Current verification result

| Check | Result | Evidence |
| --- | --- | --- |
| Django system check | Passed | No system-check issues were reported during the invoice implementation. |
| Migration consistency | Passed | `makemigrations --check --dry-run` reported no model changes. |
| GST HTML render | Passed | A populated intra-state invoice rendered successfully and contained `TAX INVOICE` and CGST content. |
| Full billing test suite | Not run in this session | The isolated container test run was not authorized. No pass/fail metric is claimed. |
| HTTP load test | Not run in this session | Requires a staging URL, a JWT, and a confirmed invoice with complete GST data. |

Run the full billing suite with an isolated database:

```bash
docker compose run --rm --no-deps \
  -e DATABASE_URL=sqlite:////tmp/saasdeck_billing_tests.sqlite \
  backend python manage.py test apps.billing.tests --verbosity 1
```

## Load-test design

The reproducible k6 workload is [loadtests/invoice-api.js](loadtests/invoice-api.js). It runs two read-only flows after a 10-second ramp overlap:

| Flow | Default rate | Why it matters |
| --- | ---: | --- |
| `GET /invoices?page_size=25` | 10 requests/sec | Measures the common authenticated billing-list view. |
| `GET /invoices/{uuid}/tax-invoice` | 5 requests/sec | Measures the HTML invoice rendering path used before PDF export. |

Suggested acceptance thresholds:

- Error rate under 1%.
- Invoice-list p95 under 300 ms.
- Tax-invoice HTML p95 under 800 ms.
- More than 99% of request checks successful.

### Prerequisites

1. Use a staging environment, never production.
2. Seed at least 100 invoices for the test customer and choose one confirmed invoice with complete supplier/recipient snapshots, HSN/SAC, UQC, place of supply, and GSTIN.
3. Obtain a customer or staff JWT appropriate to the data set.
4. Install [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/).

### Run

```bash
BASE_URL=https://staging.example.com/api/v1 \
TOKEN='<JWT>' \
INVOICE_UUID='<confirmed-invoice-uuid>' \
LIST_RPS=10 DOCUMENT_RPS=5 DURATION=2m \
k6 run docs/loadtests/invoice-api.js
```

Save the k6 terminal summary, environment size, database sizing, and revision SHA with any measured figures. A successful functional test does not establish production capacity; repeat the run while observing database CPU, query latency, memory, and application error logs.

## Known boundaries

- The load test deliberately avoids confirm/cancel endpoints because they mutate financial state. Exercise those only in a disposable environment with a fresh-invoice provisioning step.
- The tax-invoice HTML endpoint rejects incomplete GST data. A `400` response in the load test normally means bad seed data, not capacity failure.
- PDF byte generation is a later handoff stage; this workload measures HTML document generation and the existing PDF-readiness endpoint separately.
