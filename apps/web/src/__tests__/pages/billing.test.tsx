import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock API modules
const mockGetUsage = vi.fn();
const mockGetPlans = vi.fn();
const mockGetPortal = vi.fn();
const mockCreateCheckout = vi.fn();

vi.mock("@/lib/api", () => ({
  billing: {
    getUsage: () => mockGetUsage(),
    getPortal: () => mockGetPortal(),
    createCheckout: (tier: string) => mockCreateCheckout(tier),
  },
  pricing: {
    getPlans: () => mockGetPlans(),
  },
}));

vi.mock("@/components/auth-guard", () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/app-shell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import BillingPage from "@/app/billing/page";

const MOCK_USAGE = {
  tier: "starter",
  status: "active",
  ai_requests_used: 50,
  ai_requests_limit: 200,
  pages_generated: 10,
  pages_limit: 50,
  api_calls_used: 3,
  api_calls_limit: 20,
  current_period_end: "2026-04-15T00:00:00Z",
  trial_ends_at: null,
};

describe("BillingPage", () => {
  beforeEach(() => {
    mockGetUsage.mockResolvedValue(MOCK_USAGE);
    mockGetPlans.mockResolvedValue([]);
    mockGetPortal.mockResolvedValue({ portal_url: "https://billing.example.com" });
    mockCreateCheckout.mockReset();
  });

  it("renders page title", () => {
    render(<BillingPage />);
    expect(screen.getByText("Billing")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    mockGetUsage.mockReturnValue(new Promise(() => {}));
    render(<BillingPage />);
    expect(screen.getByText("Loading billing...")).toBeInTheDocument();
  });

  it("shows current plan after loading", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Current plan")).toBeInTheDocument();
      expect(screen.getByText("starter")).toBeInTheDocument();
    });
  });

  it("shows usage meters", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("AI requests")).toBeInTheDocument();
      expect(screen.getByText("Pages generated")).toBeInTheDocument();
      expect(screen.getByText("API calls")).toBeInTheDocument();
    });
  });

  it("shows business chain status", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Payment")).toBeInTheDocument();
      expect(screen.getByText("Plan active")).toBeInTheDocument();
      expect(screen.getByText("Limits applied")).toBeInTheDocument();
      expect(screen.getByText("Pipeline access")).toBeInTheDocument();
      expect(screen.getByText("Reports ready")).toBeInTheDocument();
    });
  });

  it("shows manage subscription link", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      const link = screen.getByText("Manage subscription");
      expect(link).toHaveAttribute("href", "https://billing.example.com");
    });
  });

  it("shows renewal days", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText(/Renews in \d+ days/)).toBeInTheDocument();
    });
  });

  it("shows enterprise contact section", async () => {
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Need enterprise pricing?")).toBeInTheDocument();
      expect(screen.getByText("Book a call")).toBeInTheDocument();
      expect(screen.getByText("Referral program")).toBeInTheDocument();
    });
  });

  it("shows available plans when loaded", async () => {
    mockGetPlans.mockResolvedValue([
      { tier: "starter", price_monthly: 149, ai_requests_limit: 200, pages_limit: 50, api_calls_limit: 20 },
      { tier: "pro", price_monthly: 399, ai_requests_limit: 500, pages_limit: 100, api_calls_limit: 50 },
    ]);

    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Available plans")).toBeInTheDocument();
      expect(screen.getByText("$149")).toBeInTheDocument();
      expect(screen.getByText("$399")).toBeInTheDocument();
    });
  });

  it("highlights current plan in comparison", async () => {
    mockGetPlans.mockResolvedValue([
      { tier: "starter", price_monthly: 149, ai_requests_limit: 200, pages_limit: 50, api_calls_limit: 20 },
    ]);

    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Current")).toBeInTheDocument();
    });
  });

  it("shows upgrade button for non-current plans", async () => {
    mockGetPlans.mockResolvedValue([
      { tier: "pro", price_monthly: 399, ai_requests_limit: 500, pages_limit: 100, api_calls_limit: 50 },
    ]);

    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Upgrade" })).toBeInTheDocument();
    });
  });

  it("handles checkout on upgrade click", async () => {
    mockGetPlans.mockResolvedValue([
      { tier: "pro", price_monthly: 399, ai_requests_limit: 500, pages_limit: 100, api_calls_limit: 50 },
    ]);
    mockCreateCheckout.mockResolvedValue({ checkout_url: "https://checkout.example.com" });

    // Mock window.location.href
    const originalLocation = window.location;
    Object.defineProperty(window, "location", {
      writable: true,
      value: { ...originalLocation, href: "" },
    });

    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Upgrade" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Upgrade" }));

    await waitFor(() => {
      expect(mockCreateCheckout).toHaveBeenCalledWith("pro");
    });

    Object.defineProperty(window, "location", {
      writable: true,
      value: originalLocation,
    });
  });

  it("shows error on usage load failure", async () => {
    mockGetUsage.mockRejectedValue(new Error("Network error"));
    render(<BillingPage />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });
});
