import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { BillingInterval, PaginatedResponse, Plan, Product, ProductType } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextAreaField, TextField, type TableColumn } from "../components/ui";

const productTypes: Array<{ value: ProductType; label: string }> = [
  { value: "service", label: "Service" },
  { value: "consumable", label: "Consumable" },
  { value: "addon", label: "Subscription add-on" },
  { value: "storage", label: "Storage / quota" },
];

const billingIntervals: Array<{ value: BillingInterval; label: string }> = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

function formatMoney(value: string, currency = "INR") {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(Number(value));
}

function formatInterval(interval: BillingInterval, count: number) {
  return `Every ${count} ${interval}${count === 1 ? "" : "s"}`;
}

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

const productFormSchema = z.object({
  name: z.string().trim().min(2, "Enter a product name."),
  sku: z.string().trim().min(2, "Enter a SKU."),
  product_type: z.enum(["service", "consumable", "addon", "storage"]),
  sales_price: z.string().trim().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, "Enter a valid sales price."),
  cost_price: z.string().trim().refine((value) => value === "" || (!Number.isNaN(Number(value)) && Number(value) >= 0), "Enter a valid cost price."),
  description: z.string().trim(),
  is_active: z.boolean(),
});

type ProductFormValues = z.infer<typeof productFormSchema>;

function productValues(product?: Product): ProductFormValues {
  return {
    name: product?.name ?? "",
    sku: product?.sku ?? "",
    product_type: product?.product_type ?? "service",
    sales_price: product?.sales_price ?? "",
    cost_price: "",
    description: product?.description ?? "",
    is_active: product?.is_active ?? true,
  };
}

export function ProductsPage() {
  const token = useAccessToken();
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["products", search],
    queryFn: () => api.get<PaginatedResponse<Product>>(`/products?page_size=50${search ? `&search=${encodeURIComponent(search)}` : ""}`, token),
  });
  const columns: TableColumn<Product>[] = [
    { id: "name", header: "Product", cell: (product) => <Link className="table-link" to={`/products/${product.id}`}><strong>{product.name}</strong><small>{product.description || product.sku}</small></Link> },
    { id: "sku", header: "SKU", cell: (product) => product.sku },
    { id: "type", header: "Type", cell: (product) => productTypes.find((item) => item.value === product.product_type)?.label ?? product.product_type },
    { id: "price", header: "Sales price", cell: (product) => <strong>{formatMoney(product.sales_price)}</strong> },
    { id: "status", header: "Status", cell: (product) => <StatusBadge value={product.is_active ? "ACTIVE" : "INACTIVE"} /> },
  ];

  return <><PageHeader eyebrow="Catalog" title="Products" description="Manage the services and add-ons available to your plans." action={<div className="directory-actions"><label className="search-field"><span className="sr-only">Search products</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products" /></label><Link className="button button--primary" to="/products/new">Add product</Link></div>} />{isLoading ? <LoadingState title="Loading products" description="Retrieving the live product catalog." /> : null}{isError ? <ErrorState title="Could not load products" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>product{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Products" columns={columns} rows={data.results} getRowKey={(product) => product.id} /> : <EmptyState title="No products found" description="Create a product to begin building your subscription catalog." action={<Link className="button button--primary" to="/products/new">Add product</Link>} />}</section> : null}</>;
}

export function ProductFormPage() {
  const token = useAccessToken();
  const { productId } = useParams();
  const isEditing = Boolean(productId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const productQuery = useQuery({ queryKey: ["product", productId], enabled: isEditing, queryFn: () => api.get<Product>(`/products/${productId}`, token) });
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<ProductFormValues>({ resolver: zodResolver(productFormSchema), defaultValues: productValues() });

  useEffect(() => { if (productQuery.data) reset(productValues(productQuery.data)); }, [productQuery.data, reset]);

  async function onSubmit(values: ProductFormValues) {
    setNotice(undefined);
    const payload = { ...values, name: values.name.trim(), sku: values.sku.trim(), description: values.description || null, ...(values.cost_price ? {} : { cost_price: undefined }) };
    try {
      const product = isEditing ? await api.patch<Product>(`/products/${productId}`, payload, token) : await api.post<Product>("/products", payload, token);
      queryClient.setQueryData(["product", String(product.id)], product);
      await queryClient.invalidateQueries({ queryKey: ["products"] });
      navigate(`/products/${product.id}`, { replace: true });
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "The product could not be saved.");
    }
  }

  if (productQuery.isLoading) return <LoadingState title="Loading product" description="Retrieving the product details." />;
  if (productQuery.isError) return <ErrorState title="Could not load this product" description={productQuery.error instanceof ApiError ? productQuery.error.message : "The product is unavailable."} onRetry={() => void productQuery.refetch()} />;

  return <><PageHeader eyebrow="Catalog" title={isEditing ? "Edit product" : "Add product"} description="Set the product identity and pricing used by plans." action={<Link className="button button--secondary" to="/products">Back to products</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Product details</h2><div className="form-grid"><TextField label="Product name" error={errors.name?.message} {...register("name")} /><TextField label="SKU" error={errors.sku?.message} {...register("sku")} /><label className="field"><span className="field__label">Product type</span><select className="input select-input" {...register("product_type")}>{productTypes.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}</select></label><TextField label="Sales price" type="number" min="0" step="0.01" error={errors.sales_price?.message} {...register("sales_price")} /><TextField label="Cost price" type="number" min="0" step="0.01" hint={isEditing ? "Leave empty to keep the current internal cost private." : undefined} error={errors.cost_price?.message} {...register("cost_price")} /><label className="checkbox-field"><input type="checkbox" {...register("is_active")} /> Available for sale</label><TextAreaField label="Description" rows={4} containerClassName="field--wide" {...register("description")} /></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : isEditing ? "Save product" : "Create product"}</Button></div></form></>;
}

