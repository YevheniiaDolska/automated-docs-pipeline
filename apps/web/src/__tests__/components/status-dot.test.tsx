import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatusDot from "@/components/status-dot";

describe("StatusDot", () => {
  it("renders label when provided", () => {
    render(<StatusDot status="ok" label="Payment" />);
    expect(screen.getByText("Payment")).toBeInTheDocument();
  });

  it("renders without label", () => {
    const { container } = render(<StatusDot status="ok" />);
    expect(container.querySelector(".rounded-full")).toBeInTheDocument();
  });

  it("applies ok color class", () => {
    const { container } = render(<StatusDot status="ok" />);
    expect(container.querySelector(".bg-ok")).toBeInTheDocument();
  });

  it("applies warn color class", () => {
    const { container } = render(<StatusDot status="warn" />);
    expect(container.querySelector(".bg-amber-500")).toBeInTheDocument();
  });

  it("applies error color class", () => {
    const { container } = render(<StatusDot status="error" />);
    expect(container.querySelector(".bg-red-500")).toBeInTheDocument();
  });

  it("applies idle color class", () => {
    const { container } = render(<StatusDot status="idle" />);
    expect(container.querySelector(".bg-gray-300")).toBeInTheDocument();
  });
});
