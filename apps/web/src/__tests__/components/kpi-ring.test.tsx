import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import KpiRing from "@/components/kpi-ring";

describe("KpiRing", () => {
  it("renders percentage text", () => {
    render(<KpiRing value={80} max={100} />);
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("renders label when provided", () => {
    render(<KpiRing value={50} label="Latest run" />);
    expect(screen.getByText("Latest run")).toBeInTheDocument();
  });

  it("does not render label when not provided", () => {
    const { container } = render(<KpiRing value={50} />);
    expect(container.querySelectorAll(".text-xs")).toHaveLength(0);
  });

  it("uses green color for 80%+ values", () => {
    render(<KpiRing value={85} max={100} />);
    const percentEl = screen.getByText("85%");
    expect(percentEl).toHaveStyle({ color: "#16a34a" });
  });

  it("uses amber color for 50-79% values", () => {
    render(<KpiRing value={60} max={100} />);
    const percentEl = screen.getByText("60%");
    expect(percentEl).toHaveStyle({ color: "#f59e0b" });
  });

  it("uses red color for below 50% values", () => {
    render(<KpiRing value={30} max={100} />);
    const percentEl = screen.getByText("30%");
    expect(percentEl).toHaveStyle({ color: "#ef4444" });
  });

  it("renders SVG with specified size", () => {
    const { container } = render(<KpiRing value={50} size={120} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "120");
    expect(svg).toHaveAttribute("height", "120");
  });

  it("defaults max to 100", () => {
    render(<KpiRing value={50} />);
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  it("handles zero max", () => {
    render(<KpiRing value={0} max={0} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