const planFormSchema = z.object({
  product: z.string().min(1, "Choose a product."),
  name: z.string().trim().min(2, "Enter a plan name."),
  code: z.string().trim().min(2, "Enter a plan code."),
  description: z.string().trim(),
  billing_interval: z.enum(["daily", "weekly", "monthly", "yearly"]),
  interval_count: z.string().refine((value) => Number.isInteger(Number(value)) && Number(value) > 0, "Use a whole number greater than zero."),
  price: z.string().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, "Enter a valid price."),
  currency: z.string().trim().length(3, "Use a three-letter currency code."),
  minimum_quantity: z.string().refine((value) => Number.isInteger(Number(value)) && Number(value) > 0, "Use a whole number greater than zero."),
  trial_period_days: z.string().refine((value) => Number.isInteger(Number(value)) && Number(value) >= 0, "Use zero or more days."),
  available_from: z.string(),
  available_until: z.string(),
  allow_pause: z.boolean(),
  allow_auto_renewal: z.boolean(),
  is_active: z.boolean(),
  is_public: z.boolean(),
});

type PlanFormValues = z.infer<typeof planFormSchema>;

function planValues(plan?: Plan): PlanFormValues {
  return { product: plan ? String(plan.product) : "", name: plan?.name ?? "", code: plan?.code ?? "", description: plan?.description ?? "", billing_interval: plan?.billing_interval ?? "monthly", interval_count: String(plan?.interval_count ?? 1), price: plan?.price ?? "", currency: plan?.currency ?? "INR", minimum_quantity: String(plan?.minimum_quantity ?? 1), trial_period_days: String(plan?.trial_period_days ?? 0), available_from: plan?.available_from ?? "", available_until: plan?.available_until ?? "", allow_pause: plan?.allow_pause ?? true, allow_auto_renewal: plan?.allow_auto_renewal ?? true, is_active: plan?.is_active ?? true, is_public: plan?.is_public ?? false };
}

