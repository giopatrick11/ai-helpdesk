import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import api from "../api/client";

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
    loadTickets();
  }, [loadTickets]);

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
    return <p>Loading tickets...</p>;
  }

  return (
    <div>
      <h1>Tickets</h1>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="subject">Subject</label>

          <input
            id="subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="description">Description</label>

          <textarea
            id="description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
          />
        </div>

        <button type="submit">Create Ticket</button>
      </form>

      <hr />

      {loadError && <p>{loadError}</p>}
      {deleteError && <p>{deleteError}</p>}
      {updateError && <p>{updateError}</p>}

      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        tickets.map((ticket) => {
          const isDeleting = deletingTicketIds.includes(ticket.id);
          const isUpdating = updatingTicketIds.includes(ticket.id);

          return (
            <div key={ticket.id}>
              <h2>{ticket.subject}</h2>

              <p>{ticket.description}</p>

              <p>Priority: {ticket.priority}</p>
              <div>
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
                      {status}
                    </option>
                  ))}
                </select>

                {isUpdating && <span> Updating...</span>}
              </div>

              {ticket.ai_status === "processing" && (
                <p>AI analysis: Processing...</p>
              )}

              {ticket.ai_status === "failed" && (
                <p>AI analysis failed.</p>
              )}

              {ticket.ai_status === "completed" && ticket.category && (
                <p>Category: {ticket.category}</p>
              )}

              {ticket.ai_status === "completed" && ticket.ai_summary && (
                <p>AI Summary: {ticket.ai_summary}</p>
              )}

              <button
                type="button"
                disabled={isDeleting}
                onClick={() => {
                  void handleDelete(ticket);
                }}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>

              <hr />
            </div>
          );
        })
      )}
    </div>
  );
}
