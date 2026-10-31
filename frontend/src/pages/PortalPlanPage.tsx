import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { PaginatedResponse, Plan, Subscription } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge } from "../components/ui";

function useAccessToken() { const { accessToken } = useAuth(); if (!accessToken) throw new Error("A signed-in session is required."); return accessToken; }
function money(value: string, currency: string) { return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value)); }

export function PortalPlansPage() {
  const token = useAccessToken(); const queryClient = useQueryClient(); const [requesting, setRequesting] = useState<number>(); const [notice, setNotice] = useState<string>();
  const plans = useQuery({ queryKey: ["portal-plans"], queryFn: () => api.get<PaginatedResponse<Plan>>("/plans?page_size=100", token) });
  async function requestPlan(plan: Plan) { setNotice(undefined); setRequesting(plan.id); try { const subscription = await api.post<Subscription>("/portal/plan-requests", { plan: plan.id }, token); await queryClient.invalidateQueries({ queryKey: ["subscriptions"] }); setNotice(`${plan.name} has been requested. Our team will send a quotation for ${subscription.subscription_number}.`); } catch (error) { setNotice(error instanceof ApiError ? error.message : "The plan request could not be sent."); } finally { setRequesting(undefined); } }
  if (plans.isLoading) return <LoadingState title="Loading plans" description="Retrieving plans currently available to you." />;
  if (plans.isError) return <ErrorState title="Could not load plans" description={plans.error instanceof ApiError ? plans.error.message : "Please try again."} onRetry={() => void plans.refetch()} />;
  const rows = plans.data?.results ?? [];
  return <><PageHeader eyebrow="Customer portal" title="Choose a plan" description="Request a quotation for a plan that suits your subscription needs." action={<Link className="button button--secondary" to="/portal/subscriptions">My requests</Link>} />{notice ? <p className="form-alert" role="status">{notice}</p> : null}{rows.length ? <section className="card-grid">{rows.map((plan) => <article className="profile-card" key={plan.id}><div className="profile-card__section"><p className="eyebrow">{plan.product_detail.name}</p><h2>{plan.name}</h2><p>{plan.description || `${plan.interval_count} ${plan.billing_interval} billing plan`}</p><strong className="plan-price">{money(plan.price, plan.currency)}</strong><p>{plan.interval_count === 1 ? "Every" : `Every ${plan.interval_count}`} {plan.billing_interval}{plan.interval_count === 1 ? "" : "s"}</p><div className="status-summary"><div><StatusBadge value="AVAILABLE" /><strong>{plan.payment_term_detail ? `${plan.payment_term_detail.name} · ${plan.payment_term_detail.days} days` : "Due immediately"}</strong></div></div></div><div className="form-actions"><Button type="button" onClick={() => void requestPlan(plan)} disabled={requesting === plan.id}>{requesting === plan.id ? "Requesting…" : "Request quotation"}</Button></div></article>)}</section> : <EmptyState title="No plans available" description="There are no plans available to request right now." />}</>;
}
