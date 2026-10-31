import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { PaginatedResponse, Plan, Subscription } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader } from "../components/ui";

function useAccessToken() { const { accessToken } = useAuth(); if (!accessToken) throw new Error("A signed-in session is required."); return accessToken; }
function money(value: string, currency: string) { return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(Number(value)); }
function benefits(plan: Plan) {
  const base: Record<string, string[]> = {
    "SAAS-CRM": ["Lead and pipeline management", "Customer follow-up automations", "Sales performance dashboard"],
    "SAAS-PROJECTS": ["Projects, tasks and due dates", "Team workload planning", "Progress and milestone reporting"],
    "SAAS-ACCOUNTING": ["Invoices and expense tracking", "GST-ready records", "Financial reporting"],
    "SAAS-HR": ["Employee directory and attendance", "Leave and payroll workflows", "Secure HR records"],
    "SAAS-AI-SUPPORT": ["AI answers around the clock", "Ticket hand-off to your team", "Support insight dashboard"],
  };
  return (plan.product_detail && base[plan.product_detail.sku]) ?? ["Secure cloud delivery", "Guided onboarding", "Flexible subscription management"];
}

export function PortalPlansPage({ embedded = false }: { embedded?: boolean }) {
  const token = useAccessToken(); const queryClient = useQueryClient(); const [requesting, setRequesting] = useState<number>(); const [notice, setNotice] = useState<string>(); const [selectedProduct, setSelectedProduct] = useState<number>();
  const plans = useQuery({ queryKey: ["portal-plans"], queryFn: () => api.get<PaginatedResponse<Plan>>("/plans?page_size=100", token) });
  const groups = useMemo(() => { const byProduct = new Map<number, { name: string; description: string | null; plans: Plan[] }>(); for (const plan of plans.data?.results ?? []) { if (plan.product === null || !plan.product_detail) continue; const group = byProduct.get(plan.product); if (group) group.plans.push(plan); else byProduct.set(plan.product, { name: plan.product_detail.name, description: plan.product_detail.description, plans: [plan] }); } return [...byProduct.entries()]; }, [plans.data]);
  const activeProduct = selectedProduct ?? groups[0]?.[0]; const product = groups.find(([id]) => id === activeProduct)?.[1];
  async function requestPlan(plan: Plan) { setNotice(undefined); setRequesting(plan.id); try { const subscription = await api.post<Subscription>("/portal/plan-requests", { plan: plan.id }, token); await queryClient.invalidateQueries({ queryKey: ["subscriptions"] }); setNotice(`${plan.name} is ready for review. Our team will send a quotation for ${subscription.subscription_number}.`); } catch (error) { setNotice(error instanceof ApiError ? error.message : "The plan request could not be sent."); } finally { setRequesting(undefined); } }
  if (plans.isLoading) return <LoadingState title="Loading software options" description="Retrieving plans currently available to you." />;
  if (plans.isError) return <ErrorState title="Could not load software options" description={plans.error instanceof ApiError ? plans.error.message : "Please try again."} onRetry={() => void plans.refetch()} />;
  if (!groups.length) return <EmptyState title="No software options available" description="There are no plans available to request right now." />;
  const catalogue = <section className="portal-storefront"><div className="portal-storefront__intro"><p className="eyebrow">SUBSCRIPTION STORE</p><h2>{embedded ? "Choose software to get started" : "Choose software for your team"}</h2><p>{product?.description || "Choose a product, compare its plans, and request a quote when you are ready."}</p></div><div className="catalogue-tabs" role="tablist" aria-label="Software products">{groups.map(([id, group]) => <button key={id} role="tab" type="button" aria-selected={activeProduct === id} className={activeProduct === id ? "is-active" : ""} onClick={() => setSelectedProduct(id)}>{group.name}</button>)}</div>{notice ? <p className="form-alert form-alert--success" role="status">{notice}</p> : null}<div className="store-plan-grid">{product?.plans.sort((a, b) => Number(a.price) - Number(b.price)).map((plan, index) => <article className={`store-plan-card ${index === 1 ? "store-plan-card--featured" : ""}`} key={plan.id}>{index === 1 ? <span className="store-plan-card__tag">Most popular</span> : null}<p>{plan.name.split(" ").at(-1)} plan</p><h3>{money(plan.price, plan.currency)}<small>/ month</small></h3><span className="store-plan-card__trial">{plan.trial_period_days ? `${plan.trial_period_days}-day trial included` : "Available now"}</span><ul>{benefits(plan).map((item) => <li key={item}><i>✓</i>{item}</li>)}</ul><div className="store-plan-card__foot"><small>{plan.minimum_quantity > 1 ? `${plan.minimum_quantity}+ seats` : "1 seat included"} · {plan.payment_term_detail?.name ?? "Due immediately"}</small><Button type="button" onClick={() => void requestPlan(plan)} disabled={requesting === plan.id}>{requesting === plan.id ? "Requesting…" : "Request quotation"}</Button></div></article>)}</div></section>;
  if (embedded) return catalogue;
  return <><PageHeader eyebrow="Customer portal" title="Software marketplace" description="Select a product, compare plans, and request a quotation with no immediate charge." action={<Link className="button button--secondary" to="/portal/subscriptions">My requests</Link>} />{catalogue}</>;
}
