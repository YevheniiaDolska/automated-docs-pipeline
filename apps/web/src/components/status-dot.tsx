"use client";

const DOT_COLORS: Record<string, string> = {
  ok: "bg-ok",
  warn: "bg-amber-500",
  error: "bg-red-500",
  idle: "bg-gray-300",
};

interface StatusDotProps {
  status: "ok" | "warn" | "error" | "idle";
  label?: string;
}

export default function StatusDot({ status, label }: StatusDotProps) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <span className={`inline-block h-2.5 w-2.5 rounded-full ${DOT_COLORS[status]}`} />
      {label && <span className="text-muted">{label}</span>}
    </span>
  );
}
