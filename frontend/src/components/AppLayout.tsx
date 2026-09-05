import { NavLink, useNavigate } from "react-router-dom";

import { BrandMark, Icon } from "./ui";

type AppLayoutProps = {
  children: React.ReactNode;
};

export default function AppLayout({ children }: AppLayoutProps) {
  const navigate = useNavigate();

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <NavLink className="sidebar-brand" to="/dashboard" aria-label="AI Helpdesk dashboard">
          <BrandMark />
          <span>
            <strong>AI Helpdesk</strong>
            <small>Support operations</small>
          </span>
        </NavLink>

        <div className="sidebar-navigation">
          <p className="sidebar-label">Workspace</p>
          <nav className="app-nav" aria-label="Main navigation">
            <NavLink to="/dashboard">
              <Icon name="dashboard" />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/tickets">
              <Icon name="ticket" />
              <span>Tickets</span>
            </NavLink>
            <NavLink to="/documents">
              <Icon name="document" />
              <span>Knowledge Base</span>
            </NavLink>
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="system-status-dot" aria-hidden="true" />
            <span>
              <strong>AI services</strong>
              <small>Ready to assist</small>
            </span>
          </div>
          <button className="sidebar-logout" type="button" onClick={handleLogout}>
            <Icon name="logout" />
            <span>Log out</span>
          </button>
        </div>
      </aside>

      <div className="app-content">
        <main className="app-main">{children}</main>
      </div>
    </div>
  );
}
