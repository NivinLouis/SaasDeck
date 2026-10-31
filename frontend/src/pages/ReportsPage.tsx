import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import type { DashboardSummary } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, ErrorState, LoadingState, PageHeader, StatusBadge, TextField, type TableColumn } from "../components/ui";

function useAccessToken() { const { accessToken } = useAuth(); if (!accessToken) throw new Error("A signed-in session is required."); return accessToken; }
function money(value: string) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(Number(value)); }
function queryFor(start: string, end: string) { const query = new URLSearchParams(); if (start) query.set("start_date", start); if (end) query.set("end_date", end); return query.toString() ? `?${query}` : ""; }

export function ReportsPage() {
  const token = useAccessToken(); const [startDate, setStartDate] = useState(""); const [endDate, setEndDate] = useState(""); const [applied, setApplied] = useState({ start: "", end: "" }); const [downloading, setDownloading] = useState(false);
  const report = useQuery({ queryKey: ["reports", applied], queryFn: () => api.get<DashboardSummary>(`/reports/dashboard${queryFor(applied.start, applied.end)}`, token) });
  async function exportCsv() { setDownloading(true); try { const blob = await api.download(`/reports/invoices.csv${queryFor(applied.start, applied.end)}`, token); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "invoice-report.csv"; link.click(); URL.revokeObjectURL(url); } finally { setDownloading(false); } }
  if (report.isLoading) return <LoadingState title="Loading reports" description="Aggregating billing performance from the ledger." />;
  if (report.isError || !report.data) return <ErrorState title="Could not load reports" description={report.error instanceof ApiError ? report.error.message : "Please check your connection and try again."} onRetry={() => void report.refetch()} />;
  const columns: TableColumn<NonNullable<DashboardSummary["trend"]>[number]>[] = [{ id: "month", header: "Month", cell: (item) => new Date(item.month).toLocaleDateString(undefined, { month: "long", year: "numeric" }) }, { id: "invoices", header: "Invoices", cell: (item) => item.invoice_count }, { id: "billed", header: "Billed", cell: (item) => money(item.invoiced_total) }, { id: "paid", header: "Collected", cell: (item) => money(item.paid_total) }];
  return <><PageHeader eyebrow="Reporting" title="Billing performance" description="Filter ledger totals, inspect monthly trends, and export the matching invoice rows." action={<Button type="button" tone="secondary" onClick={() => void exportCsv()} disabled={downloading}>{downloading ? "Exporting…" : "Export CSV"}</Button>} />
    <form className="profile-card" onSubmit={(event) => { event.preventDefault(); setApplied({ start: startDate, end: endDate }); }}><div className="profile-card__section"><div className="form-grid"><TextField label="From" type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /><TextField label="To" type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></div></div><div className="form-actions"><Button>Apply date range</Button></div></form>
    <section className="metric-grid"><article><span>Invoices</span><strong>{report.data.invoices.total}</strong><small>Non-cancelled in range</small></article><article><span>Collected</span><strong>{money(report.data.invoices.paid_total)}</strong><small>Applied payments</small></article><article><span>Outstanding</span><strong>{money(report.data.invoices.outstanding_total)}</strong><small>Still due</small></article><article><span>Overdue</span><strong>{report.data.invoices.overdue_count}</strong><small>Past their due date</small></article></section>
    <section className="profile-card"><div className="profile-card__section"><h2>Subscription lifecycle</h2><div className="status-summary">{Object.entries(report.data.subscriptions.by_status).map(([status, count]) => <div key={status}><StatusBadge value={status} /><strong>{count}</strong></div>)}</div></div></section>
    <section className="data-card"><div className="data-card__summary"><strong>{report.data.trend?.length ?? 0}</strong><span>monthly reporting periods</span></div>{report.data.trend?.length ? <DataTable label="Monthly billing trend" rows={report.data.trend} columns={columns} getRowKey={(item) => item.month} /> : <p className="empty-table-message">No invoice activity matches this date range.</p>}</section></>;
}
