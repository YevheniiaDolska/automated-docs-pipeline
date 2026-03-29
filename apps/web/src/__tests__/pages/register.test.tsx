import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mockPush } from "../setup";

// Mock auth API
const mockRegister = vi.fn();
const mockLogin = vi.fn();
vi.mock("@/lib/api", () => ({
  auth: {
    register: (data: unknown) => mockRegister(data),
    login: (data: unknown) => mockLogin(data),
  },
}));

import RegisterPage from "@/app/register/page";

describe("RegisterPage", () => {
  beforeEach(() => {
    mockRegister.mockReset();
    mockLogin.mockReset();
    mockPush.mockClear();
  });

  it("renders registration form", () => {
    render(<RegisterPage />);
    expect(screen.getByText("VeriDoc")).toBeInTheDocument();
    expect(screen.getByText("Create your account")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create account" })).toBeInTheDocument();
  });

  it("renders sign in link", () => {
    render(<RegisterPage />);
    expect(screen.getByText("Sign in")).toHaveAttribute("href", "/login");
  });

  it("shows error when passwords do not match", async () => {
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "password1");
    await user.type(screen.getByLabelText("Confirm password"), "password2");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(screen.getByText("Passwords do not match")).toBeInTheDocument();
    });
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it("registers, logs in, and redirects to onboarding on success", async () => {
    mockRegister.mockResolvedValue({ id: 1, email: "a@b.com" });
    mockLogin.mockResolvedValue({ access_token: "new-token" });
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "password1");
    await user.type(screen.getByLabelText("Confirm password"), "password1");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith({
        email: "a@b.com",
        password: "password1",
      });
      expect(mockLogin).toHaveBeenCalledWith({
        email: "a@b.com",
        password: "password1",
      });
      expect(mockPush).toHaveBeenCalledWith("/onboarding");
    });
  });

  it("shows error on registration failure", async () => {
    mockRegister.mockRejectedValue(new Error("Email already exists"));
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "password1");
    await user.type(screen.getByLabelText("Confirm password"), "password1");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(screen.getByText("Email already exists")).toBeInTheDocument();
    });
  });

  it("disables button while loading", async () => {
    mockRegister.mockReturnValue(new Promise(() => {}));
    const user = userEvent.setup();
    render(<RegisterPage />);

    await user.type(screen.getByLabelText("Email"), "a@b.com");
    await user.type(screen.getByLabelText("Password"), "password1");
    await user.type(screen.getByLabelText("Confirm password"), "password1");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Creating account..." })).toBeDisabled();
    });
  });
});
