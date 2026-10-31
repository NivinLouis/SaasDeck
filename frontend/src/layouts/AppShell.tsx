import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Brand, Button } from "../components/ui";
import { useAuth } from "../auth/useAuth";

export function AppShell() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const isCustomer = user?.role === "customer";
  const links = isCustomer
    ? [{ to: "/portal/profile", label: "My profile" }]
    : [{ to: "/", label: "Overview" }, { to: "/customers", label: "Customers" }];

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
          {links.map((link) => <NavLink key={link.to} to={link.to} end={link.to === "/"}>{link.label}</NavLink>)}
        </nav>
        <div className="sidebar__footer">
          <div className="identity"><span>{user?.full_name.slice(0, 1).toUpperCase()}</span><div><strong>{user?.full_name}</strong><small>{user?.role}</small></div></div>
          <Button type="button" tone="quiet" onClick={handleLogout}>Sign out</Button>
        </div>
      </aside>
      <main className="main-content"><Outlet /></main>
    </div>
  );
}
