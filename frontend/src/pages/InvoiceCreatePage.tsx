import { useEffect, useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { Customer, Invoice, PaginatedResponse, Product, Tax } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, TextAreaField, TextField } from "../components/ui";

function useAccessToken() { const { accessToken } = useAuth(); if (!accessToken) throw new Error("A signed-in session is required."); return accessToken; }

const invoiceSchema = z.object({
  customer: z.string().min(1, "Choose a customer."),
  issue_date: z.string(),
  due_date: z.string().min(1, "Choose a due date."),
  product: z.string(),
  description: z.string().trim().min(2, "Enter a description."),
  quantity: z.string().refine((value) => Number.isInteger(Number(value)) && Number(value) >= 1, "Use a whole number of at least 1."),
  unit_price: z.string().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, "Enter a valid price."),
  discount_amount: z.string().refine((value) => !Number.isNaN(Number(value)) && Number(value) >= 0, "Enter zero or more."),
  tax_rule: z.string(),
  notes: z.string().trim(),
});
type InvoiceValues = z.infer<typeof invoiceSchema>;

export function InvoiceCreatePage() {
  const token = useAccessToken(); const navigate = useNavigate(); const queryClient = useQueryClient(); const [notice, setNotice] = useState<string>();
  const customersQuery = useQuery({ queryKey: ["customers", "for-invoice"], queryFn: () => api.get<PaginatedResponse<Customer>>("/customers?page_size=100", token) });
  const productsQuery = useQuery({ queryKey: ["products", "for-invoice"], queryFn: () => api.get<PaginatedResponse<Product>>("/products?page_size=100&is_active=true", token) });
  const taxesQuery = useQuery({ queryKey: ["taxes", "for-invoice"], queryFn: () => api.get<PaginatedResponse<Tax>>("/taxes?page_size=100&is_active=true", token) });
  const { register, handleSubmit, watch, setValue, formState: { errors, isSubmitting } } = useForm<InvoiceValues>({ resolver: zodResolver(invoiceSchema), defaultValues: { customer: "", issue_date: new Date().toISOString().slice(0, 10), due_date: "", product: "", description: "", quantity: "1", unit_price: "", discount_amount: "0", tax_rule: "", notes: "" } });
  const productId = watch("product"); const selectedProduct = productsQuery.data?.results.find((product) => String(product.id) === productId);
  useEffect(() => { if (selectedProduct) { setValue("description", selectedProduct.name); setValue("unit_price", selectedProduct.sales_price); setValue("tax_rule", selectedProduct.applied_taxes[0] ? String(selectedProduct.applied_taxes[0].id) : ""); } }, [selectedProduct, setValue]);
  async function onSubmit(values: InvoiceValues) {
    setNotice(undefined);
    const tax = taxesQuery.data?.results.find((item) => String(item.id) === values.tax_rule);
    try {
      const invoice = await api.post<Invoice>("/invoices", { customer: Number(values.customer), issue_date: values.issue_date || undefined, due_date: values.due_date, notes: values.notes, lines: [{ product: values.product ? Number(values.product) : null, description: values.description, quantity: Number(values.quantity), unit_price: values.unit_price, discount_amount: values.discount_amount, tax_rule: values.tax_rule ? Number(values.tax_rule) : null, tax_rate_percent: tax?.rate ?? "0" }] }, token);
      await queryClient.invalidateQueries({ queryKey: ["invoices"] }); navigate(`/invoices/${invoice.uuid}`, { replace: true });
    } catch (submitError) { setNotice(submitError instanceof ApiError ? submitError.message : "The invoice could not be created."); }
  }
  if (customersQuery.isLoading || productsQuery.isLoading || taxesQuery.isLoading) return <LoadingState title="Loading invoice form" description="Retrieving customers, products, and taxes." />;
  if (customersQuery.isError || productsQuery.isError || taxesQuery.isError) return <ErrorState title="Could not load invoice options" description={(customersQuery.error ?? productsQuery.error ?? taxesQuery.error) instanceof ApiError ? ((customersQuery.error ?? productsQuery.error ?? taxesQuery.error) as ApiError).message : "Please check your connection and try again."} onRetry={() => { void customersQuery.refetch(); void productsQuery.refetch(); void taxesQuery.refetch(); }} />;
  const customers = customersQuery.data?.results ?? []; const products = productsQuery.data?.results ?? []; const taxes = taxesQuery.data?.results ?? [];
  if (!customers.length) return <><PageHeader eyebrow="Billing" title="Create invoice" description="Create a draft manual invoice for a customer." action={<Link className="button button--secondary" to="/invoices">Back to invoices</Link>} /><EmptyState title="Add a customer first" description="Manual invoices need a customer billing record." action={<Link className="button button--primary" to="/customers/new">Add customer</Link>} /></>;
  return <><PageHeader eyebrow="Billing" title="Create invoice" description="Create a draft manual invoice with one product or service line." action={<Link className="button button--secondary" to="/invoices">Back to invoices</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Invoice details</h2><div className="form-grid"><label className="field"><span className="field__label">Customer</span><select className="input select-input" {...register("customer")}><option value="">Choose a customer</option>{customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name}</option>)}</select>{errors.customer ? <span className="field__error">{errors.customer.message}</span> : null}</label><TextField label="Issue date" type="date" {...register("issue_date")} /><TextField label="Due date" type="date" error={errors.due_date?.message} {...register("due_date")} /><label className="field"><span className="field__label">Catalog product</span><select className="input select-input" {...register("product")}><option value="">Custom line item</option>{products.map((product) => <option key={product.id} value={product.id}>{product.name} · {product.sku}</option>)}</select></label><TextField label="Description" error={errors.description?.message} {...register("description")} /><TextField label="Quantity" type="number" min="1" step="1" error={errors.quantity?.message} {...register("quantity")} /><TextField label="Unit price" type="number" min="0" step="0.01" error={errors.unit_price?.message} {...register("unit_price")} /><TextField label="Discount amount" type="number" min="0" step="0.01" error={errors.discount_amount?.message} {...register("discount_amount")} /><label className="field"><span className="field__label">Tax</span><select className="input select-input" {...register("tax_rule")}><option value="">No tax</option>{taxes.map((tax) => <option key={tax.id} value={tax.id}>{tax.name} · {tax.rate}%</option>)}</select></label><TextAreaField label="Notes" rows={3} containerClassName="field--wide" {...register("notes")} /></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating…" : "Create draft invoice"}</Button></div></form></>;
}
