import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../api/client";
import AppLayout from "../components/AppLayout";
import { Icon, MetricCard, PageHeader } from "../components/ui";

type User = {
  id: number;
  name: string;
  email: string;
};

type Ticket = {
  id: number;
  status: string;
};

type Document = {
  id: number;
  status: string;
};

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [
          userResponse,
          ticketsResponse,
          documentsResponse,
        ] = await Promise.all([
          api.get<User>("/auth/me"),
          api.get<Ticket[]>("/tickets/"),
          api.get<Document[]>("/documents/"),
        ]);

        setUser(userResponse.data);
        setTickets(ticketsResponse.data);
        setDocuments(documentsResponse.data);
        setError("");
      } catch {
        setError("Could not load dashboard summary.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <AppLayout>
        <p className="message message-loading">Loading...</p>
      </AppLayout>
    );
  }

  const openTickets = tickets.filter(
    (ticket) => ticket.status === "open",
  ).length;
  const resolvedTickets = tickets.filter(
    (ticket) => ticket.status === "resolved",
  ).length;
  const readyDocuments = documents.filter(
    (document) => document.status === "ready",
  ).length;
  const processingDocuments = documents.filter(
    (document) => document.status === "processing",
  ).length;

  return (
    <AppLayout>
      <PageHeader
        eyebrow="Overview"
        title="Dashboard"
        description="Monitor your support queue and knowledge base at a glance."
      />

      {error && <p className="message message-error" role="alert">{error}</p>}

      <section className="welcome-panel">
        {user && (
          <>
            <div className="user-avatar" aria-hidden="true">
              {user.name.charAt(0).toUpperCase()}
            </div>
            <div className="welcome-copy">
              <p className="eyebrow">Your workspace</p>
              <h3>Welcome, {user.name}</h3>
              <p>{user.email}</p>
            </div>
            <div className="welcome-status">
              <span className="system-status-dot" aria-hidden="true" />
              System operational
            </div>
          </>
        )}
      </section>

      <section className="dashboard-section" aria-labelledby="ticket-metrics-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Support queue</p>
            <h3 id="ticket-metrics-title">Ticket activity</h3>
          </div>
          <Link className="text-link" to="/tickets">
            View tickets <Icon name="arrow" size={15} />
          </Link>
        </div>
        <div className="metrics-grid">
          <MetricCard
            label="Total tickets"
            value={tickets.length}
            helper="All support requests"
            icon="ticket"
            tone="accent"
          />
          <MetricCard
            label="Open tickets"
            value={openTickets}
            helper="Awaiting a resolution"
            icon="open"
            tone="warning"
          />
          <MetricCard
            label="Resolved tickets"
            value={resolvedTickets}
            helper="Successfully completed"
            icon="check"
            tone="success"
          />
        </div>
      </section>

      <section className="dashboard-section" aria-labelledby="document-metrics-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Knowledge base</p>
            <h3 id="document-metrics-title">Document activity</h3>
          </div>
          <Link className="text-link" to="/documents">
            View knowledge base <Icon name="arrow" size={15} />
          </Link>
        </div>
        <div className="metrics-grid">
          <MetricCard
            label="Total documents"
            value={documents.length}
            helper="Uploaded knowledge"
            icon="document"
          />
          <MetricCard
            label="Ready documents"
            value={readyDocuments}
            helper="Available for AI answers"
            icon="check"
            tone="success"
          />
          <MetricCard
            label="Processing documents"
            value={processingDocuments}
            helper="Preparing for search"
            icon="processing"
            tone="warning"
          />
        </div>
      </section>

      <section className="dashboard-section" aria-labelledby="shortcuts-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Shortcuts</p>
            <h3 id="shortcuts-title">Continue working</h3>
          </div>
        </div>
        <nav className="shortcut-grid" aria-label="Dashboard shortcuts">
          <Link className="shortcut-card" to="/tickets">
            <span className="shortcut-icon"><Icon name="inbox" /></span>
            <span>
              <strong>Manage support queue</strong>
              <small>Create, review, and update tickets.</small>
            </span>
            <Icon name="arrow" />
          </Link>
          <Link className="shortcut-card" to="/documents">
            <span className="shortcut-icon"><Icon name="sparkles" /></span>
            <span>
              <strong>Ask the knowledge base</strong>
              <small>Upload resources and get grounded answers.</small>
            </span>
            <Icon name="arrow" />
          </Link>
        </nav>
      </section>
    </AppLayout>
  );
}
