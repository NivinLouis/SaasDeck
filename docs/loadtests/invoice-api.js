import http from "k6/http";
import { check, sleep } from "k6";

// Non-mutating invoice API workload. Run only against a seeded staging environment:
// BASE_URL=https://staging.example.com/api/v1 TOKEN=<jwt> INVOICE_UUID=<uuid> \
//   k6 run docs/loadtests/invoice-api.js
//
// The script intentionally does not call POST /confirm or POST /cancel because
// those operations change invoice state. Test those flows with freshly provisioned
// draft invoices in a separate, disposable environment.

const baseUrl = (__ENV.BASE_URL || "").replace(/\/$/, "");
const token = __ENV.TOKEN || "";
const invoiceUuid = __ENV.INVOICE_UUID || "";

export const options = {
  scenarios: {
    invoice_list: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.LIST_RPS || 10),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: 10,
      maxVUs: 50,
      exec: "listInvoices",
    },
    invoice_document: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.DOCUMENT_RPS || 5),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: 5,
      maxVUs: 25,
      exec: "renderInvoice",
      startTime: "10s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:list}": ["p(95)<300"],
    "http_req_duration{endpoint:tax_invoice}": ["p(95)<800"],
    checks: ["rate>0.99"],
  },
};

function params(endpoint) {
  return {
    headers: { Authorization: `Bearer ${token}` },
    tags: { endpoint },
    timeout: "10s",
  };
}

export function setup() {
  if (!baseUrl || !token || !invoiceUuid) {
    throw new Error("BASE_URL, TOKEN, and INVOICE_UUID must be supplied.");
  }
}

export function listInvoices() {
  const response = http.get(`${baseUrl}/invoices?page_size=25`, params("list"));
  check(response, { "invoice list returns 200": (r) => r.status === 200 });
  sleep(0.1);
}

export function renderInvoice() {
  const response = http.get(`${baseUrl}/invoices/${invoiceUuid}/tax-invoice`, params("tax_invoice"));
  check(response, {
    "tax invoice returns HTML": (r) => r.status === 200 && r.headers["Content-Type"].includes("text/html"),
    "tax invoice contains heading": (r) => r.body.includes("TAX INVOICE"),
  });
  sleep(0.2);
}
