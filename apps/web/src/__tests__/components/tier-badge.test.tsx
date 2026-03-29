import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import TierBadge from "@/components/tier-badge";

describe("TierBadge", () => {
  it("renders tier name", () => {
    render(<TierBadge tier="pro" />);
    expect(screen.getByText("pro")).toBeInTheDocument();
  });

  it("applies correct color class for each tier", () => {
    const tiers = [
      { tier: "free", cls: "bg-gray-100" },
      { tier: "starter", cls: "bg-blue-100" },
      { tier: "pro", cls: "bg-brand/10" },
      { tier: "business", cls: "bg-purple-100" },
      { tier: "enterprise", cls: "bg-amber-100" },
    ];

    for (const { tier, cls } of tiers) {
      const { unmount } = render(<TierBadge tier={tier} />);
      expect(screen.getByText(tier).className).toContain(cls);
      unmount();
    }
  });

  it("falls back to free colors for unknown tier", () => {
    render(<TierBadge tier="unknown" />);
    expect(screen.getByText("unknown").className).toContain("bg-gray-100");
  });

  it("has capitalize class for display", () => {
    render(<TierBadge tier="starter" />);
    expect(screen.getByText("starter").className).toContain("capitalize");
  });
});