export function PlansPage() {
  const token = useAccessToken();
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["plans"], queryFn: () => api.get<PaginatedResponse<Plan>>("/plans?page_size=50", token) });
  const columns: TableColumn<Plan>[] = [
    { id: "name", header: "Plan", cell: (plan) => <Link className="table-link" to={`/plans/${plan.id}`}><strong>{plan.name}</strong><small>{plan.code}</small></Link> },
    { id: "product", header: "Product", cell: (plan) => plan.product_detail.name },
    { id: "interval", header: "Billing", cell: (plan) => formatInterval(plan.billing_interval, plan.interval_count) },
    { id: "price", header: "Price", cell: (plan) => <strong>{formatMoney(plan.price, plan.currency)}</strong> },
    { id: "status", header: "Status", cell: (plan) => <StatusBadge value={plan.is_active ? "ACTIVE" : "INACTIVE"} /> },
  ];
  return <><PageHeader eyebrow="Catalog" title="Plans" description="Define the recurring pricing and lifecycle settings for subscriptions." action={<Link className="button button--primary" to="/plans/new">Add plan</Link>} />{isLoading ? <LoadingState title="Loading plans" description="Retrieving the live plan catalog." /> : null}{isError ? <ErrorState title="Could not load plans" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>plan{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Plans" columns={columns} rows={data.results} getRowKey={(plan) => plan.id} /> : <EmptyState title="No plans found" description="Create a plan after adding a product to your catalog." action={<Link className="button button--primary" to="/plans/new">Add plan</Link>} />}</section> : null}</>;
}

export function PlanFormPage() {
  const token = useAccessToken();
  const { planId } = useParams();
  const isEditing = Boolean(planId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const productsQuery = useQuery({ queryKey: ["products", "for-plan"], queryFn: () => api.get<PaginatedResponse<Product>>("/products?page_size=100", token) });
  const planQuery = useQuery({ queryKey: ["plan", planId], enabled: isEditing, queryFn: () => api.get<Plan>(`/plans/${planId}`, token) });
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<PlanFormValues>({ resolver: zodResolver(planFormSchema), defaultValues: planValues() });

  useEffect(() => { if (planQuery.data) reset(planValues(planQuery.data)); }, [planQuery.data, reset]);

  async function onSubmit(values: PlanFormValues) {
    setNotice(undefined);
    const payload = { ...values, product: Number(values.product), name: values.name.trim(), code: values.code.trim(), description: values.description || null, currency: values.currency.trim().toUpperCase(), interval_count: Number(values.interval_count), price: values.price, minimum_quantity: Number(values.minimum_quantity), trial_period_days: Number(values.trial_period_days), available_from: values.available_from || null, available_until: values.available_until || null };
    try {
      const plan = isEditing ? await api.patch<Plan>(`/plans/${planId}`, payload, token) : await api.post<Plan>("/plans", payload, token);
      queryClient.setQueryData(["plan", String(plan.id)], plan);
      await queryClient.invalidateQueries({ queryKey: ["plans"] });
      navigate(`/plans/${plan.id}`, { replace: true });
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "The plan could not be saved.");
    }
  }

  if (planQuery.isLoading || productsQuery.isLoading) return <LoadingState title="Loading plan form" description="Retrieving the products needed to configure this plan." />;
  if (planQuery.isError || productsQuery.isError) return <ErrorState title="Could not load this plan" description={(planQuery.error ?? productsQuery.error) instanceof ApiError ? ((planQuery.error ?? productsQuery.error) as ApiError).message : "Please check your connection and try again."} onRetry={() => { void planQuery.refetch(); void productsQuery.refetch(); }} />;
  const products = productsQuery.data?.results ?? [];

  return <><PageHeader eyebrow="Catalog" title={isEditing ? "Edit plan" : "Add plan"} description="Set price, billing cadence, availability, and customer lifecycle controls." action={<Link className="button button--secondary" to="/plans">Back to plans</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Plan details</h2>{products.length === 0 ? <EmptyState title="Add a product first" description="A plan must be connected to a catalog product." action={<Link className="button button--primary" to="/products/new">Add product</Link>} /> : <div className="form-grid"><label className="field"><span className="field__label">Product</span><select className="input select-input" aria-invalid={Boolean(errors.product)} {...register("product")}><option value="">Choose a product</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} · {product.sku}</option>)}</select>{errors.product ? <span className="field__error">{errors.product.message}</span> : null}</label><TextField label="Plan name" error={errors.name?.message} {...register("name")} /><TextField label="Plan code" error={errors.code?.message} {...register("code")} /><label className="field"><span className="field__label">Billing interval</span><select className="input select-input" {...register("billing_interval")}>{billingIntervals.map((interval) => <option key={interval.value} value={interval.value}>{interval.label}</option>)}</select></label><TextField label="Every" type="number" min="1" step="1" error={errors.interval_count?.message} {...register("interval_count")} /><TextField label="Price" type="number" min="0" step="0.01" error={errors.price?.message} {...register("price")} /><TextField label="Currency" maxLength={3} error={errors.currency?.message} {...register("currency")} /><TextField label="Minimum quantity" type="number" min="1" step="1" error={errors.minimum_quantity?.message} {...register("minimum_quantity")} /><TextField label="Trial period (days)" type="number" min="0" step="1" error={errors.trial_period_days?.message} {...register("trial_period_days")} /><TextField label="Available from" type="date" {...register("available_from")} /><TextField label="Available until" type="date" error={errors.available_until?.message} {...register("available_until")} /><div className="checkbox-group field--wide"><label className="checkbox-field"><input type="checkbox" {...register("allow_pause")} /> Allow customers to pause</label><label className="checkbox-field"><input type="checkbox" {...register("allow_auto_renewal")} /> Allow automatic renewal</label><label className="checkbox-field"><input type="checkbox" {...register("is_active")} /> Available for sale</label><label className="checkbox-field"><input type="checkbox" {...register("is_public")} /> Show in customer marketplace</label></div><TextAreaField label="Description" rows={4} containerClassName="field--wide" {...register("description")} /></div>}</div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}{products.length ? <div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : isEditing ? "Save plan" : "Create plan"}</Button></div> : null}</form></>;
}
