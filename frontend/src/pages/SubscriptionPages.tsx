import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { Customer, PaginatedResponse, Plan, Subscription, SubscriptionStatus } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextAreaField, TextField, type TableColumn } from "../components/ui";

const statuses: Array<SubscriptionStatus | "ALL"> = ["ALL", "DRAFT", "QUOTATION", "CONFIRMED", "TRIAL", "ACTIVE", "PAUSED", "CANCELLED", "EXPIRED", "CLOSED"];

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

function formatDate(value: string | null) {
  return value ? new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : "—";
}

function formatMoney(value: string, currency: string) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value));
}

export function SubscriptionsPage({ portal = false }: { portal?: boolean }) {
  const token = useAccessToken();
  const [status, setStatus] = useState<SubscriptionStatus | "ALL">("ALL");
  const query = status === "ALL" ? "/subscriptions?page_size=50" : `/subscriptions?page_size=50&status=${status}`;
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["subscriptions", portal ? "portal" : "operations", status], queryFn: () => api.get<PaginatedResponse<Subscription>>(query, token) });
  const pathFor = (subscription: Subscription) => portal ? `/portal/subscriptions/${subscription.uuid}` : `/subscriptions/${subscription.uuid}`;
  const columns: TableColumn<Subscription>[] = [
    { id: "number", header: "Subscription", cell: (subscription) => <Link className="table-link" to={pathFor(subscription)}><strong>{subscription.subscription_number}</strong><small>{subscription.customer_detail.name}</small></Link> },
    { id: "plan", header: "Plan", cell: (subscription) => <><strong>{subscription.plan_detail.name}</strong><small>{formatMoney(subscription.plan_detail.price, subscription.plan_detail.currency)}</small></> },
    { id: "next-billing", header: "Next billing", cell: (subscription) => formatDate(subscription.next_billing_date) },
    { id: "expiry", header: "Expiry", cell: (subscription) => formatDate(subscription.expiry_date) },
    { id: "status", header: "Status", cell: (subscription) => <StatusBadge value={subscription.status} /> },
  ];
  const title = portal ? "My subscriptions" : "Subscriptions";
  const description = portal ? "Review the plans and billing dates for your active services." : "Create and manage recurring customer services from draft to renewal.";
  return <><PageHeader eyebrow={portal ? "Customer portal" : "Sales"} title={title} description={description} action={portal ? undefined : <div className="directory-actions"><label className="filter-field">Status<select value={status} onChange={(event) => setStatus(event.target.value as SubscriptionStatus | "ALL")}>{statuses.map((option) => <option key={option} value={option}>{option === "ALL" ? "All statuses" : option.replaceAll("_", " ")}</option>)}</select></label><Link className="button button--primary" to="/subscriptions/new">Add subscription</Link></div>} />{isLoading ? <LoadingState title="Loading subscriptions" description="Retrieving the current subscription lifecycle records." /> : null}{isError ? <ErrorState title="Could not load subscriptions" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>subscription{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label={title} columns={columns} rows={data.results} getRowKey={(subscription) => subscription.uuid} /> : <EmptyState title="No subscriptions found" description={portal ? "You do not have any subscriptions yet." : "Create a subscription once you have customers and plans ready."} action={portal ? undefined : <Link className="button button--primary" to="/subscriptions/new">Add subscription</Link>} />}</section> : null}</>;
}

const subscriptionFormSchema = z.object({
  customer: z.string().min(1, "Choose a customer."),
  plan: z.string().min(1, "Choose a plan."),
  start_date: z.string(),
  expiry_date: z.string(),
  auto_renew: z.boolean(),
}).refine((values) => !values.start_date || !values.expiry_date || values.expiry_date >= values.start_date, { message: "Expiry must be on or after the start date.", path: ["expiry_date"] });

type SubscriptionFormValues = z.infer<typeof subscriptionFormSchema>;

