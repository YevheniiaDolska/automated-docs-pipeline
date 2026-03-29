import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import Sidebar from "@/components/sidebar";

describe("Sidebar", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders VeriDoc brand link", () => {
    render(<Sidebar />);
    expect(screen.getByText("VeriDoc")).toBeInTheDocument();
  });

  it("renders all nav items", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Billing")).toBeInTheDocument();
    expect(screen.getByText("Onboarding")).toBeInTheDocument();
    expect(screen.getByText("Referrals")).toBeInTheDocument();
  });

  it("renders log out button", () => {
    render(<Sidebar />);
    expect(screen.getByText("Log out")).toBeInTheDocument();
  });

  it("clears veridoc_token on log out", () => {
    localStorage.setItem("veridoc_token", "test-token");
    render(<Sidebar />);

    // Mock window.location.href
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, href: "" },
    });

    fireEvent.click(screen.getByText("Log out"));
    expect(localStorage.getItem("veridoc_token")).toBeNull();

    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });

  it("nav links have correct hrefs", () => {
    render(<Sidebar />);
    expect(screen.getByText("Dashboard").closest("a")).toHaveAttribute("href", "/dashboard");
    expect(screen.getByText("Settings").closest("a")).toHaveAttribute("href", "/settings");
    expect(screen.getByText("Billing").closest("a")).toHaveAttribute("href", "/billing");
  });
});
