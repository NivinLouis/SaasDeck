# GST tax-invoice document

`GET /api/v1/invoices/{invoice_uuid}/tax-invoice` renders a print-ready A4 HTML tax invoice. It is the single document source for a later PDF worker; do not maintain a separate PDF layout.

The endpoint only renders an invoice that is `CONFIRMED` or `PAID`, has at least one line, and includes the Rule 46 fields used by the template: supplier identity/GSTIN, invoice number and date, recipient identity/address, HSN/SAC, quantity/UQC, taxable value, GST rate and amounts, place of supply, reverse-charge status, and an authorised signatory. It returns a validation response rather than showing an incomplete document as a tax invoice.

Set the issuer values in the environment before issuing any invoice:

```text
GST_INVOICE_SUPPLIER_LEGAL_NAME=SaaSDeck Technologies Private Limited
GST_INVOICE_SUPPLIER_ADDRESS=...
GST_INVOICE_SUPPLIER_GSTIN=...
GST_INVOICE_SUPPLIER_STATE_NAME=Kerala
GST_INVOICE_SUPPLIER_STATE_CODE=32
GST_INVOICE_AUTHORISED_SIGNATORY=...
```

The model stores seller, recipient and place-of-supply values on the invoice as snapshots. Call `populate_invoice_gst_snapshots(invoice)` while the invoice is still a draft, then save it before confirmation; final documents never read mutable customer or application settings values. GSTIN format, HSN/SAC, and party details are validated at publication time. When the supplier is covered by e-invoicing, populate the IRN and acknowledgement fields after IRP registration and add the signed QR payload/asset in the planned PDF/export step.

The layout determines CGST+SGST versus IGST from the supplier state code and place-of-supply state code. Confirm those values with the tax team for any special place-of-supply, reverse-charge, export, SEZ, bill-to/ship-to, or e-invoicing case. The implementation follows the particulars specified by [CGST Rules, 2017 Rule 46](https://cbic-gst.gov.in/gst-invoice-rules.html); there is no single mandated visual format.