export function SubscriptionFormPage() {
  const token = useAccessToken();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const customersQuery = useQuery({ queryKey: ["customers", "for-subscription"], queryFn: () => api.get<PaginatedResponse<Customer>>("/customers?page_size=100", token) });
  const plansQuery = useQuery({ queryKey: ["plans", "for-subscription"], queryFn: () => api.get<PaginatedResponse<Plan>>("/plans?page_size=100&is_active=true", token) });
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<SubscriptionFormValues>({ resolver: zodResolver(subscriptionFormSchema), defaultValues: { customer: "", plan: "", start_date: "", expiry_date: "", auto_renew: true } });

  async function onSubmit(values: SubscriptionFormValues) {
    setNotice(undefined);
    try {
      const subscription = await api.post<Subscription>("/subscriptions", { customer: Number(values.customer), plan: Number(values.plan), start_date: values.start_date || null, expiry_date: values.expiry_date || null, auto_renew: values.auto_renew }, token);
      await queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      navigate(`/subscriptions/${subscription.uuid}`, { replace: true });
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "The subscription could not be created.");
    }
  }

  if (customersQuery.isLoading || plansQuery.isLoading) return <LoadingState title="Loading subscription form" description="Retrieving customers and plans." />;
  if (customersQuery.isError || plansQuery.isError) return <ErrorState title="Could not load subscription options" description={(customersQuery.error ?? plansQuery.error) instanceof ApiError ? ((customersQuery.error ?? plansQuery.error) as ApiError).message : "Please check your connection and try again."} onRetry={() => { void customersQuery.refetch(); void plansQuery.refetch(); }} />;
  const customers = customersQuery.data?.results ?? [];
  const plans = plansQuery.data?.results ?? [];
  const canCreate = customers.length > 0 && plans.length > 0;
  return <><PageHeader eyebrow="Sales" title="Add subscription" description="Start a recurring service for an existing customer and plan." action={<Link className="button button--secondary" to="/subscriptions">Back to subscriptions</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Subscription setup</h2>{canCreate ? <div className="form-grid"><label className="field"><span className="field__label">Customer</span><select className="input select-input" aria-invalid={Boolean(errors.customer)} {...register("customer")}><option value="">Choose a customer</option>{customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}{customer.company ? ` · ${customer.company}` : ""}</option>)}</select>{errors.customer ? <span className="field__error">{errors.customer.message}</span> : null}</label><label className="field"><span className="field__label">Plan</span><select className="input select-input" aria-invalid={Boolean(errors.plan)} {...register("plan")}><option value="">Choose a plan</option>{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {formatMoney(plan.price, plan.currency)}</option>)}</select>{errors.plan ? <span className="field__error">{errors.plan.message}</span> : null}</label><TextField label="Start date" type="date" {...register("start_date")} /><TextField label="Expiry date" type="date" error={errors.expiry_date?.message} {...register("expiry_date")} /><label className="checkbox-field field--wide"><input type="checkbox" {...register("auto_renew")} /> Renew automatically at the end of each billing cycle</label></div> : <EmptyState title="Customers and plans are required" description="Add at least one customer and one active plan before creating a subscription." action={<div className="page-actions"><Link className="button button--secondary" to="/customers/new">Add customer</Link><Link className="button button--primary" to="/plans/new">Add plan</Link></div>} />}</div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}{canCreate ? <div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating…" : "Create subscription"}</Button></div> : null}</form></>;
}

