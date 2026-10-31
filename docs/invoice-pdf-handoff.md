# Invoice PDF handoff

## Backend contract already available

The invoice backend owns financial values, permission checks, and historical
snapshots. The PDF implementation must not calculate amounts or query live product,
tax, or customer records.

Use this function as the only template data source:

```python
from apps.billing.services import build_invoice_pdf_context

context = build_invoice_pdf_context(invoice)
```

The returned context contains exactly these template keys:

```text
invoice.number
invoice.status
invoice.issue_date
invoice.due_date
invoice.billing_period_start / invoice.billing_period_end
invoice.currency
invoice.payment_terms
invoice.notes
invoice.subtotal_amount / discount_amount / tax_amount / total_amount
invoice.amount_paid / amount_due

customer.name / company / email / phone / billing_address / city / state
customer.country / postal_code / tax_id

lines[].description / quantity / unit_price / discount_amount
lines[].tax_rate_percent / tax_amount / line_total
```

## PDF teammate scope

Create a branch named `feature/invoice-pdf` and work in:

```text
backend/apps/billing/
├── templates/billing/invoice.html
├── pdf.py
├── tasks.py
└── tests/test_pdf.py
```

1. Add WeasyPrint to the backend dependency file if it is not already present.
2. Render `templates/billing/invoice.html` with `build_invoice_pdf_context`.
3. Store the generated PDF in `Invoice.pdf_document`.
4. Add a Celery task that generates the PDF after an invoice is confirmed.
5. Use only the snapshot data supplied by the context; never query the current
   `Product`, `Tax`, or `Customer` model while rendering a historical invoice.
6. Add a test proving the document renders and contains the invoice number and
   total from its saved snapshot.

## Existing API behaviour

```text
GET /api/v1/invoices/{uuid}      Authorized invoice detail and line data
GET /api/v1/invoices/{uuid}/pdf  Authorized PDF download
```

The PDF download endpoint returns `409` with `pdf_not_ready` before a document has
been generated. Once `Invoice.pdf_document` is stored, it streams the file. Customers
can access only their own invoices; internal staff can access all invoices.

## Do not change

The PDF branch must not change invoice totals, status transitions, database
migrations, or authorization rules without coordinating with the invoice backend owner.
