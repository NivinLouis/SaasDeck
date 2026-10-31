import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { useAuth } from "../auth/useAuth";
import { AppShell } from "../layouts/AppShell";
import { SecurityPage, TeamCreatePage, TeamPage } from "../pages/AdminPages";
import { DiscountFormPage, DiscountsPage, TaxFormPage, TaxesPage } from "../pages/AdminCatalogPages";
import { LoginPage, RegisterPage } from "../pages/AuthPages";
import { InvoiceDetailPage, InvoicesPage } from "../pages/InvoicePages";
import { InvoiceCreatePage } from "../pages/InvoiceCreatePage";
import { ModuleFormPage, ModuleListPage, modules } from "../pages/ModulePages";
import { PaymentDetailPage, PaymentFormPage, PaymentsPage } from "../pages/PaymentPages";
import { PlanFormPage, PlansPage, ProductFormPage, ProductsPage } from "../pages/CatalogPages";
import { SubscriptionDetailPage, SubscriptionFormPage, SubscriptionsPage } from "../pages/SubscriptionPages";
import { CustomerCreatePage, CustomerEditPage, CustomersPage, ProfilePage } from "../pages/WorkspacePages";
import { LandingPage } from "../pages/LandingPage";
import { DashboardPage } from "../pages/DashboardPage";

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
  return user?.role === "customer" ? <Navigate to="/portal/profile" replace /> : <DashboardPage />;
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
                <Route path="settings/security" element={<SecurityPage />} />

                <Route element={<InternalOnlyRoute />}>
                  <Route path="customers" element={<CustomersPage />} />
                  <Route path="customers/new" element={<CustomerCreatePage />} />
                  <Route path="customers/:customerId" element={<CustomerEditPage />} />
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
                  <Route path="team" element={<TeamPage />} />
                  <Route path="team/new" element={<TeamCreatePage />} />
                  <Route path="team/:userId" element={<Navigate to="/team" replace />} />
                  <Route path="taxes" element={<TaxesPage />} />
                  <Route path="taxes/new" element={<TaxFormPage />} />
                  <Route path="taxes/:taxId" element={<TaxFormPage />} />
                  <Route path="attributes" element={<ModuleListPage module={modules.attributes} />} />
                  <Route path="attributes/new" element={<ModuleFormPage module={modules.attributes} />} />
                  <Route path="attributes/:attributeId" element={<ModuleFormPage module={modules.attributes} mode="edit" />} />
                  <Route path="payment-terms" element={<ModuleListPage module={modules.paymentTerms} />} />
                  <Route path="payment-terms/new" element={<ModuleFormPage module={modules.paymentTerms} />} />
                  <Route path="payment-terms/:paymentTermId" element={<ModuleFormPage module={modules.paymentTerms} mode="edit" />} />
                  <Route path="discounts" element={<DiscountsPage />} />
                  <Route path="discounts/new" element={<DiscountFormPage />} />
                  <Route path="discounts/:discountId" element={<DiscountFormPage />} />
                  <Route path="billing-runs" element={<ModuleListPage module={modules.billingRuns} />} />
                  <Route path="billing-runs/:runId" element={<ModuleFormPage module={modules.billingRuns} mode="edit" />} />
                  <Route path="reports" element={<DashboardPage />} />
                  <Route path="notifications" element={<ModuleListPage module={modules.notifications} />} />
                </Route>

                <Route path="invoices" element={<InvoicesPage />} />
                <Route path="invoices/new" element={<InvoiceCreatePage />} />
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
