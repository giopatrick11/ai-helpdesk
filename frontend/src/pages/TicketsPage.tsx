import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import api from "../api/client";
import AppLayout from "../components/AppLayout";
import { Icon, PageHeader, StatusBadge } from "../components/ui";
import { formatStatus } from "../utils/format";

type Ticket = {
  id: number;
  subject: string;
  description: string;
  priority: string;
  status: string;
  category: string | null;
  ai_summary: string | null;
  ai_status: string;
  ai_error: string | null;
};

const TICKET_STATUSES = [
  "open",
  "in_progress",
  "resolved",
];

function isPendingAiAnalysis(ticket: Ticket) {
  return ticket.ai_status === "processing";
}

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [deletingTicketIds, setDeletingTicketIds] = useState<number[]>([]);
  const [deleteError, setDeleteError] = useState("");
  const [updatingTicketIds, setUpdatingTicketIds] = useState<number[]>([]);
  const [updateError, setUpdateError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");

  const loadTickets = useCallback(async () => {
    try {
      const response = await api.get("/tickets/");
      setTickets(response.data);
      setLoadError("");
    } catch {
      setLoadError("Could not load tickets.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isActive = true;

    api.get<Ticket[]>("/tickets/")
      .then((response) => {
        if (isActive) {
          setTickets(response.data);
          setLoadError("");
        }
      })
      .catch(() => {
        if (isActive) {
          setLoadError("Could not load tickets.");
        }
      })
      .finally(() => {
        if (isActive) {
          setLoading(false);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    const hasPendingAiAnalysis = tickets.some(isPendingAiAnalysis);

    if (!hasPendingAiAnalysis) {
      return;
    }

    const intervalId = window.setInterval(() => {
      void loadTickets();
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [tickets, loadTickets]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setCreateError("");
    setCreateSuccess("");

    try {
      const response = await api.post<Ticket>("/tickets/", {
        subject,
        description,
      });

      setSubject("");
      setDescription("");
      setTickets((currentTickets) => [
        ...currentTickets,
        response.data,
      ]);
      setCreateSuccess(
        response.data.ai_status === "failed"
          ? "Ticket saved, but AI analysis could not be queued."
          : "Ticket created. AI analysis has started.",
      );
    } catch {
      setCreateError("Could not create ticket.");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(ticket: Ticket) {
    const confirmed = window.confirm(
      `Delete "${ticket.subject}"?`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingTicketIds((currentIds) => [
      ...currentIds,
      ticket.id,
    ]);
    setDeleteError("");

    try {
      await api.delete(`/tickets/${ticket.id}`);

      setTickets((currentTickets) =>
        currentTickets.filter(
          (currentTicket) => currentTicket.id !== ticket.id,
        ),
      );
    } catch {
      setDeleteError("Could not delete ticket.");
    } finally {
      setDeletingTicketIds((currentIds) =>
        currentIds.filter((ticketId) => ticketId !== ticket.id),
      );
    }
  }

  async function handleStatusChange(
    ticket: Ticket,
    status: string,
  ) {
    if (status === ticket.status) {
      return;
    }

    setUpdatingTicketIds((currentIds) => [
      ...currentIds,
      ticket.id,
    ]);
    setUpdateError("");

    try {
      const response = await api.put<Ticket>(`/tickets/${ticket.id}`, {
        status,
      });

      setTickets((currentTickets) =>
        currentTickets.map((currentTicket) =>
          currentTicket.id === ticket.id ? response.data : currentTicket,
        ),
      );
    } catch {
      setUpdateError("Could not update ticket status.");
    } finally {
      setUpdatingTicketIds((currentIds) =>
        currentIds.filter((ticketId) => ticketId !== ticket.id),
      );
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <p className="message message-loading">Loading tickets...</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <PageHeader
        eyebrow="Support operations"
        title="Tickets"
        description="Create and manage customer requests while AI handles triage in the background."
      >
        <span className="header-count">
          <Icon name="inbox" size={16} />
          {tickets.length} {tickets.length === 1 ? "ticket" : "tickets"}
        </span>
      </PageHeader>

      <section className="panel create-ticket-panel">
        <div className="panel-heading">
          <span className="panel-icon"><Icon name="ticket" /></span>
          <div>
            <h3>Create ticket</h3>
            <p>Describe the issue and AI will categorize and summarize it.</p>
          </div>
        </div>

        <form className="ticket-create-form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="subject">Subject</label>
            <input
              id="subject"
              placeholder="Short summary of the issue"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              required
            />
          </div>

          <div className="field">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              placeholder="Add the details your support team needs..."
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              required
            />
          </div>

          <div className="form-feedback" aria-live="polite">
            {createError && <p className="message message-error" role="alert">{createError}</p>}
            {createSuccess && <p className="message message-success">{createSuccess}</p>}
          </div>

          <button className="button button-primary ticket-submit" type="submit" disabled={creating}>
            {!creating && <Icon name="ticket" size={17} />}
            {creating ? "Creating..." : "Create Ticket"}
          </button>
        </form>
      </section>

      <div className="page-messages" aria-live="polite">
        {loadError && <p className="message message-error" role="alert">{loadError}</p>}
        {deleteError && <p className="message message-error" role="alert">{deleteError}</p>}
        {updateError && <p className="message message-error" role="alert">{updateError}</p>}
      </div>

      {tickets.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon"><Icon name="inbox" size={22} /></span>
          <h3>Your support queue is clear</h3>
          <p>No tickets yet. New requests will appear here.</p>
        </div>
      ) : (
        <section className="queue-section" aria-labelledby="ticket-queue-title">
          <div className="section-heading queue-heading">
            <div>
              <p className="eyebrow">Current workload</p>
              <h3 id="ticket-queue-title">Support queue</h3>
            </div>
            <span className="section-count">{tickets.length} total</span>
          </div>

          <div className="ticket-list">
            {tickets.map((ticket) => {
              const isDeleting = deletingTicketIds.includes(ticket.id);
              const isUpdating = updatingTicketIds.includes(ticket.id);

              return (
                <article className="ticket-card" key={ticket.id}>
                  <div className="ticket-card-body">
                    <div className="ticket-card-header">
                      <div className="ticket-title-block">
                        <span className="ticket-id">#{ticket.id}</span>
                        <div>
                          <h3>{ticket.subject}</h3>
                          <p className="ticket-description">{ticket.description}</p>
                        </div>
                      </div>
                      <StatusBadge value={ticket.status} />
                    </div>

                    <div className="ticket-metadata">
                      <div className="ticket-meta-item">
                        <span>Priority</span>
                        <StatusBadge value={ticket.priority} variant="priority" />
                      </div>
                      <div className="ticket-meta-item">
                        <span>Category</span>
                        <strong>{ticket.category ?? "Awaiting AI"}</strong>
                      </div>
                      <div className="ticket-meta-item">
                        <span>AI analysis</span>
                        <StatusBadge value={ticket.ai_status} variant="ai" />
                      </div>
                    </div>
                  </div>

                  {ticket.ai_status === "processing" && (
                    <div className="ai-insight ai-insight-processing" aria-live="polite">
                      <span className="ai-insight-icon"><Icon name="sparkles" /></span>
                      <div>
                        <h4>AI analysis</h4>
                        <p>AI analysis is running.</p>
                      </div>
                    </div>
                  )}

                  {ticket.ai_status === "failed" && (
                    <div className="ai-insight ai-insight-failed" role="alert">
                      <span className="ai-insight-icon"><Icon name="sparkles" /></span>
                      <div>
                        <h4>AI analysis failed</h4>
                        <p>{ticket.ai_error ?? "AI analysis failed."}</p>
                      </div>
                    </div>
                  )}

                  {ticket.ai_status === "completed" && (ticket.category || ticket.ai_summary) && (
                    <div className="ai-insight ai-insight-completed">
                      <span className="ai-insight-icon"><Icon name="sparkles" /></span>
                      <div>
                        <h4>AI triage summary</h4>
                        {ticket.category && <p>Category: {ticket.category}</p>}
                        {ticket.ai_summary && <p>AI Summary: {ticket.ai_summary}</p>}
                      </div>
                    </div>
                  )}

                  <footer className="ticket-card-footer">
                    <div className="status-control">
                      <label htmlFor={`ticket-status-${ticket.id}`}>Status</label>
                      <select
                        id={`ticket-status-${ticket.id}`}
                        value={ticket.status}
                        disabled={isUpdating}
                        onChange={(event) => {
                          void handleStatusChange(ticket, event.target.value);
                        }}
                      >
                        {TICKET_STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {formatStatus(status)}
                          </option>
                        ))}
                      </select>
                      {isUpdating && <span className="control-status">Updating...</span>}
                    </div>

                    <button
                      className="button button-danger-ghost"
                      type="button"
                      disabled={isDeleting}
                      onClick={() => {
                        void handleDelete(ticket);
                      }}
                    >
                      <Icon name="trash" size={16} />
                      {isDeleting ? "Deleting..." : "Delete"}
                    </button>
                  </footer>
                </article>
              );
            })}
          </div>
        </section>
      )}
    </AppLayout>
  );
}
