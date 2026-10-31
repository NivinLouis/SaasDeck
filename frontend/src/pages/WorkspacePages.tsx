import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useParams } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { Customer, PaginatedResponse } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, TextAreaField, TextField, type TableColumn } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

const customerColumns: TableColumn<Customer>[] = [
  { id: "name", header: "Name", cell: (customer) => <Link className="table-link" to={`/customers/${customer.id}`}><strong>{customer.name}</strong><small>{customer.email}</small></Link> },
  { id: "company", header: "Company", cell: (customer) => customer.company || "—" },
  { id: "contact", header: "Contact", cell: (customer) => customer.phone || "—" },
  { id: "location", header: "Location", cell: (customer) => [customer.city, customer.country].filter(Boolean).join(", ") || "—" },
];

export function WorkspaceHome() {
  const { user } = useAuth();
  return <><PageHeader eyebrow="Workspace" title={`Good to see you, ${user?.full_name.split(" ")[0] ?? "there"}.`} description="Your live reporting modules will appear here as the corresponding backend APIs are released." /><section className="welcome-card"><p className="eyebrow">Foundation ready</p><h2>Start with customers, then expand into the subscription workflow.</h2><p>This workspace deliberately avoids placeholder revenue figures. Dashboard cards will use the reports API when it is available.</p><div className="workflow-steps"><span>Customers</span><i /> <span>Catalog</span><i /> <span>Plans</span><i /> <span>Subscriptions</span><i /> <span>Billing</span></div></section></>;
}

export function CustomersPage() {
  const token = useAccessToken();
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["customers", search], queryFn: () => api.get<PaginatedResponse<Customer>>(`/customers?page_size=25${search ? `&search=${encodeURIComponent(search)}` : ""}`, token) });

  return <><PageHeader eyebrow="Customers" title="Customer directory" description="Search and manage the customer records used across subscriptions and billing." action={<div className="directory-actions"><label className="search-field"><span className="sr-only">Search customers</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search customers" /></label><Link className="button button--primary" to="/customers/new">Add customer</Link></div>} />{isLoading ? <LoadingState title="Loading customers" description="Retrieving the latest customer records." /> : null}{isError ? <ErrorState title="Could not load customers" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>customer{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Customer directory" columns={customerColumns} rows={data.results} getRowKey={(customer) => customer.id} /> : <EmptyState title="No customers found" description="Try another search term, or create a customer from the back-office API." />}</section> : null}</>;
}

const customerFormSchema = z.object({
  name: z.string().trim().min(2, "Enter the customer name."),
  company: z.string().trim(),
  email: z.string().trim().email("Enter a valid email address."),
  phone: z.string().trim(),
  billing_address: z.string().trim(),
  city: z.string().trim(),
  state: z.string().trim(),
  country: z.string().trim(),
  postal_code: z.string().trim(),
  tax_id: z.string().trim(),
});

type CustomerFormValues = z.infer<typeof customerFormSchema>;

function CustomerForm({ customer }: { customer?: Customer }) {
  const token = useAccessToken();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<CustomerFormValues>({ resolver: zodResolver(customerFormSchema), values: customer ? customerFormValues(customer) : undefined, defaultValues: customerFormValues() });

  async function onSubmit(values: CustomerFormValues) {
    setNotice(undefined);
    try {
      const saved = customer ? await api.patch<Customer>(`/customers/${customer.id}`, values, token) : await api.post<Customer>("/customers", values, token);
      queryClient.setQueryData(["customer", String(saved.id)], saved);
      await queryClient.invalidateQueries({ queryKey: ["customers"] });
      navigate(`/customers/${saved.id}`, { replace: true });
    } catch (saveError) {
      setNotice(saveError instanceof ApiError ? saveError.message : "We could not save this customer.");
    }
  }

  return <><PageHeader eyebrow="Customers" title={customer ? "Edit customer" : "Add customer"} description="Capture the contact and billing details used for subscriptions and invoices." action={<Link className="button button--secondary" to="/customers">Back to customers</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Contact details</h2><div className="form-grid"><TextField label="Customer name" autoComplete="name" error={errors.name?.message} {...register("name")} /><TextField label="Company" autoComplete="organization" {...register("company")} /><TextField label="Email address" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} /><TextField label="Phone" type="tel" autoComplete="tel" {...register("phone")} /></div></div><div className="profile-card__section"><h2>Billing details</h2><div className="form-grid"><TextAreaField label="Billing address" rows={3} containerClassName="field--wide" {...register("billing_address")} /><TextField label="City" autoComplete="address-level2" {...register("city")} /><TextField label="State" autoComplete="address-level1" {...register("state")} /><TextField label="Country" autoComplete="country-name" {...register("country")} /><TextField label="Postal code" autoComplete="postal-code" {...register("postal_code")} /><TextField label="Tax ID" {...register("tax_id")} /></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save customer"}</Button></div></form></>;
}

