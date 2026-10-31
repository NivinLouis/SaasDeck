import { useEffect, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { BillingRun, Notification, NotificationPreference, PaginatedResponse, PaymentTerm, Product, ProductAttribute, ProductVariant } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextAreaField, TextField, type TableColumn } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

function date(value: string | null) { return value ? new Date(value).toLocaleString() : "—"; }

export function AttributesPage() {
  const token = useAccessToken();
  const attributes = useQuery({ queryKey: ["attributes"], queryFn: () => api.get<PaginatedResponse<ProductAttribute>>("/attributes?page_size=100", token) });
  const variants = useQuery({ queryKey: ["variants"], queryFn: () => api.get<PaginatedResponse<ProductVariant>>("/variants?page_size=100", token) });
  const products = useQuery({ queryKey: ["products", "variant-form"], queryFn: () => api.get<PaginatedResponse<Product>>("/products?page_size=100", token) });
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [attributeName, setAttributeName] = useState("");
  const [attributeDescription, setAttributeDescription] = useState("");
  const [variant, setVariant] = useState({ product: "", attribute: "", value: "", price_extra: "0" });

  async function createAttribute(event: FormEvent) {
    event.preventDefault(); setNotice(undefined); setSaving(true);
    try { await api.post("/attributes", { name: attributeName.trim(), description: attributeDescription.trim() || null }, token); setAttributeName(""); setAttributeDescription(""); await queryClient.invalidateQueries({ queryKey: ["attributes"] }); }
    catch (error) { setNotice(error instanceof ApiError ? error.message : "The attribute could not be saved."); }
    finally { setSaving(false); }
  }
  async function createVariant(event: FormEvent) {
    event.preventDefault(); setNotice(undefined); setSaving(true);
    try { await api.post("/variants", { product: Number(variant.product), attribute: Number(variant.attribute), value: variant.value.trim(), price_extra: variant.price_extra }, token); setVariant({ product: "", attribute: "", value: "", price_extra: "0" }); await queryClient.invalidateQueries({ queryKey: ["variants"] }); }
    catch (error) { setNotice(error instanceof ApiError ? error.message : "The variant could not be saved."); }
    finally { setSaving(false); }
  }
  if (attributes.isLoading || variants.isLoading || products.isLoading) return <LoadingState title="Loading product variants" description="Retrieving catalog attributes and values." />;
  if (attributes.isError || variants.isError || products.isError) return <ErrorState title="Could not load product variants" description="Please check your connection and try again." onRetry={() => { void attributes.refetch(); void variants.refetch(); void products.refetch(); }} />;
  const attributeRows = attributes.data?.results ?? []; const productRows = products.data?.results ?? []; const variantRows = variants.data?.results ?? [];
  const attributeById = new Map(attributeRows.map((item) => [item.id, item])); const productById = new Map(productRows.map((item) => [item.id, item]));
  const columns: TableColumn<ProductVariant>[] = [
    { id: "value", header: "Value", cell: (item) => <strong>{item.value}</strong> },
    { id: "attribute", header: "Attribute", cell: (item) => attributeById.get(item.attribute)?.name ?? `#${item.attribute}` },
    { id: "product", header: "Product", cell: (item) => productById.get(item.product)?.name ?? `#${item.product}` },
    { id: "extra", header: "Price adjustment", cell: (item) => `${Number(item.price_extra) >= 0 ? "+" : ""}${item.price_extra}` },
    { id: "price", header: "Final price", cell: (item) => item.final_price },
  ];
  return <><PageHeader eyebrow="Catalog" title="Product attributes & variants" description="Define reusable attributes, then attach priced values to products." />
    <section className="split-grid"><form className="profile-card" onSubmit={createAttribute}><div className="profile-card__section"><h2>Add attribute</h2><div className="form-grid"><TextField label="Name" value={attributeName} onChange={(event) => setAttributeName(event.target.value)} required /><TextAreaField label="Description" value={attributeDescription} onChange={(event) => setAttributeDescription(event.target.value)} rows={2} containerClassName="field--wide" /></div></div><div className="form-actions"><Button disabled={saving}>{saving ? "Saving…" : "Add attribute"}</Button></div></form>
    <form className="profile-card" onSubmit={createVariant}><div className="profile-card__section"><h2>Add variant value</h2><div className="form-grid"><label className="field"><span className="field__label">Product</span><select className="input select-input" value={variant.product} onChange={(event) => setVariant({ ...variant, product: event.target.value })} required><option value="">Select product</option>{productRows.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}</select></label><label className="field"><span className="field__label">Attribute</span><select className="input select-input" value={variant.attribute} onChange={(event) => setVariant({ ...variant, attribute: event.target.value })} required><option value="">Select attribute</option>{attributeRows.map((attribute) => <option key={attribute.id} value={attribute.id}>{attribute.name}</option>)}</select></label><TextField label="Value" value={variant.value} onChange={(event) => setVariant({ ...variant, value: event.target.value })} required /><TextField label="Price adjustment" type="number" step="0.01" value={variant.price_extra} onChange={(event) => setVariant({ ...variant, price_extra: event.target.value })} required /></div></div><div className="form-actions"><Button disabled={saving}>{saving ? "Saving…" : "Add variant"}</Button></div></form></section>
    {notice ? <p className="form-alert" role="alert">{notice}</p> : null}<section className="data-card"><div className="data-card__summary"><strong>{attributeRows.length}</strong><span>attributes · {variantRows.length} values</span></div>{variantRows.length ? <DataTable label="Product variants" rows={variantRows} columns={columns} getRowKey={(item) => item.id} /> : <EmptyState title="No variant values yet" description="Add an attribute and attach a value to a product." />}</section></>;
}

