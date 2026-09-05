import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";

import ProtectedRoute from "./ProtectedRoute";

function renderProtectedRoute() {
  return render(
    <MemoryRouter initialEntries={["/private"]}>
      <Routes>
        <Route path="/login" element={<p>Login page</p>} />
        <Route
          path="/private"
          element={(
            <ProtectedRoute>
              <p>Private content</p>
            </ProtectedRoute>
          )}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects visitors without a token", () => {
    renderProtectedRoute();
    expect(screen.getByText("Login page")).toBeInTheDocument();
  });

  it("renders protected content when a token exists", () => {
    localStorage.setItem("access_token", "test-token");
    renderProtectedRoute();
    expect(screen.getByText("Private content")).toBeInTheDocument();
  });
});
