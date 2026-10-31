import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Brand, Button } from "../components/ui";
import { useAuth } from "../auth/useAuth";

export function AppShell() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const isCustomer = user?.role === "customer";
  const links = isCustomer
      ? [{ to: "/portal/profile", label: "My profile" }, { to: "/portal/plans", label: "Choose a plan" }, { to: "/portal/subscriptions", label: "My subscriptions" }, { to: "/invoices", label: "Invoices" }, { to: "/notifications", label: "Notifications" }, { to: "/settings/security", label: "Security" }]
      : user?.role === "admin"
      ? [{ to: "/app", label: "Overview" }, { to: "/customers", label: "Customers" }, { to: "/team", label: "Team" }, { to: "/products", label: "Products" }, { to: "/attributes", label: "Variants" }, { to: "/plans", label: "Plans" }, { to: "/payment-terms", label: "Payment terms" }, { to: "/quotation-templates", label: "Quotations" }, { to: "/subscriptions", label: "Subscriptions" }, { to: "/invoices", label: "Invoices" }, { to: "/payments", label: "Payments" }, { to: "/billing-runs", label: "Billing runs" }, { to: "/reports", label: "Reports" }, { to: "/notifications", label: "Notifications" }, { to: "/settings/security", label: "Security" }]
      : [{ to: "/app", label: "Overview" }, { to: "/customers", label: "Customers" }, { to: "/products", label: "Products" }, { to: "/plans", label: "Plans" }, { to: "/quotation-templates", label: "Quotations" }, { to: "/subscriptions", label: "Subscriptions" }, { to: "/invoices", label: "Invoices" }, { to: "/payments", label: "Payments" }, { to: "/settings/security", label: "Security" }];

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Brand />
        <div className="workspace-pill"><span className="workspace-pill__dot" /> Brightloop workspace</div>
        <nav className="primary-nav" aria-label="Main navigation">
          <p>Workspace</p>
          {links.map((link) => <NavLink key={link.to} to={link.to} end={link.to === "/app"}>{link.label}</NavLink>)}
        </nav>
        <div className="sidebar__footer">
          <div className="identity"><span>{user?.full_name.slice(0, 1).toUpperCase()}</span><div><strong>{user?.full_name}</strong><small>{user?.role}</small></div></div>
          <Button type="button" tone="quiet" onClick={handleLogout}>Sign out</Button>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div><p className="eyebrow">Brightloop</p><span>{isCustomer ? "Customer portal" : "Operations workspace"}</span></div>
          <NavLink className="topbar__profile" to={isCustomer ? "/portal/profile" : "/app"} aria-label="Open account area">
            <span>{user?.full_name.slice(0, 1).toUpperCase()}</span><strong>{user?.full_name}</strong>
          </NavLink>
        </header>
        <div className="main-content__body"><Outlet /></div>
      </main>
    </div>
  );
}
