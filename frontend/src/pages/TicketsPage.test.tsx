import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../api/client";
import TicketsPage from "./TicketsPage";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("TicketsPage", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          id: 1,
          subject: "Pending ticket",
          description: "Waiting for AI.",
          priority: "medium",
          status: "open",
          category: null,
          ai_summary: null,
          ai_status: "processing",
          ai_error: null,
        },
        {
          id: 2,
          subject: "Completed ticket",
          description: "AI finished.",
          priority: "high",
          status: "in_progress",
          category: "Account Access",
          ai_summary: "Reset assistance is needed.",
          ai_status: "completed",
          ai_error: null,
        },
        {
          id: 3,
          subject: "Failed ticket",
          description: "AI failed.",
          priority: "medium",
          status: "open",
          category: null,
          ai_summary: null,
          ai_status: "failed",
          ai_error: "Ticket AI analysis failed.",
        },
      ],
    });
  });

  it("renders pending, completed, and failed AI states", async () => {
    render(
      <MemoryRouter>
        <TicketsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Pending ticket")).toBeInTheDocument();
    expect(screen.getByText("AI analysis is running.")).toBeInTheDocument();
    expect(screen.getByText(/Category: Account Access/)).toBeInTheDocument();
    expect(screen.getByText(/Reset assistance is needed/)).toBeInTheDocument();
    expect(screen.getByText("Ticket AI analysis failed.")).toBeInTheDocument();
  });
});
