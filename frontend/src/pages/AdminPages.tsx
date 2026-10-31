import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import type { PaginatedResponse, User } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { Button, DataTable, EmptyState, ErrorState, LoadingState, PageHeader, StatusBadge, TextField, type TableColumn } from "../components/ui";

function useAccessToken() {
  const { accessToken } = useAuth();
  if (!accessToken) throw new Error("A signed-in session is required.");
  return accessToken;
}

export function TeamPage() {
  const token = useAccessToken();
  const [search, setSearch] = useState("");
  const { data, isLoading, isError, error, refetch } = useQuery({ queryKey: ["users", search], queryFn: () => api.get<PaginatedResponse<User>>(`/users?page_size=50${search ? `&search=${encodeURIComponent(search)}` : ""}`, token) });
  const columns: TableColumn<User>[] = [
    { id: "name", header: "Team member", cell: (user) => <><strong>{user.full_name}</strong><small>{user.email}</small></> },
    { id: "role", header: "Role", cell: (user) => <StatusBadge value={user.role.toUpperCase()} /> },
    { id: "joined", header: "Joined", cell: (user) => new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(user.date_joined)) },
    { id: "status", header: "Status", cell: (user) => <StatusBadge value={user.is_active ? "ACTIVE" : "INACTIVE"} /> },
  ];
  return <><PageHeader eyebrow="Administration" title="Team members" description="Manage the internal people who can access the operations workspace." action={<div className="directory-actions"><label className="search-field"><span className="sr-only">Search team members</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search people" /></label><Link className="button button--primary" to="/team/new">Add team member</Link></div>} />{isLoading ? <LoadingState title="Loading team" description="Retrieving user accounts." /> : null}{isError ? <ErrorState title="Could not load team members" description={error instanceof ApiError ? error.message : "Please check your connection and try again."} onRetry={() => void refetch()} /> : null}{data ? <section className="data-card"><div className="data-card__summary"><strong>{data.count}</strong><span>team member{data.count === 1 ? "" : "s"}</span></div>{data.results.length ? <DataTable label="Team members" columns={columns} rows={data.results} getRowKey={(user) => user.id} /> : <EmptyState title="No team members found" description="Invite a staff member to share operational work." action={<Link className="button button--primary" to="/team/new">Add team member</Link>} />}</section> : null}</>;
}

const staffFormSchema = z.object({
  full_name: z.string().trim().min(2, "Enter a name."),
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters."),
  role: z.enum(["staff", "admin"]),
});

type StaffFormValues = z.infer<typeof staffFormSchema>;

export function TeamCreatePage() {
  const token = useAccessToken();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [notice, setNotice] = useState<string>();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<StaffFormValues>({ resolver: zodResolver(staffFormSchema), defaultValues: { full_name: "", email: "", password: "", role: "staff" } });
  async function onSubmit(values: StaffFormValues) {
    setNotice(undefined);
    try {
      await api.post<User>("/users/staff", values, token);
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      navigate("/team", { replace: true });
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "The team member could not be created.");
    }
  }
  return <><PageHeader eyebrow="Administration" title="Add team member" description="Create an internal account with the appropriate role." action={<Link className="button button--secondary" to="/team">Back to team</Link>} /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Account details</h2><div className="form-grid"><TextField label="Full name" autoComplete="name" error={errors.full_name?.message} {...register("full_name")} /><TextField label="Email address" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} /><TextField label="Temporary password" type="password" autoComplete="new-password" error={errors.password?.message} {...register("password")} /><label className="field"><span className="field__label">Role</span><select className="input select-input" {...register("role")}><option value="staff">Staff</option><option value="admin">Admin</option></select></label></div></div>{notice ? <p className="form-alert" role="alert">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating…" : "Create team member"}</Button></div></form></>;
}

const passwordFormSchema = z.object({
  current_password: z.string().min(1, "Enter your current password."),
  new_password: z.string().min(8, "Use at least 8 characters."),
  confirm_password: z.string().min(1, "Confirm your new password."),
}).refine((values) => values.new_password === values.confirm_password, { path: ["confirm_password"], message: "Passwords do not match." });

type PasswordFormValues = z.infer<typeof passwordFormSchema>;

export function SecurityPage() {
  const token = useAccessToken();
  const [notice, setNotice] = useState<string>();
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<PasswordFormValues>({ resolver: zodResolver(passwordFormSchema), defaultValues: { current_password: "", new_password: "", confirm_password: "" } });
  async function onSubmit(values: PasswordFormValues) {
    setNotice(undefined);
    try {
      await api.post<void>("/auth/password/change", { current_password: values.current_password, new_password: values.new_password }, token);
      reset();
      setNotice("Your password has been updated.");
    } catch (submitError) {
      setNotice(submitError instanceof ApiError ? submitError.message : "We could not update your password.");
    }
  }
  return <><PageHeader eyebrow="Account" title="Password and security" description="Update your password to keep your account protected." /><form className="profile-card" onSubmit={handleSubmit(onSubmit)} noValidate><div className="profile-card__section"><h2>Change password</h2><div className="form-grid"><TextField label="Current password" type="password" autoComplete="current-password" error={errors.current_password?.message} {...register("current_password")} /><TextField label="New password" type="password" autoComplete="new-password" hint="Use at least 8 characters." error={errors.new_password?.message} {...register("new_password")} /><TextField label="Confirm new password" type="password" autoComplete="new-password" error={errors.confirm_password?.message} {...register("confirm_password")} /></div></div>{notice ? <p className="form-alert" role="status">{notice}</p> : null}<div className="form-actions"><Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Updating…" : "Update password"}</Button></div></form></>;
}
