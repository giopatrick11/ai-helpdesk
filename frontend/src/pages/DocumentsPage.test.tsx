import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../api/client";
import DocumentsPage from "./DocumentsPage";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe("DocumentsPage", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockResolvedValue({
      data: [
        {
          id: 1,
          title: "Processing document",
          filename: "processing.pdf",
          status: "processing",
          processing_error: null,
          created_at: "2026-09-05T04:00:00Z",
        },
        {
          id: 2,
          title: "Ready document",
          filename: "ready.pdf",
          status: "ready",
          processing_error: null,
          created_at: "2026-09-05T04:00:00Z",
        },
      ],
    });
  });

  it("renders processing and ready document states", async () => {
    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Processing document")).toBeInTheDocument();
    expect(screen.getByText("Ready document")).toBeInTheDocument();
    expect(screen.getByText("Processing")).toBeInTheDocument();
    expect(screen.getByText("Ready")).toBeInTheDocument();
  });

  it("renders a RAG answer with no sources", async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: {
        answer: "I do not have enough information to answer that.",
        sources: [],
      },
    });
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <DocumentsPage />
      </MemoryRouter>,
    );

    await screen.findByText("Ready document");
    await user.type(screen.getByLabelText("Question"), "Unknown policy?");
    await user.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByText(
      "I do not have enough information to answer that.",
    )).toBeInTheDocument();
    expect(screen.getByText("No sources returned.")).toBeInTheDocument();
  });
});
