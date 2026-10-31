import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { useAuth } from "../auth/useAuth";
import { AppShell } from "../layouts/AppShell";
import { LoginPage, RegisterPage } from "../pages/AuthPages";
import { CustomersPage, ProfilePage, WorkspaceHome } from "../pages/WorkspacePages";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

function ProtectedRoute() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

function CustomerOnlyRoute() {
  const { user } = useAuth();
  return user?.role === "customer" ? <Outlet /> : <Navigate to="/" replace />;
}

function RoleHome() {
  const { user } = useAuth();
  return user?.role === "customer" ? <Navigate to="/portal/profile" replace /> : <WorkspaceHome />;
}

export function App() {
  return <QueryClientProvider client={queryClient}><AuthProvider><BrowserRouter><Routes><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route element={<ProtectedRoute />}><Route element={<AppShell />}><Route index element={<RoleHome />} /><Route path="customers" element={<CustomersPage />} /><Route element={<CustomerOnlyRoute />}><Route path="portal/profile" element={<ProfilePage />} /></Route></Route></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes></BrowserRouter></AuthProvider></QueryClientProvider>;
}