function customerFormValues(customer?: Customer): CustomerFormValues {
  return { name: customer?.name ?? "", company: customer?.company ?? "", email: customer?.email ?? "", phone: customer?.phone ?? "", billing_address: customer?.billing_address ?? "", city: customer?.city ?? "", state: customer?.state ?? "", country: customer?.country ?? "", postal_code: customer?.postal_code ?? "", tax_id: customer?.tax_id ?? "" };
}

export function CustomerCreatePage() {
  return <CustomerForm />;
}

export function CustomerEditPage() {
  const token = useAccessToken();
  const { customerId } = useParams();
  const query = useQuery({ queryKey: ["customer", customerId], enabled: Boolean(customerId), queryFn: () => api.get<Customer>(`/customers/${customerId}`, token) });
  if (query.isLoading) return <LoadingState title="Loading customer" description="Retrieving the customer record." />;
  if (query.isError || !query.data) return <ErrorState title="Could not load this customer" description={query.error instanceof ApiError ? query.error.message : "The customer is unavailable."} onRetry={() => void query.refetch()} />;
  return <CustomerForm customer={query.data} />;
}

type ProfileValues = Pick<Customer, "name" | "company" | "email" | "phone" | "billing_address" | "city" | "state" | "country" | "postal_code" | "tax_id">;

export function ProfilePage() {
  const token = useAccessToken();
  const [saveMessage, setSaveMessage] = useState<string>();
  const { data, isLoading, isError, error } = useQuery({ queryKey: ["portal-profile"], queryFn: () => api.get<Customer>("/portal/profile", token) });
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<ProfileValues>();

  useEffect(() => { if (data) reset(data); }, [data, reset]);

  async function onSubmit(values: ProfileValues) {
    setSaveMessage(undefined);
    try {
      await api.patch<Customer>("/portal/profile", values, token);
      setSaveMessage("Your profile has been updated.");
    } catch (saveError) {
      setSaveMessage(saveError instanceof ApiError ? saveError.message : "We could not save your profile.");
    }
  }

  if (isLoading) return <LoadingState title="Loading your profile" description="Retrieving your account details." />;
  if (isError) return <ErrorState title="Could not load your profile" description={error instanceof ApiError ? error.message : "Please sign in again and retry."} />;

  return <><PageHeader eyebrow="Customer portal" title="My profile" description="Keep your billing and contact details accurate." /><form className="profile-card" onSubmit={handleSubmit(onSubmit)}><div className="profile-card__section"><h2>Account details</h2><div className="form-grid"><TextField label="Full name" {...register("name")} /><TextField label="Company" {...register("company")} /><TextField label="Email address" type="email" {...register("email")} /><TextField label="Phone" {...register("phone")} /></div></div><div className="profile-card__section"><h2>Billing address</h2><div className="form-grid"><TextField label="Address" containerClassName="field--wide" {...register("billing_address")} /><TextField label="City" {...register("city")} /><TextField label="State" {...register("state")} /><TextField label="Country" {...register("country")} /><TextField label="Postal code" {...register("postal_code")} /><TextField label="Tax ID" {...register("tax_id")} /></div></div>{saveMessage ? <p className="form-alert">{saveMessage}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save changes"}</Button></div></form></>;
}
