import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import AppShell from "@/components/app-shell";

describe("AppShell", () => {
  it("renders children inside main content area", () => {
    render(
      <AppShell>
        <div>Page content</div>
      </AppShell>,
    );
    expect(screen.getByText("Page content")).toBeInTheDocument();
  });

  it("renders sidebar with VeriDoc brand", () => {
    render(
      <AppShell>
        <div>Content</div>
      </AppShell>,
    );
    expect(screen.getByText("VeriDoc")).toBeInTheDocument();
  });

  it("renders sidebar navigation items", () => {
    render(
      <AppShell>
        <div>Content</div>
      </AppShell>,
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Billing")).toBeInTheDocument();
  });
});