export function PaymentTermsPage() {
  const token = useAccessToken(); const { paymentTermId } = useParams(); const location = useLocation(); const editing = Boolean(paymentTermId); const navigate = useNavigate(); const queryClient = useQueryClient();
  const terms = useQuery({ queryKey: ["payment-terms"], queryFn: () => api.get<PaginatedResponse<PaymentTerm>>("/payment-terms?page_size=100", token) });
  const term = useQuery({ queryKey: ["payment-term", paymentTermId], enabled: editing, queryFn: () => api.get<PaymentTerm>(`/payment-terms/${paymentTermId}`, token) });
  const [values, setValues] = useState({ name: "", days: "0", description: "", is_active: true }); const [notice, setNotice] = useState<string>(); const [saving, setSaving] = useState(false);
  useEffect(() => { if (term.data) setValues({ name: term.data.name, days: String(term.data.days), description: term.data.description ?? "", is_active: term.data.is_active }); }, [term.data]);
  async function submit(event: FormEvent) { event.preventDefault(); setNotice(undefined); setSaving(true); try { const payload = { ...values, name: values.name.trim(), days: Number(values.days), description: values.description.trim() || null }; const saved = editing ? await api.patch<PaymentTerm>(`/payment-terms/${paymentTermId}`, payload, token) : await api.post<PaymentTerm>("/payment-terms", payload, token); await queryClient.invalidateQueries({ queryKey: ["payment-terms"] }); navigate(`/payment-terms/${saved.id}`, { replace: true }); } catch (error) { setNotice(error instanceof ApiError ? error.message : "The payment term could not be saved."); } finally { setSaving(false); } }
  if (editing && term.isLoading) return <LoadingState title="Loading payment term" description="Retrieving the payment term." />;
  if (editing && term.isError) return <ErrorState title="Could not load payment term" description="Please try again." onRetry={() => void term.refetch()} />;
  const columns: TableColumn<PaymentTerm>[] = [{ id: "name", header: "Term", cell: (item) => <Link className="table-link" to={`/payment-terms/${item.id}`}><strong>{item.name}</strong><small>{item.description || "No description"}</small></Link> }, { id: "days", header: "Due", cell: (item) => item.days ? `${item.days} days` : "Due immediately" }, { id: "status", header: "Status", cell: (item) => <StatusBadge value={item.is_active ? "ACTIVE" : "INACTIVE"} /> }];
  return <><PageHeader eyebrow="Billing" title={editing ? "Edit payment term" : "Payment terms"} description="Set the invoice due dates available to plans." action={editing ? <Link className="button button--secondary" to="/payment-terms">Back to terms</Link> : <Link className="button button--primary" to="/payment-terms/new">Add payment term</Link>} />
    {editing || location.pathname.endsWith("/new") ? <form className="profile-card" onSubmit={submit}><div className="profile-card__section"><h2>Term details</h2><div className="form-grid"><TextField label="Name" value={values.name} onChange={(event) => setValues({ ...values, name: event.target.value })} required /><TextField label="Days until due" type="number" min="0" step="1" value={values.days} onChange={(event) => setValues({ ...values, days: event.target.value })} required /><TextAreaField label="Description" rows={3} containerClassName="field--wide" value={values.description} onChange={(event) => setValues({ ...values, description: event.target.value })} /><label className="checkbox-field field--wide"><input type="checkbox" checked={values.is_active} onChange={(event) => setValues({ ...values, is_active: event.target.checked })} /> Available for new plans</label></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button disabled={saving}>{saving ? "Saving…" : "Save payment term"}</Button></div></form> : terms.isLoading ? <LoadingState title="Loading payment terms" description="Retrieving configured due dates." /> : terms.isError ? <ErrorState title="Could not load payment terms" description="Please try again." onRetry={() => void terms.refetch()} /> : <section className="data-card">{terms.data?.results.length ? <DataTable label="Payment terms" rows={terms.data.results} columns={columns} getRowKey={(item) => item.id} /> : <EmptyState title="No payment terms found" description="Add a due-date policy before assigning it to a plan." action={<Link className="button button--primary" to="/payment-terms/new">Add payment term</Link>} />}</section>}</>;
}

