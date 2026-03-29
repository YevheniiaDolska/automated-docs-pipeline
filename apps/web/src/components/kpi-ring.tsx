"use client";

interface KpiRingProps {
  value: number;
  max?: number;
  size?: number;
  label?: string;
}

export default function KpiRing({ value, max = 100, size = 96, label }: KpiRingProps) {
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const r = (size - 10) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  const color = pct >= 0.8 ? "#16a34a" : pct >= 0.5 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={8}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <span className="mt-1 text-lg font-bold" style={{ color }}>
        {Math.round(pct * 100)}%
      </span>
      {label && <span className="text-xs text-muted">{label}</span>}
    </div>
  );
}
