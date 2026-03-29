"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/settings", label: "Settings" },
  { href: "/billing", label: "Billing" },
  { href: "/onboarding", label: "Onboarding" },
  { href: "/referral-terms", label: "Referrals" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 flex-col border-r border-line bg-surface px-3 py-6">
      <Link href="/dashboard" className="mb-8 px-3 text-xl font-extrabold text-brand">
        VeriDoc
      </Link>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-brand/10 text-brand"
                  : "text-muted hover:bg-gray-100 hover:text-ink"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <button
        className="mt-auto px-3 py-2 text-left text-sm text-muted hover:text-ink"
        onClick={() => {
          localStorage.removeItem("veridoc_token");
          window.location.href = "/login";
        }}
      >
        Log out
      </button>
    </aside>
  );
}
