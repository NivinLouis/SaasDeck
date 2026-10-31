import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { DiscountRule, PaginatedResponse, Plan, Product, Tax } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextAreaField, TextField, type TableColumn } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

function dateTimeLocal(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

const taxSchema = z.object({
  name: z.string().trim().min(2, "Enter a tax name."),
  rate: z.string().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0 && Number(value) <= 100, "Use a rate between 0 and 100."),
  is_inclusive: z.boolean(),
  is_active: z.boolean(),
});
type TaxValues = z.infer<typeof taxSchema>;

function taxValues(tax?: Tax): TaxValues {
  return { name: tax?.name ?? "", rate: tax?.rate ?? "", is_inclusive: tax?.is_inclusive ?? false, is_active: tax?.is_active ?? true };
}

export function TaxesPage() {
  const token = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["taxes"], queryFn: () => api.get<PaginatedResponse<Tax>>("/taxes?page_size=50", token) });
  const columns: TableColumn<Tax>[] = [
    { id: "name", header: "Tax", cell: (tax) => <Link className="table-link" to={`/taxes/${tax.id}`}><strong>{tax.name}</strong><small>{tax.is_inclusive ? "Included in price" : "Added to price"}</small></Link> },
    { id: "rate", header: "Rate", cell: (tax) => <strong>{tax.rate}%</strong> },
    { id: "treatment", header: "Treatment", cell: (tax) => tax.is_inclusive ? "Inclusive" : "Exclusive" },
    { id: "status", header: "Status", cell: (tax) => <StatusBadge value={tax.is_active ? "ACTIVE" : "INACTIVE"} /> },
  ];
  return <><PageHeader eyebrow="Catalog" title="Taxes" description="Define the tax rates that can be applied to products and manual invoice lines." action={<Link className="button button--primary" to="/taxes/new">Add tax</Link>} />{isLoading ? <LoadingState title="Loading taxes" description="Retrieving the configured tax rates." /> : null}{isError ? <ErrorState title="Could not load taxes" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>tax rule{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Taxes" columns={columns} rows={data.results} getRowKey={(tax) => tax.id} /> : <EmptyState title="No tax rules found" description="Create a tax rule to apply it to products and invoices." action={<Link className="button button--primary" to="/taxes/new">Add tax</Link>} />}</section> : null}</>;
}

export function TaxFormPage() {
  const token = useAccessToken();
  const { taxId } = useParams();
  const isEditing = Boolean(taxId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const taxQuery = useQuery({ queryKey: ["tax", taxId], enabled: isEditing, queryFn: () => api.get<Tax>(`/taxes/${taxId}`, token) });
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<TaxValues>({ resolver: zodResolver(taxSchema), defaultValues: taxValues() });
  useEffect(() => { if (taxQuery.data) reset(taxValues(taxQuery.data)); }, [reset, taxQuery.data]);
  async function onSubmit(values: TaxValues) {
    setNotice(undefined);
    try {
      const tax = isEditing ? await api.patch<Tax>(`/taxes/${taxId}`, { ...values, name: values.name.trim() }, token) : await api.post<Tax>("/taxes", { ...values, name: values.name.trim() }, token);
      await queryClient.invalidateQueries({ queryKey: ["taxes"] });
      navigate(`/taxes/${tax.id}`, { replace: true });
    } catch (submitError) { setNotice(submitError instanceof ApiError ? submitError.message : "The tax rule could not be saved."); }
  }
  if (taxQuery.isLoading) return <LoadingState title="Loading tax rule" description="Retrieving tax details." />;
  if (taxQuery.isError) return <ErrorState title="Could not load this tax rule" description={taxQuery.error instanceof ApiError ? taxQuery.error.message : "The tax rule is unavailable."} onRetry={() => void taxQuery.refetch()} />;
  return <><PageHeader eyebrow="Catalog" title={isEditing ? "Edit tax" : "Add tax"} description="Configure a tax rate and how it is included in prices." action={<Link className="button button--secondary" to="/taxes">Back to taxes</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Tax details</h2><div className="form-grid"><TextField label="Tax name" error={errors.name?.message} {...register("name")} /><TextField label="Rate (%)" type="number" min="0" max="100" step="0.01" error={errors.rate?.message} {...register("rate")} /><div className="checkbox-group field--wide"><label className="checkbox-field"><input type="checkbox" {...register("is_inclusive")} /> Included in the product price</label><label className="checkbox-field"><input type="checkbox" {...register("is_active")} /> Active</label></div></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save tax rule"}</Button></div></form></>;
}

const discountSchema = z.object({
  code: z.string().trim().min(2, "Enter a code."),
  name: z.string().trim().min(2, "Enter a name."),
  description: z.string().trim(),
  discount_type: z.enum(["PERCENTAGE", "FIXED_AMOUNT"]),
  value: z.string().refine((value) => Number(value) > 0, "Enter a value greater than zero."),
  scope: z.enum(["SUBSCRIPTION", "PRODUCTS", "PLANS"]),
  minimum_purchase_amount: z.string().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, "Enter zero or more."),
  minimum_quantity: z.string().refine((value) => Number.isInteger(Number(value)) && Number(value) >= 1, "Use a whole number of at least 1."),
  valid_from: z.string().min(1, "Select a start date."),
  valid_until: z.string(),
  max_uses: z.string(),
  is_active: z.boolean(),
  applicable_products: z.array(z.string()),
  applicable_plans: z.array(z.string()),
}).superRefine((values, context) => {
  if (values.discount_type === "PERCENTAGE" && Number(values.value) > 100) context.addIssue({ code: "custom", path: ["value"], message: "Percentage cannot exceed 100." });
  if (values.valid_until && values.valid_until < values.valid_from) context.addIssue({ code: "custom", path: ["valid_until"], message: "Expiry must follow the start date." });
  if (values.scope === "PRODUCTS" && !values.applicable_products.length) context.addIssue({ code: "custom", path: ["applicable_products"], message: "Select at least one product." });
  if (values.scope === "PLANS" && !values.applicable_plans.length) context.addIssue({ code: "custom", path: ["applicable_plans"], message: "Select at least one plan." });
});
type DiscountValues = z.infer<typeof discountSchema>;

function defaultDateTime() { return dateTimeLocal(new Date().toISOString()); }
function discountValues(discount?: DiscountRule): DiscountValues {
  return { code: discount?.code ?? "", name: discount?.name ?? "", description: discount?.description ?? "", discount_type: discount?.discount_type ?? "PERCENTAGE", value: discount?.value ?? "", scope: discount?.scope ?? "SUBSCRIPTION", minimum_purchase_amount: discount?.minimum_purchase_amount ?? "0", minimum_quantity: String(discount?.minimum_quantity ?? 1), valid_from: dateTimeLocal(discount?.valid_from) || defaultDateTime(), valid_until: dateTimeLocal(discount?.valid_until), max_uses: discount?.max_uses ? String(discount.max_uses) : "", is_active: discount?.is_active ?? true, applicable_products: discount?.applicable_products.map(String) ?? [], applicable_plans: discount?.applicable_plans.map(String) ?? [] };
}

export function DiscountsPage() {
  const token = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["discounts"], queryFn: () => api.get<PaginatedResponse<DiscountRule>>("/discounts?page_size=50", token) });
  const columns: TableColumn<DiscountRule>[] = [
    { id: "code", header: "Code", cell: (rule) => <Link className="table-link" to={`/discounts/${rule.uuid}`}><strong>{rule.code}</strong><small>{rule.name}</small></Link> },
    { id: "value", header: "Discount", cell: (rule) => <strong>{rule.discount_type === "PERCENTAGE" ? `${rule.value}%` : `₹${rule.value}`}</strong> },
    { id: "scope", header: "Scope", cell: (rule) => rule.scope === "SUBSCRIPTION" ? "Entire subscription" : rule.scope === "PRODUCTS" ? "Selected products" : "Selected plans" },
    { id: "uses", header: "Uses", cell: (rule) => `${rule.times_used}${rule.max_uses === null ? "" : ` / ${rule.max_uses}`}` },
    { id: "status", header: "Status", cell: (rule) => <StatusBadge value={rule.is_active ? "ACTIVE" : "INACTIVE"} /> },
  ];
  return <><PageHeader eyebrow="Pricing" title="Discounts" description="Manage validated discount rules for selected plans, products, or subscriptions." action={<Link className="button button--primary" to="/discounts/new">Add discount</Link>} />{isLoading ? <LoadingState title="Loading discounts" description="Retrieving discount rules." /> : null}{isError ? <ErrorState title="Could not load discounts" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>discount rule{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Discount rules" columns={columns} rows={data.results} getRowKey={(rule) => rule.uuid} /> : <EmptyState title="No discounts found" description="Create a rule to offer a targeted discount." action={<Link className="button button--primary" to="/discounts/new">Add discount</Link>} />}</section> : null}</>;
}

export function DiscountFormPage() {
  const token = useAccessToken();
  const { discountId } = useParams();
  const isEditing = Boolean(discountId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const discountQuery = useQuery({ queryKey: ["discount", discountId], enabled: isEditing, queryFn: () => api.get<DiscountRule>(`/discounts/${discountId}`, token) });
  const productsQuery = useQuery({ queryKey: ["products", "for-discount"], queryFn: () => api.get<PaginatedResponse<Product>>("/products?page_size=100", token) });
  const plansQuery = useQuery({ queryKey: ["plans", "for-discount"], queryFn: () => api.get<PaginatedResponse<Plan>>("/plans?page_size=100", token) });
  const { register, handleSubmit, reset, watch, formState: { errors, isSubmitting } } = useForm<DiscountValues>({ resolver: zodResolver(discountSchema), defaultValues: discountValues() });
  const scope = watch("scope");
  useEffect(() => { if (discountQuery.data) reset(discountValues(discountQuery.data)); }, [discountQuery.data, reset]);
  async function onSubmit(values: DiscountValues) {
    setNotice(undefined);
    const payload = { ...values, code: values.code.trim(), name: values.name.trim(), description: values.description || null, value: values.value, minimum_purchase_amount: values.minimum_purchase_amount, minimum_quantity: Number(values.minimum_quantity), valid_from: new Date(values.valid_from).toISOString(), valid_until: values.valid_until ? new Date(values.valid_until).toISOString() : null, max_uses: values.max_uses ? Number(values.max_uses) : null, applicable_products: values.scope === "PRODUCTS" ? values.applicable_products.map(Number) : [], applicable_plans: values.scope === "PLANS" ? values.applicable_plans.map(Number) : [] };
    try {
      const discount = isEditing ? await api.patch<DiscountRule>(`/discounts/${discountId}`, payload, token) : await api.post<DiscountRule>("/discounts", payload, token);
      await queryClient.invalidateQueries({ queryKey: ["discounts"] });
      navigate(`/discounts/${discount.uuid}`, { replace: true });
    } catch (submitError) { setNotice(submitError instanceof ApiError ? submitError.message : "The discount could not be saved."); }
  }
  if (discountQuery.isLoading || productsQuery.isLoading || plansQuery.isLoading) return <LoadingState title="Loading discount form" description="Retrieving products and plans." />;
  if (discountQuery.isError || productsQuery.isError || plansQuery.isError) return <ErrorState title="Could not load the discount form" description={(discountQuery.error ?? productsQuery.error ?? plansQuery.error) instanceof ApiError ? ((discountQuery.error ?? productsQuery.error ?? plansQuery.error) as ApiError).message : "Please check your connection and try again."} onRetry={() => { void discountQuery.refetch(); void productsQuery.refetch(); void plansQuery.refetch(); }} />;
  const products = productsQuery.data?.results ?? []; const plans = plansQuery.data?.results ?? [];
  return <><PageHeader eyebrow="Pricing" title={isEditing ? "Edit discount" : "Add discount"} description="Set discount eligibility, validity, and usage constraints." action={<Link className="button button--secondary" to="/discounts">Back to discounts</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Rule details</h2><div className="form-grid"><TextField label="Discount code" error={errors.code?.message} {...register("code")} /><TextField label="Rule name" error={errors.name?.message} {...register("name")} /><label className="field"><span className="field__label">Discount type</span><select className="input select-input" {...register("discount_type")}><option value="PERCENTAGE">Percentage</option><option value="FIXED_AMOUNT">Fixed amount</option></select></label><TextField label="Value" type="number" min="0.01" step="0.01" error={errors.value?.message} {...register("value")} /><label className="field"><span className="field__label">Applies to</span><select className="input select-input" {...register("scope")}><option value="SUBSCRIPTION">Entire subscription</option><option value="PRODUCTS">Specific products</option><option value="PLANS">Specific plans</option></select></label><TextField label="Minimum purchase amount" type="number" min="0" step="0.01" error={errors.minimum_purchase_amount?.message} {...register("minimum_purchase_amount")} /><TextField label="Minimum quantity" type="number" min="1" step="1" error={errors.minimum_quantity?.message} {...register("minimum_quantity")} /><TextField label="Starts" type="datetime-local" error={errors.valid_from?.message} {...register("valid_from")} /><TextField label="Ends" type="datetime-local" error={errors.valid_until?.message} {...register("valid_until")} /><TextField label="Maximum uses" type="number" min="1" step="1" hint="Leave blank for unlimited." {...register("max_uses")} />{scope === "PRODUCTS" ? <label className="field field--wide"><span className="field__label">Eligible products</span><select className="input select-input select-input--multiple" multiple size={Math.min(5, Math.max(2, products.length))} {...register("applicable_products")} >{products.map((product) => <option key={product.id} value={product.id}>{product.name} · {product.sku}</option>)}</select>{errors.applicable_products ? <span className="field__error">{errors.applicable_products.message}</span> : null}</label> : null}{scope === "PLANS" ? <label className="field field--wide"><span className="field__label">Eligible plans</span><select className="input select-input select-input--multiple" multiple size={Math.min(5, Math.max(2, plans.length))} {...register("applicable_plans")}>{plans.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {plan.code}</option>)}</select>{errors.applicable_plans ? <span className="field__error">{errors.applicable_plans.message}</span> : null}</label> : null}<div className="checkbox-group field--wide"><label className="checkbox-field"><input type="checkbox" {...register("is_active")} /> Active</label></div><TextAreaField label="Description" rows={3} containerClassName="field--wide" {...register("description")} /></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save discount"}</Button></div></form></>;
}
