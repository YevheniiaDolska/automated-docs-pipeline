import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AuthGuard from "@/components/auth-guard";
import { mockReplace } from "../setup";

// Mock api.auth.me()
const mockMe = vi.fn();
vi.mock("@/lib/api", () => ({
  auth: { me: () => mockMe() },
}));

describe("AuthGuard", () => {
  beforeEach(() => {
    localStorage.clear();
    mockMe.mockReset();
    mockReplace.mockClear();
  });

  it("shows loading state initially", () => {
    localStorage.setItem("veridoc_token", "valid-token");
    mockMe.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    expect(screen.getByText("Authenticating...")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("redirects to login when no token", () => {
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    expect(mockReplace).toHaveBeenCalledWith("/login");
  });

  it("renders children when auth succeeds", async () => {
    localStorage.setItem("veridoc_token", "valid-token");
    mockMe.mockResolvedValue({ email: "test@example.com" });
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(screen.getByText("Protected content")).toBeInTheDocument();
    });
  });

  it("redirects and clears token when auth fails", async () => {
    localStorage.setItem("veridoc_token", "expired-token");
    mockMe.mockRejectedValue(new Error("Unauthorized"));
    render(
      <AuthGuard>
        <div>Protected content</div>
      </AuthGuard>,
    );
    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/login");
    });
    expect(localStorage.getItem("veridoc_token")).toBeNull();
  });
});
