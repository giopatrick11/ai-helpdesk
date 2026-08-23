import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import api from "../api/client";

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
  const navigate = useNavigate();

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

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  if (loading) {
    return <p>Loading...</p>;
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
    <div>
      <h1>Dashboard</h1>

      {error && <p>{error}</p>}

      <section>
        <h2>Account</h2>

        {user && (
          <>
            <p>Welcome, {user.name}</p>
            <p>{user.email}</p>
          </>
        )}
      </section>

      <section>
        <h2>Ticket Summary</h2>

        <p>Total tickets: {tickets.length}</p>
        <p>Open tickets: {openTickets}</p>
        <p>Resolved tickets: {resolvedTickets}</p>
      </section>

      <section>
        <h2>Knowledge Base Summary</h2>

        <p>Total documents: {documents.length}</p>
        <p>Ready documents: {readyDocuments}</p>
        <p>Processing documents: {processingDocuments}</p>
      </section>

      <section>
        <h2>Navigation</h2>

        <nav>
          <Link to="/tickets">Tickets</Link>
          {" | "}
          <Link to="/documents">Documents</Link>
        </nav>
      </section>

      <button onClick={handleLogout}>Logout</button>
    </div>
  );
}
