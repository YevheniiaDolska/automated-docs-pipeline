import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import UsageMeter from "@/components/usage-meter";

describe("UsageMeter", () => {
  it("renders label and usage text", () => {
    render(<UsageMeter label="AI requests" used={50} limit={100} />);
    expect(screen.getByText("AI requests")).toBeInTheDocument();
    expect(screen.getByText(/50/)).toBeInTheDocument();
    expect(screen.getByText(/100/)).toBeInTheDocument();
  });

  it("renders unit suffix when provided", () => {
    render(<UsageMeter label="Storage" used={5} limit={10} unit=" GB" />);
    expect(screen.getByText(/5 GB/)).toBeInTheDocument();
    expect(screen.getByText(/10 GB/)).toBeInTheDocument();
  });

  it("calculates percentage width correctly", () => {
    const { container } = render(<UsageMeter label="Pages" used={75} limit={100} />);
    const bar = container.querySelector("[style]");
    expect(bar).toHaveStyle({ width: "75%" });
  });

  it("caps percentage at 100%", () => {
    const { container } = render(<UsageMeter label="Pages" used={150} limit={100} />);
    const bar = container.querySelector("[style]");
    expect(bar).toHaveStyle({ width: "100%" });
  });

  it("handles zero limit without crashing", () => {
    const { container } = render(<UsageMeter label="Pages" used={0} limit={0} />);
    const bar = container.querySelector("[style]");
    expect(bar).toHaveStyle({ width: "0%" });
  });

  it("applies red color at 90%+ usage", () => {
    const { container } = render(<UsageMeter label="X" used={95} limit={100} />);
    const bar = container.querySelector("[style]");
    expect(bar?.className).toContain("bg-red-500");
  });

  it("applies amber color at 70-89% usage", () => {
    const { container } = render(<UsageMeter label="X" used={75} limit={100} />);
    const bar = container.querySelector("[style]");
    expect(bar?.className).toContain("bg-amber-500");
  });

  it("applies brand color below 70% usage", () => {
    const { container } = render(<UsageMeter label="X" used={50} limit={100} />);
    const bar = container.querySelector("[style]");
    expect(bar?.className).toContain("bg-brand");
  });
});
