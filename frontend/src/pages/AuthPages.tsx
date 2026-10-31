import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/useAuth";
import { Brand, Button, TextField } from "../components/ui";

const loginSchema = z.object({ email: z.string().trim().email("Enter a valid email address."), password: z.string().min(1, "Enter your password.") });
const registerSchema = z.object({
  full_name: z.string().trim().min(2, "Enter your full name."),
  email: z.string().trim().email("Enter a valid email address."),
  password: z.string().min(9, "Use at least 9 characters.").regex(/[A-Z]/, "Include an uppercase letter.").regex(/[a-z]/, "Include a lowercase letter.").regex(/[^A-Za-z0-9]/, "Include a special character."),
});

type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;

function AuthFrame({ children, title, description }: { children: React.ReactNode; title: string; description: string }) {
  return <main className="auth-page"><section className="auth-panel"><Brand /><div className="auth-copy"><p className="eyebrow">Subscription operations, simplified</p><h1>{title}</h1><p>{description}</p></div>{children}</section><aside className="auth-aside"><div><p className="eyebrow">Brightloop Software</p><h2>One clear view of every subscription.</h2><p>Manage customers, recurring revenue, invoices, and payments from a single focused workspace.</p></div><small>Built for the people who keep subscriptions moving.</small></aside></main>;
}

export function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState<string>();
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) });

  if (isAuthenticated) return <Navigate to="/" replace />;

  async function onSubmit(values: LoginValues) {
    setServerError(undefined);
    try {
      const user = await login(values);
      const requestedPath = (location.state as { from?: string } | null)?.from;
      navigate(requestedPath ?? (user.role === "customer" ? "/portal/profile" : "/"), { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.fields) {
        Object.entries(error.fields).forEach(([field, messages]) => {
          if (field === "email" || field === "password") setError(field, { message: messages[0] });
        });
      }
      setServerError(error instanceof ApiError ? error.message : "We could not sign you in. Please try again.");
    }
  }

  return <AuthFrame title="Welcome back" description="Sign in to continue to your workspace."><form className="form-stack" onSubmit={handleSubmit(onSubmit)} noValidate><TextField label="Email address" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} /><TextField label="Password" type="password" autoComplete="current-password" error={errors.password?.message} {...register("password")} />{serverError ? <p className="form-alert" role="alert">{serverError}</p> : null}<Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Signing in…" : "Sign in"}</Button></form><p className="auth-switch">New to Brightloop? <Link to="/register">Create an account</Link></p></AuthFrame>;
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string>();
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterValues) {
    setServerError(undefined);
    try {
      await api.post("/auth/register", values);
      navigate("/login", { replace: true, state: { registered: true } });
    } catch (error) {
      if (error instanceof ApiError && error.fields) {
        Object.entries(error.fields).forEach(([field, messages]) => {
          if (field === "email" || field === "full_name" || field === "password") setError(field, { message: messages[0] });
        });
      }
      setServerError(error instanceof ApiError ? error.message : "We could not create your account. Please try again.");
    }
  }

  return <AuthFrame title="Create your account" description="Start managing your subscription account in one secure place."><form className="form-stack" onSubmit={handleSubmit(onSubmit)} noValidate><TextField label="Full name" autoComplete="name" error={errors.full_name?.message} {...register("full_name")} /><TextField label="Email address" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} /><TextField label="Password" type="password" autoComplete="new-password" hint="At least 9 characters, with uppercase, lowercase, and a special character." error={errors.password?.message} {...register("password")} />{serverError ? <p className="form-alert" role="alert">{serverError}</p> : null}<Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Creating account…" : "Create account"}</Button></form><p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p></AuthFrame>;
}
