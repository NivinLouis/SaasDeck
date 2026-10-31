import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Invoice, InvoiceLine, InvoiceStatus, PaginatedResponse } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, type TableColumn } from "../components/ui";

const invoiceStatuses: Array<InvoiceStatus | "ALL"> = ["ALL", "DRAFT", "CONFIRMED", "PAID", "CANCELLED"];
function formatMoney(value: string, currency: string) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value));
}

function getInvoiceLineColumns(currency: string): TableColumn<InvoiceLine>[] {
  return [
    { id: "description", header: "Description", cell: (line) => <strong>{line.description}</strong> },
    { id: "quantity", header: "Qty", cell: (line) => line.quantity },
    { id: "unit-price", header: "Unit price", cell: (line) => formatMoney(line.unit_price, currency) },
    { id: "discount", header: "Discount", cell: (line) => formatMoney(line.discount_amount, currency) },
    { id: "tax", header: "Tax", cell: (line) => formatMoney(line.tax_amount, currency) },
    { id: "total", header: "Line total", cell: (line) => <strong>{formatMoney(line.line_total, currency)}</strong> },
  ];
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : "—";
}

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

export function InvoicesPage() {
  const token = useAccessToken();
  const { user } = useAuth();
  const [status, setStatus] = useState<InvoiceStatus | "ALL">("ALL");
  const query = status === "ALL" ? "/invoices?page_size=25" : `/invoices?page_size=25&status=${status}`;
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["invoices", status], queryFn: () => api.get<PaginatedResponse<Invoice>>(query, token) });

  const invoiceColumns: TableColumn<Invoice>[] = [
    { id: "number", header: "Invoice", cell: (invoice) => <Link className="table-link" to={`/invoices/${invoice.uuid}`}>{invoice.invoice_number}</Link> },
    { id: "issue-date", header: "Issued", cell: (invoice) => formatDate(invoice.issue_date) },
    { id: "due-date", header: "Due", cell: (invoice) => <span className={invoice.is_overdue ? "due-date due-date--overdue" : "due-date"}>{formatDate(invoice.due_date)}</span> },
    { id: "status", header: "Status", cell: (invoice) => <StatusBadge value={invoice.status} /> },
    { id: "payment", header: "Payment", cell: (invoice) => <StatusBadge value={invoice.payment_status} /> },
    { id: "amount", header: "Amount due", cell: (invoice) => <strong>{formatMoney(invoice.amount_due, invoice.currency)}</strong> },
  ];

  const canCreate = user?.role === "admin" || user?.role === "staff";
  return <><PageHeader eyebrow="Billing" title="Invoices" description="Review invoices, due dates, and payment status from the live billing ledger." action={<div className="directory-actions"><label className="filter-field">Status<select value={status} onChange={(event) => setStatus(event.target.value as InvoiceStatus | "ALL")}>{invoiceStatuses.map((option) => <option key={option} value={option}>{option === "ALL" ? "All statuses" : option.replaceAll("_", " ")}</option>)}</select></label>{canCreate ? <Link className="button button--primary" to="/invoices/new">Create invoice</Link> : null}</div>} />{isLoading ? <LoadingState title="Loading invoices" description="Retrieving the latest billing records." /> : null}{isError ? <ErrorState title="Could not load invoices" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>invoice{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Invoices" columns={invoiceColumns} rows={data.results} getRowKey={(invoice) => invoice.uuid} /> : <EmptyState title="No invoices found" description="There are no invoices matching this status yet." />}</section> : null}</>;
}

export function InvoiceDetailPage() {
  const token = useAccessToken();
  const { user } = useAuth();
  const { invoiceUuid } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<string>();
  const { data: invoice, isLoading, isError, error, refetch } = useQuery({ queryKey: ["invoice", invoiceUuid], enabled: Boolean(invoiceUuid), queryFn: () => api.get<Invoice>(`/invoices/${invoiceUuid}`, token) });
  const updateInvoice = useMutation({
    mutationFn: (action: "confirm" | "cancel") => api.post<Invoice>(`/invoices/${invoiceUuid}/${action}`, undefined, token),
    onSuccess: (updatedInvoice) => {
      queryClient.setQueryData(["invoice", invoiceUuid], updatedInvoice);
      void queryClient.invalidateQueries({ queryKey: ["invoices"] });
      setFeedback(`Invoice ${updatedInvoice.status.toLowerCase()}.`);
    },
    onError: (actionError) => setFeedback(actionError instanceof ApiError ? actionError.message : "The invoice could not be updated."),
  });

  async function downloadPdf() {
    if (!invoice) return;
    setFeedback(undefined);
    try {
      const file = await api.download(`/invoices/${invoice.uuid}/pdf`, token);
      const fileUrl = URL.createObjectURL(file);
      const link = document.createElement("a");
      link.href = fileUrl;
      link.download = `${invoice.invoice_number}.pdf`;
      link.click();
      URL.revokeObjectURL(fileUrl);
    } catch (downloadError) {
      setFeedback(downloadError instanceof ApiError ? downloadError.message : "The PDF could not be downloaded.");
    }
  }

  async function openTaxInvoice() {
    if (!invoice) return;
    setFeedback(undefined);
    try {
      const document = await api.download(`/invoices/${invoice.uuid}/tax-invoice`, token);
      const documentUrl = URL.createObjectURL(document);
      const windowReference = window.open(documentUrl, "_blank", "noopener,noreferrer");
      if (!windowReference) setFeedback("Your browser blocked the tax invoice window. Please allow pop-ups and try again.");
      window.setTimeout(() => URL.revokeObjectURL(documentUrl), 60_000);
    } catch (downloadError) {
      setFeedback(downloadError instanceof ApiError ? downloadError.message : "The tax invoice could not be opened.");
    }
  }

  if (isLoading) return <LoadingState title="Loading invoice" description="Retrieving invoice details and line items." />;
  if (isError || !invoice) return <ErrorState title="Could not load this invoice" description={error instanceof ApiError ? error.message : "The invoice is unavailable."} onRetry={() => void refetch()} />;

  const canManage = user?.role === "admin" || user?.role === "staff";
  const canConfirm = canManage && invoice.status === "DRAFT";
  const canCancel = canManage && (invoice.status === "DRAFT" || invoice.status === "CONFIRMED");

  return <><PageHeader eyebrow="Billing" title={invoice.invoice_number} description={`Issued ${formatDate(invoice.issue_date)} · Due ${formatDate(invoice.due_date)}`} action={<div className="page-actions"><Button type="button" tone="secondary" onClick={() => navigate("/invoices")}>Back to invoices</Button><Button type="button" tone="secondary" onClick={() => void downloadPdf()}>Download PDF</Button><Button type="button" tone="secondary" onClick={() => void openTaxInvoice()}>View tax invoice</Button>{canConfirm ? <Button type="button" disabled={updateInvoice.isPending} onClick={() => updateInvoice.mutate("confirm")}>Confirm invoice</Button> : null}{canCancel ? <Button type="button" tone="quiet" disabled={updateInvoice.isPending} onClick={() => updateInvoice.mutate("cancel")}>Cancel invoice</Button> : null}</div>} />{feedback ? <p className="form-alert" role="status">{feedback}</p> : null}<section className="invoice-overview"><div className="invoice-overview__status"><StatusBadge value={invoice.status} /><StatusBadge value={invoice.payment_status} />{invoice.is_overdue ? <StatusBadge value="OVERDUE" /> : null}</div><div><span>Amount due</span><strong>{formatMoney(invoice.amount_due, invoice.currency)}</strong></div><div><span>Total</span><strong>{formatMoney(invoice.total_amount, invoice.currency)}</strong></div><div><span>Payment terms</span><strong>{invoice.payment_terms}</strong></div></section><section className="invoice-section"><h2>Invoice lines</h2><DataTable label={`${invoice.invoice_number} line items`} columns={getInvoiceLineColumns(invoice.currency)} rows={invoice.lines} getRowKey={(line) => line.id} /></section><section className="invoice-totals"><div><span>Subtotal</span><strong>{formatMoney(invoice.subtotal_amount, invoice.currency)}</strong></div><div><span>Discount</span><strong>−{formatMoney(invoice.discount_amount, invoice.currency)}</strong></div><div><span>Tax</span><strong>{formatMoney(invoice.tax_amount, invoice.currency)}</strong></div><div className="invoice-totals__total"><span>Total</span><strong>{formatMoney(invoice.total_amount, invoice.currency)}</strong></div></section></>;
}
