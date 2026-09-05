import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import api from "../api/client";
import DashboardPage from "./DashboardPage";

vi.mock("../api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation((url) => {
      if (url === "/auth/me") {
        return Promise.resolve({
          data: { id: 1, name: "Ada", email: "ada@example.com" },
        });
      }

      if (url === "/tickets/") {
        return Promise.resolve({
          data: [
            { id: 1, status: "open" },
            { id: 2, status: "resolved" },
          ],
        });
      }

      return Promise.resolve({
        data: [
          { id: 1, status: "ready" },
          { id: 2, status: "processing" },
        ],
      });
    });
  });

  it("renders account and summary metrics", async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Welcome, Ada")).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByText("Total tickets").nextElementSibling).toHaveTextContent("2");
    expect(screen.getByText("Ready documents").nextElementSibling).toHaveTextContent("1");
  });
});
