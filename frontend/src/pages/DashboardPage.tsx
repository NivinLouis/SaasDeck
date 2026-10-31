import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { DashboardSummary } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

function formatMoney(value: string) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(Number(value)); }

export function DashboardPage() {
  const token = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["dashboard-summary"], queryFn: () => api.get<DashboardSummary>("/reports/dashboard", token) });
  if (isLoading) return <LoadingState title="Loading dashboard" description="Calculating live subscription and invoice totals." />;
  if (isError || !data) return <ErrorState title="Could not load dashboard" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} />;
  const active = data.subscriptions.by_status.ACTIVE ?? 0;
  return <><PageHeader eyebrow="Operations" title="Business overview" description="Live subscription health and invoice collection totals from the billing ledger." action={<Link className="button button--secondary" to="/reports">Detailed reporting</Link>} /><section className="metric-grid"><article><span>Active subscriptions</span><strong>{active}</strong><small>{data.subscriptions.total} total subscriptions</small></article><article><span>Revenue received</span><strong>{formatMoney(data.invoices.paid_total)}</strong><small>Payments applied to invoices</small></article><article><span>Outstanding amount</span><strong>{formatMoney(data.invoices.outstanding_total)}</strong><small>Across confirmed and unpaid invoices</small></article><article><span>Overdue invoices</span><strong>{data.invoices.overdue_count}</strong><small>{data.invoices.total} non-cancelled invoices</small></article></section><section className="profile-card"><div className="profile-card__section"><h2>Subscription lifecycle</h2><div className="status-summary">{Object.entries(data.subscriptions.by_status).length ? Object.entries(data.subscriptions.by_status).map(([status, count]) => <div key={status}><StatusBadge value={status} /><strong>{count}</strong></div>) : <p>No subscriptions have been created yet.</p>}</div></div></section></>;
}
