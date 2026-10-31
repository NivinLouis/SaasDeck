import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { useAuth } from "../auth/useAuth";
import { AppShell } from "../layouts/AppShell";
import { LoginPage, RegisterPage } from "../pages/AuthPages";
import { InvoiceDetailPage, InvoicesPage } from "../pages/InvoicePages";
import { ModuleFormPage, ModuleListPage, modules } from "../pages/ModulePages";
import { PaymentDetailPage, PaymentFormPage, PaymentsPage } from "../pages/PaymentPages";
import { PlanFormPage, PlansPage, ProductFormPage, ProductsPage } from "../pages/CatalogPages";
import { SubscriptionDetailPage, SubscriptionFormPage, SubscriptionsPage } from "../pages/SubscriptionPages";
import { CustomerCreatePage, CustomersPage, ProfilePage, WorkspaceHome } from "../pages/WorkspacePages";
import { LandingPage } from "../pages/LandingPage";

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

function InternalOnlyRoute() {
  const { user } = useAuth();
  return user?.role === "admin" || user?.role === "staff" ? <Outlet /> : <Navigate to="/portal/profile" replace />;
}

function AdminOnlyRoute() {
  const { user } = useAuth();
  return user?.role === "admin" ? <Outlet /> : <Navigate to="/app" replace />;
}

function RoleHome() {
  const { user } = useAuth();
  return user?.role === "customer" ? <Navigate to="/portal/profile" replace /> : <WorkspaceHome />;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="app" element={<RoleHome />} />
                <Route path="settings/security" element={<ModuleFormPage module={modules.security} />} />

                <Route element={<InternalOnlyRoute />}>
                  <Route path="customers" element={<CustomersPage />} />
                  <Route path="customers/new" element={<CustomerCreatePage />} />
                  <Route path="customers/:customerId" element={<ModuleFormPage module={modules.customerEdit} mode="edit" />} />
                  <Route path="quotation-templates" element={<ModuleListPage module={modules.quotationTemplates} />} />
                  <Route path="quotation-templates/new" element={<ModuleFormPage module={modules.quotationTemplates} />} />
                  <Route path="quotation-templates/:templateId" element={<ModuleFormPage module={modules.quotationTemplates} mode="edit" />} />
                  <Route path="subscriptions" element={<SubscriptionsPage />} />
                  <Route path="subscriptions/new" element={<SubscriptionFormPage />} />
                  <Route path="subscriptions/:subscriptionId" element={<SubscriptionDetailPage />} />
                  <Route path="payments" element={<PaymentsPage />} />
                  <Route path="payments/new" element={<PaymentFormPage />} />
                  <Route path="payments/:paymentId" element={<PaymentDetailPage />} />
                  <Route path="products" element={<ProductsPage />} />
                  <Route path="products/new" element={<ProductFormPage />} />
                  <Route path="products/:productId" element={<ProductFormPage />} />
                  <Route path="plans" element={<PlansPage />} />
                  <Route path="plans/new" element={<PlanFormPage />} />
                  <Route path="plans/:planId" element={<PlanFormPage />} />
                </Route>

                <Route element={<AdminOnlyRoute />}>
                  <Route path="team" element={<ModuleListPage module={modules.team} />} />
                  <Route path="team/new" element={<ModuleFormPage module={modules.team} />} />
                  <Route path="team/:userId" element={<ModuleFormPage module={modules.team} mode="edit" />} />
                  <Route path="taxes" element={<ModuleListPage module={modules.taxes} />} />
                  <Route path="taxes/new" element={<ModuleFormPage module={modules.taxes} />} />
                  <Route path="taxes/:taxId" element={<ModuleFormPage module={modules.taxes} mode="edit" />} />
                  <Route path="attributes" element={<ModuleListPage module={modules.attributes} />} />
                  <Route path="attributes/new" element={<ModuleFormPage module={modules.attributes} />} />
                  <Route path="attributes/:attributeId" element={<ModuleFormPage module={modules.attributes} mode="edit" />} />
                  <Route path="payment-terms" element={<ModuleListPage module={modules.paymentTerms} />} />
                  <Route path="payment-terms/new" element={<ModuleFormPage module={modules.paymentTerms} />} />
                  <Route path="payment-terms/:paymentTermId" element={<ModuleFormPage module={modules.paymentTerms} mode="edit" />} />
                  <Route path="discounts" element={<ModuleListPage module={modules.discounts} />} />
                  <Route path="discounts/new" element={<ModuleFormPage module={modules.discounts} />} />
                  <Route path="discounts/:discountId" element={<ModuleFormPage module={modules.discounts} mode="edit" />} />
                  <Route path="billing-runs" element={<ModuleListPage module={modules.billingRuns} />} />
                  <Route path="billing-runs/:runId" element={<ModuleFormPage module={modules.billingRuns} mode="edit" />} />
                  <Route path="reports" element={<ModuleListPage module={modules.reports} />} />
                  <Route path="notifications" element={<ModuleListPage module={modules.notifications} />} />
                </Route>

                <Route path="invoices" element={<InvoicesPage />} />
                <Route path="invoices/:invoiceUuid" element={<InvoiceDetailPage />} />

                <Route element={<CustomerOnlyRoute />}>
                  <Route path="portal/profile" element={<ProfilePage />} />
                  <Route path="portal/subscriptions" element={<SubscriptionsPage portal />} />
                  <Route path="portal/subscriptions/:subscriptionId" element={<SubscriptionDetailPage portal />} />
                  <Route path="portal/invoices" element={<Navigate to="/invoices" replace />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