export function BillingRunsPage() {
  const token = useAccessToken(); const queryClient = useQueryClient(); const [notice, setNotice] = useState<string>(); const [running, setRunning] = useState(false);
  const runs = useQuery({ queryKey: ["billing-runs"], queryFn: () => api.get<PaginatedResponse<BillingRun>>("/billing/runs?page_size=50", token) });
  async function runBilling() { setNotice(undefined); setRunning(true); try { const run = await api.post<BillingRun>("/billing/run", {}, token); setNotice(`Billing run completed: ${run.invoices_created} invoice(s) created, ${run.invoices_existing} already present.`); await queryClient.invalidateQueries({ queryKey: ["billing-runs"] }); } catch (error) { setNotice(error instanceof ApiError ? error.message : "The billing run could not start."); } finally { setRunning(false); } }
  const columns: TableColumn<BillingRun>[] = [{ id: "date", header: "Run date", cell: (run) => <strong>{run.run_date}</strong> }, { id: "status", header: "Status", cell: (run) => <StatusBadge value={run.status} /> }, { id: "result", header: "Result", cell: (run) => `${run.invoices_created} created · ${run.invoices_existing} existing` }, { id: "scope", header: "Subscriptions", cell: (run) => run.subscriptions_considered }, { id: "triggered", header: "Triggered by", cell: (run) => run.triggered_by_email ?? "Scheduler" }, { id: "finished", header: "Finished", cell: (run) => date(run.finished_at) }];
  return <><PageHeader eyebrow="Billing" title="Billing run history" description="Review scheduled and manually triggered recurring-invoice runs." action={<Button type="button" onClick={() => void runBilling()} disabled={running}>{running ? "Running…" : "Run billing now"}</Button>} />{notice ? <p className="form-alert" role="status">{notice}</p> : null}{runs.isLoading ? <LoadingState title="Loading billing history" description="Retrieving the latest billing runs." /> : runs.isError ? <ErrorState title="Could not load billing history" description="Please try again." onRetry={() => void runs.refetch()} /> : <section className="data-card">{runs.data?.results.length ? <DataTable label="Billing run history" rows={runs.data.results} columns={columns} getRowKey={(run) => run.uuid} /> : <EmptyState title="No billing runs yet" description="The scheduled worker will record its first run here, or you can run billing now." />}</section>}</>;
}

export function NotificationsPage() {
  const token = useAccessToken(); const queryClient = useQueryClient();
  const notifications = useQuery({ queryKey: ["notifications"], queryFn: () => api.get<PaginatedResponse<Notification>>("/notifications?page_size=100", token) });
  const preferences = useQuery({ queryKey: ["notification-preferences"], queryFn: () => api.get<NotificationPreference>("/notifications/preferences", token) });
  async function markRead(item: Notification) { if (item.read_at) return; await api.post<Notification>(`/notifications/${item.uuid}/read`, {}, token); await queryClient.invalidateQueries({ queryKey: ["notifications"] }); }
  async function updatePreferences(patch: Partial<NotificationPreference>) { const saved = await api.patch<NotificationPreference>("/notifications/preferences", patch, token); queryClient.setQueryData(["notification-preferences"], saved); }
  const columns: TableColumn<Notification>[] = [{ id: "notification", header: "Notification", cell: (item) => <button type="button" className="table-link table-link--button" onClick={() => void markRead(item)}><strong>{item.title}</strong><small>{item.body || "No details"}</small></button> }, { id: "category", header: "Category", cell: (item) => item.category }, { id: "sent", header: "Sent", cell: (item) => date(item.created_at) }, { id: "status", header: "Status", cell: (item) => <StatusBadge value={item.read_at ? "READ" : "UNREAD"} /> }];
  return <><PageHeader eyebrow="Operations" title="Notifications" description="Review your billing, subscription, and system notifications. Select an unread item to mark it read." />{preferences.data ? <section className="profile-card"><div className="profile-card__section"><h2>Overdue invoice reminders</h2><div className="checkbox-group"><label className="checkbox-field"><input type="checkbox" checked={preferences.data.email_overdue_reminders} onChange={(event) => void updatePreferences({ email_overdue_reminders: event.target.checked })} /> Email me when an invoice becomes overdue</label><label className="checkbox-field"><input type="checkbox" checked={preferences.data.in_app_overdue_reminders} onChange={(event) => void updatePreferences({ in_app_overdue_reminders: event.target.checked })} /> Show overdue reminders in this inbox</label></div></div></section> : null}{notifications.isLoading ? <LoadingState title="Loading notifications" description="Retrieving your notification inbox." /> : notifications.isError ? <ErrorState title="Could not load notifications" description="Please try again." onRetry={() => void notifications.refetch()} /> : <section className="data-card">{notifications.data?.results.length ? <DataTable label="Notifications" rows={notifications.data.results} columns={columns} getRowKey={(item) => item.uuid} /> : <EmptyState title="No notifications" description="New billing and account notifications will appear here." />}</section>}</>;
}
