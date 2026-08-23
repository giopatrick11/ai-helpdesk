import { FormEvent, useEffect, useState } from "react";

import api from "../api/client";

type Ticket = {
  id: number;
  subject: string;
  description: string;
  priority: string;
  status: string;
  category: string | null;
  ai_summary: string | null;
};

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadTickets() {
    try {
      const response = await api.get("/tickets/");
      setTickets(response.data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    await api.post("/tickets/", {
      subject,
      description,
    });

    setSubject("");
    setDescription("");

    await loadTickets();
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

      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        tickets.map((ticket) => (
          <div key={ticket.id}>
            <h2>{ticket.subject}</h2>

            <p>{ticket.description}</p>

            <p>Priority: {ticket.priority}</p>
            <p>Status: {ticket.status}</p>

            {ticket.category && <p>Category: {ticket.category}</p>}

            {ticket.ai_summary && <p>AI Summary: {ticket.ai_summary}</p>}

            <hr />
          </div>
        ))
      )}
    </div>
  );
}