export function SubscriptionDetailPage({ portal = false }: { portal?: boolean }) {
  const token = useAccessToken();
  const { user } = useAuth();
  const { subscriptionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState<string>();
  const [reason, setReason] = useState("");
  const { data: subscription, isLoading, isError, error, refetch } = useQuery({ queryKey: ["subscription", subscriptionId], enabled: Boolean(subscriptionId), queryFn: () => api.get<Subscription>(`/subscriptions/${subscriptionId}`, token) });
  const actionMutation = useMutation({
    mutationFn: ({ action, cancellation_reason }: { action: "send-quotation" | "confirm" | "activate" | "pause" | "resume" | "cancel"; cancellation_reason?: string }) => api.post<Subscription>(`/subscriptions/${subscriptionId}/${action}`, cancellation_reason === undefined ? undefined : { cancellation_reason }, token),
    onSuccess: (updated) => { queryClient.setQueryData(["subscription", subscriptionId], updated); void queryClient.invalidateQueries({ queryKey: ["subscriptions"] }); setFeedback(`Subscription ${updated.status.toLowerCase()}.`); setReason(""); },
    onError: (actionError) => setFeedback(actionError instanceof ApiError ? actionError.message : "The subscription could not be updated."),
  });

  if (isLoading) return <LoadingState title="Loading subscription" description="Retrieving the subscription and billing schedule." />;
  if (isError || !subscription) return <ErrorState title="Could not load this subscription" description={error instanceof ApiError ? error.message : "The subscription is unavailable."} onRetry={() => void refetch()} />;
  const isInternal = user?.role === "admin" || user?.role === "staff";
  const listPath = portal ? "/portal/subscriptions" : "/subscriptions";
  const canSendQuotation = isInternal && subscription.status === "DRAFT";
  const canConfirm = isInternal && subscription.status === "QUOTATION";
  const canActivate = isInternal && ["CONFIRMED", "TRIAL"].includes(subscription.status);
  const canPause = isInternal && subscription.status === "ACTIVE";
  const canResume = isInternal && subscription.status === "PAUSED";
  const canCancel = isInternal && !["CANCELLED", "CLOSED", "EXPIRED"].includes(subscription.status);

  return <><PageHeader eyebrow={portal ? "Customer portal" : "Sales"} title={subscription.subscription_number} description={`${subscription.plan_detail.name} · ${subscription.customer_detail.name}`} action={<div className="page-actions"><Button type="button" tone="secondary" onClick={() => navigate(listPath)}>Back to subscriptions</Button>{canSendQuotation ? <Button type="button" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "send-quotation" })}>Send quotation</Button> : null}{canConfirm ? <Button type="button" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "confirm" })}>Confirm quotation</Button> : null}{canActivate ? <Button type="button" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "activate" })}>Activate</Button> : null}{canPause ? <Button type="button" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "pause" })}>Pause</Button> : null}{canResume ? <Button type="button" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "resume" })}>Resume</Button> : null}</div>} />{feedback ? <p className="form-alert" role="status">{feedback}</p> : null}<section className="invoice-overview"><div className="invoice-overview__status"><StatusBadge value={subscription.status} /></div><div><span>Recurring price</span><strong>{formatMoney(subscription.plan_detail.price, subscription.plan_detail.currency)}</strong></div><div><span>Next billing</span><strong>{formatDate(subscription.next_billing_date)}</strong></div><div><span>Auto-renew</span><strong>{subscription.auto_renew ? "Enabled" : "Disabled"}</strong></div></section><section className="profile-card subscription-details"><div className="profile-card__section"><h2>Service details</h2><dl className="detail-list"><div><dt>Customer</dt><dd>{subscription.customer_detail.name}<br /><small>{subscription.customer_detail.email}</small></dd></div><div><dt>Plan</dt><dd>{subscription.plan_detail.name}<br /><small>{subscription.plan_detail.code}</small></dd></div>{subscription.template_detail ? <div><dt>Quotation template</dt><dd>{subscription.template_detail.name}<br /><small>{subscription.quotation_valid_until ? `Valid until ${formatDate(subscription.quotation_valid_until)}` : ""}</small></dd></div> : null}<div><dt>Current period</dt><dd>{formatDate(subscription.current_period_start)} – {formatDate(subscription.current_period_end)}</dd></div><div><dt>Contract expiry</dt><dd>{formatDate(subscription.expiry_date)}</dd></div><div><dt>Payment terms</dt><dd>{subscription.payment_terms}</dd></div><div><dt>Created</dt><dd>{formatDate(subscription.created_at.slice(0, 10))}</dd></div></dl></div>{canCancel ? <div className="profile-card__section"><h2>Cancel subscription</h2><p className="section-copy">Record an optional reason before cancelling. This lifecycle action cannot be undone from this screen.</p><div className="form-grid"><TextAreaField label="Cancellation reason" rows={3} containerClassName="field--wide" value={reason} onChange={(event) => setReason(event.target.value)} /></div><div className="form-actions form-actions--inline"><Button type="button" tone="quiet" disabled={actionMutation.isPending} onClick={() => actionMutation.mutate({ action: "cancel", cancellation_reason: reason })}>Cancel subscription</Button></div></div> : null}</section></>;
}
