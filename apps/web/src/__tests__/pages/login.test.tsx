import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mockPush } from "../setup";

// Mock auth API
const mockLogin = vi.fn();
vi.mock("@/lib/api", () => ({
  auth: { login: (data: unknown) => mockLogin(data) },
}));

// Import after mocks
import LoginPage from "@/app/login/page";

describe("LoginPage", () => {
  beforeEach(() => {
    mockLogin.mockReset();
    mockPush.mockClear();
  });

  it("renders login form", () => {
    render(<LoginPage />);
    expect(screen.getByText("VeriDoc")).toBeInTheDocument();
    expect(screen.getByText("Sign in to your account")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("renders sign up link", () => {
    render(<LoginPage />);
    const link = screen.getByText("Sign up");
    expect(link).toHaveAttribute("href", "/register");
  });

  it("submits form and redirects on success", async () => {
    mockLogin.mockResolvedValue({ access_token: "jwt-token" });
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "mypassword");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: "test@example.com",
        password: "mypassword",
      });
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows error message on failed login", async () => {
    mockLogin.mockRejectedValue(new Error("Invalid credentials"));
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "test@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid credentials")).toBeInTheDocument();
    });
  });

  it("disables button while loading", async () => {
    mockLogin.mockReturnValue(new Promise(() => {})); // never resolves
    const user = userEvent.setup();
    render(<LoginPage />);

    await user.type(screen.getByLabelText("Email"), "t@t.com");
    await user.type(screen.getByLabelText("Password"), "pass1234");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Signing in..." })).toBeDisabled();
    });
  });
});
