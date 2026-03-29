import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock all API modules
const mockMe = vi.fn();
const mockGetUsage = vi.fn();
const mockAutomationList = vi.fn();
const mockSettingsGet = vi.fn();
const mockPipelineRun = vi.fn();

vi.mock("@/lib/api", () => ({
  auth: { me: () => mockMe() },
  billing: { getUsage: () => mockGetUsage() },
  automation: { list: () => mockAutomationList() },
  settings: { get: () => mockSettingsGet() },
  pipeline: { run: (opts: unknown) => mockPipelineRun(opts) },
}));

// Mock AuthGuard to just render children (tested separately)
vi.mock("@/components/auth-guard", () => ({
  default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock AppShell to just render children (tested separately)
vi.mock("@/components/app-shell", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import DashboardPage from "@/app/dashboard/page";

const MOCK_USAGE = {
  tier: "pro",
  status: "active",
  ai_requests_used: 120,
  ai_requests_limit: 500,
  pages_generated: 25,
  pages_limit: 100,
  api_calls_used: 8,
  api_calls_limit: 50,
  current_period_end: "2026-04-15T00:00:00Z",
};

describe("DashboardPage", () => {
  beforeEach(() => {
    mockMe.mockResolvedValue({ email: "user@test.com" });
    mockGetUsage.mockResolvedValue(MOCK_USAGE);
    mockAutomationList.mockResolvedValue({ schedules: [] });
    mockSettingsGet.mockReset();
    mockPipelineRun.mockReset();
  });

  it("renders page title", async () => {
    render(<DashboardPage />);
    expect(screen.getByText("Pipeline Dashboard")).toBeInTheDocument();
  });

  it("shows welcome banner with email", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Welcome back/)).toBeInTheDocument();
      expect(screen.getByText(/user@test.com/)).toBeInTheDocument();
    });
  });

  it("shows usage meters after data loads", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("AI requests")).toBeInTheDocument();
      expect(screen.getByText("Pages generated")).toBeInTheDocument();
      expect(screen.getByText("API calls")).toBeInTheDocument();
    });
  });

  it("shows business chain status dots", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Payment")).toBeInTheDocument();
      expect(screen.getByText("Plan active")).toBeInTheDocument();
      expect(screen.getByText("Limits OK")).toBeInTheDocument();
      expect(screen.getByText("Pipeline")).toBeInTheDocument();
      expect(screen.getByText("Reports")).toBeInTheDocument();
    });
  });

  it("shows Run Pipeline button", () => {
    render(<DashboardPage />);
    expect(screen.getByRole("button", { name: "Run Pipeline" })).toBeInTheDocument();
  });

  it("runs pipeline on button click", async () => {
    mockSettingsGet.mockResolvedValue({
      settings: {
        flow_mode: "hybrid",
        default_protocols: ["rest"],
        algolia_enabled: false,
        sandbox_backend: "external",
        modules: [],
      },
    });
    mockPipelineRun.mockResolvedValue({
      phases: [{ name: "validate", status: "ok", duration_seconds: 1.5 }],
      errors: [],
      artifacts: [],
      report: null,
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run Pipeline" })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    await waitFor(() => {
      expect(mockPipelineRun).toHaveBeenCalled();
    });
  });

  it("shows error on pipeline failure", async () => {
    mockSettingsGet.mockResolvedValue({
      settings: {
        flow_mode: "hybrid",
        default_protocols: [],
        algolia_enabled: false,
        sandbox_backend: "external",
        modules: [],
      },
    });
    mockPipelineRun.mockRejectedValue(new Error("Pipeline timed out"));

    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Run Pipeline" })).toBeEnabled();
    });

    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    await waitFor(() => {
      expect(screen.getByText("Pipeline timed out")).toBeInTheDocument();
    });
  });

  it("shows no schedules message when empty", async () => {
    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/No schedules configured/)).toBeInTheDocument();
    });
  });

  it("renders automation schedules when present", async () => {
    mockAutomationList.mockResolvedValue({
      schedules: [
        { id: "s1", name: "Nightly docs", cron: "0 2 * * *", enabled: true },
      ],
    });

    render(<DashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Nightly docs")).toBeInTheDocument();
      expect(screen.getByText("0 2 * * *")).toBeInTheDocument();
    });
  });
});
