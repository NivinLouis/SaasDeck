import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider } from "../auth/AuthContext";
import { useAuth } from "../auth/useAuth";
import { AppShell } from "../layouts/AppShell";
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from "../pages/AuthPages";
import { LandingPage } from "../pages/LandingPage";

const SecurityPage = lazy(() => import("../pages/AdminPages").then((m) => ({ default: m.SecurityPage })));
const TeamPage = lazy(() => import("../pages/AdminPages").then((m) => ({ default: m.TeamPage })));
const TeamCreatePage = lazy(() => import("../pages/AdminPages").then((m) => ({ default: m.TeamCreatePage })));
const TaxesPage = lazy(() => import("../pages/AdminCatalogPages").then((m) => ({ default: m.TaxesPage })));
const TaxFormPage = lazy(() => import("../pages/AdminCatalogPages").then((m) => ({ default: m.TaxFormPage })));
const DiscountsPage = lazy(() => import("../pages/AdminCatalogPages").then((m) => ({ default: m.DiscountsPage })));
const DiscountFormPage = lazy(() => import("../pages/AdminCatalogPages").then((m) => ({ default: m.DiscountFormPage })));
const ProductsPage = lazy(() => import("../pages/CatalogPages").then((m) => ({ default: m.ProductsPage })));
const ProductFormPage = lazy(() => import("../pages/CatalogPages").then((m) => ({ default: m.ProductFormPage })));
const PlansPage = lazy(() => import("../pages/CatalogPages").then((m) => ({ default: m.PlansPage })));
const PlanFormPage = lazy(() => import("../pages/CatalogPages").then((m) => ({ default: m.PlanFormPage })));
const InvoiceCreatePage = lazy(() => import("../pages/InvoiceCreatePage").then((module) => ({ default: module.InvoiceCreatePage })));
const InvoiceDetailPage = lazy(() => import("../pages/InvoicePages").then((m) => ({ default: m.InvoiceDetailPage })));
const InvoicesPage = lazy(() => import("../pages/InvoicePages").then((m) => ({ default: m.InvoicesPage })));
const AttributesPage = lazy(() => import("../pages/OperationsPages").then((m) => ({ default: m.AttributesPage })));
const BillingRunsPage = lazy(() => import("../pages/OperationsPages").then((m) => ({ default: m.BillingRunsPage })));
const NotificationsPage = lazy(() => import("../pages/OperationsPages").then((m) => ({ default: m.NotificationsPage })));
const PaymentTermsPage = lazy(() => import("../pages/OperationsPages").then((m) => ({ default: m.PaymentTermsPage })));
const PaymentsPage = lazy(() => import("../pages/PaymentPages").then((m) => ({ default: m.PaymentsPage })));
const PaymentFormPage = lazy(() => import("../pages/PaymentPages").then((m) => ({ default: m.PaymentFormPage })));
const PaymentDetailPage = lazy(() => import("../pages/PaymentPages").then((m) => ({ default: m.PaymentDetailPage })));
const QuotationTemplatesPage = lazy(() => import("../pages/QuotationPages").then((m) => ({ default: m.QuotationTemplatesPage })));
const QuotationTemplateFormPage = lazy(() => import("../pages/QuotationPages").then((m) => ({ default: m.QuotationTemplateFormPage })));
const CreateQuotationPage = lazy(() => import("../pages/QuotationPages").then((m) => ({ default: m.CreateQuotationPage })));
const SubscriptionsPage = lazy(() => import("../pages/SubscriptionPages").then((m) => ({ default: m.SubscriptionsPage })));
const SubscriptionFormPage = lazy(() => import("../pages/SubscriptionPages").then((m) => ({ default: m.SubscriptionFormPage })));
const SubscriptionDetailPage = lazy(() => import("../pages/SubscriptionPages").then((m) => ({ default: m.SubscriptionDetailPage })));
const CustomersPage = lazy(() => import("../pages/WorkspacePages").then((m) => ({ default: m.CustomersPage })));
const CustomerCreatePage = lazy(() => import("../pages/WorkspacePages").then((m) => ({ default: m.CustomerCreatePage })));
const CustomerEditPage = lazy(() => import("../pages/WorkspacePages").then((m) => ({ default: m.CustomerEditPage })));
const ProfilePage = lazy(() => import("../pages/WorkspacePages").then((m) => ({ default: m.ProfilePage })));
const DashboardPage = lazy(() => import("../pages/DashboardPage").then((module) => ({ default: module.DashboardPage })));
const ReportsPage = lazy(() => import("../pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const PortalPlansPage = lazy(() => import("../pages/PortalPlanPage").then((module) => ({ default: module.PortalPlansPage })));

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
          <Suspense fallback={<div className="route-loading" aria-live="polite">Loading workspace…</div>}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="app" element={<RoleHome />} />
                <Route path="settings/security" element={<SecurityPage />} />

                <Route element={<InternalOnlyRoute />}>
                  <Route path="customers" element={<CustomersPage />} />
                  <Route path="customers/new" element={<CustomerCreatePage />} />
                  <Route path="customers/:customerId" element={<CustomerEditPage />} />
                  <Route path="quotation-templates" element={<QuotationTemplatesPage />} />
                  <Route path="quotation-templates/new" element={<QuotationTemplateFormPage />} />
                  <Route path="quotation-templates/:templateId" element={<QuotationTemplateFormPage />} />
                  <Route path="quotation-templates/:templateId/quotations/new" element={<CreateQuotationPage />} />
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
                  <Route path="attributes" element={<AttributesPage />} />
                  <Route path="payment-terms" element={<PaymentTermsPage />} />
                  <Route path="payment-terms/new" element={<PaymentTermsPage />} />
                  <Route path="payment-terms/:paymentTermId" element={<PaymentTermsPage />} />
                  <Route path="discounts" element={<DiscountsPage />} />
                  <Route path="discounts/new" element={<DiscountFormPage />} />
                  <Route path="discounts/:discountId" element={<DiscountFormPage />} />
                  <Route path="billing-runs" element={<BillingRunsPage />} />
                  <Route path="reports" element={<ReportsPage />} />
                </Route>

                <Route path="invoices" element={<InvoicesPage />} />
                <Route path="invoices/new" element={<InvoiceCreatePage />} />
                <Route path="invoices/:invoiceUuid" element={<InvoiceDetailPage />} />
                <Route path="notifications" element={<NotificationsPage />} />

                <Route element={<CustomerOnlyRoute />}>
                  <Route path="portal/profile" element={<ProfilePage />} />
                  <Route path="portal/plans" element={<PortalPlansPage />} />
                  <Route path="portal/subscriptions" element={<SubscriptionsPage portal />} />
                  <Route path="portal/subscriptions/:subscriptionId" element={<SubscriptionDetailPage portal />} />
                  <Route path="portal/invoices" element={<Navigate to="/invoices" replace />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
