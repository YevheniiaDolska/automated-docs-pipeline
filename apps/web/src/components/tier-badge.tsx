"use client";

const TIER_COLORS: Record<string, string> = {
  free: "bg-gray-100 text-gray-700",
  starter: "bg-blue-100 text-blue-700",
  pro: "bg-brand/10 text-brand",
  business: "bg-purple-100 text-purple-700",
  enterprise: "bg-amber-100 text-amber-800",
};

export default function TierBadge({ tier }: { tier: string }) {
  const cls = TIER_COLORS[tier] || TIER_COLORS.free;
  return (
    <span className={`inline-block rounded-full px-3 py-0.5 text-xs font-semibold capitalize ${cls}`}>
      {tier}
    </span>
  );
}
