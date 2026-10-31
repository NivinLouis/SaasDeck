import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { api, ApiError } from "../api/client";
import type { Customer, PaginatedResponse } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, PageHeader, StatePanel, TextField } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

export function WorkspaceHome() {
  const { user } = useAuth();
  return <><PageHeader eyebrow="Workspace" title={`Good to see you, ${user?.full_name.split(" ")[0] ?? "there"}.`} description="Your live reporting modules will appear here as the corresponding backend APIs are released." /><section className="welcome-card"><p className="eyebrow">Foundation ready</p><h2>Start with customers, then expand into the subscription workflow.</h2><p>This workspace deliberately avoids placeholder revenue figures. Dashboard cards will use the reports API when it is available.</p><div className="workflow-steps"><span>Customers</span><i /> <span>Catalog</span><i /> <span>Plans</span><i /> <span>Subscriptions</span><i /> <span>Billing</span></div></section></>;
}

export function CustomersPage() {
  const token = useAccessToken();
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["customers", search], queryFn: () => api.get<PaginatedResponse<Customer>>(`/customers?page_size=25${search ? `&search=${encodeURIComponent(search)}` : ""}`, token) });

  return <><PageHeader eyebrow="Customers" title="Customer directory" description="Search and manage the customer records used across subscriptions and billing." action={<label className="search-field"><span className="sr-only">Search customers</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search customers" /></label>} />{isLoading ? <StatePanel title="Loading customers">Retrieving the latest customer records.</StatePanel> : null}{isError ? <StatePanel title="Could not load customers" tone="danger"><p>{error instanceof ApiError ? error.message : "Please check your connection and try again."}</p><Button type="button" tone="secondary" onClick={() => void refetch()}>Try again</Button></StatePanel> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>customer{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <div className="table-wrap"><table><thead><tr><th>Name</th><th>Company</th><th>Contact</th><th>Location</th></tr></thead><tbody>{data.results.map((customer) => <tr key={customer.id}><td><strong>{customer.name}</strong><small>{customer.email}</small></td><td>{customer.company || "—"}</td><td>{customer.phone || "—"}</td><td>{[customer.city, customer.country].filter(Boolean).join(", ") || "—"}</td></tr>)}</tbody></table></div> : <StatePanel title="No customers found">Try another search term, or create a customer from the back-office API.</StatePanel>}</section> : null}</>;
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

  if (isLoading) return <StatePanel title="Loading your profile">Retrieving your account details.</StatePanel>;
  if (isError) return <StatePanel title="Could not load your profile" tone="danger">{error instanceof ApiError ? error.message : "Please sign in again and retry."}</StatePanel>;

  return <><PageHeader eyebrow="Customer portal" title="My profile" description="Keep your billing and contact details accurate." /><form className="profile-card" onSubmit={handleSubmit(onSubmit)}><div className="profile-card__section"><h2>Account details</h2><div className="form-grid"><TextField label="Full name" {...register("name")} /><TextField label="Company" {...register("company")} /><TextField label="Email address" type="email" {...register("email")} /><TextField label="Phone" {...register("phone")} /></div></div><div className="profile-card__section"><h2>Billing address</h2><div className="form-grid"><TextField label="Address" containerClassName="field--wide" {...register("billing_address")} /><TextField label="City" {...register("city")} /><TextField label="State" {...register("state")} /><TextField label="Country" {...register("country")} /><TextField label="Postal code" {...register("postal_code")} /><TextField label="Tax ID" {...register("tax_id")} /></div></div>{saveMessage ? <p className="form-alert">{saveMessage}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Save changes"}</Button></div></form></>;
}
