"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  type UsageResponse,
  type PortalResponse,
  billing as billingApi,
  pricing as pricingApi,
} from "@/lib/api";
import AuthGuard from "@/components/auth-guard";
import AppShell from "@/components/app-shell";
import TierBadge from "@/components/tier-badge";
import UsageMeter from "@/components/usage-meter";
import StatusDot from "@/components/status-dot";

// ---------------------------------------------------------------------------
// Business chain steps
// ---------------------------------------------------------------------------

interface ChainStep {
  label: string;
  check: (u: UsageResponse) => "ok" | "warn" | "error" | "idle";
}

const CHAIN_STEPS: ChainStep[] = [
  {
    label: "Payment",
    check: (u) => (u.status === "active" || u.status === "trialing" ? "ok" : "error"),
  },
  {
    label: "Plan active",
    check: (u) => (u.tier !== "free" ? "ok" : "idle"),
  },
  {
    label: "Limits applied",
    check: (u) =>
      u.ai_requests_used < u.ai_requests_limit &&
      u.pages_generated < u.pages_limit &&
      u.api_calls_used < u.api_calls_limit
        ? "ok"
        : "warn",
  },
  {
    label: "Pipeline access",
    check: (u) => (u.status === "active" || u.status === "trialing" ? "ok" : "error"),
  },
  {
    label: "Reports ready",
    check: () => "ok",
  },
];

// ---------------------------------------------------------------------------
// Tier display order
// ---------------------------------------------------------------------------

const TIER_ORDER = ["free", "starter", "pro", "business", "enterprise"];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

function BillingContent() {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [plans, setPlans] = useState<Record<string, unknown>[]>([]);
  const [portalUrl, setPortalUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checkingOut, setCheckingOut] = useState<string | null>(null);

  useEffect(() => {
    billingApi.getUsage().then(setUsage).catch((e) => setError(e.message));
    pricingApi.getPlans().then(setPlans).catch(() => {});
    billingApi.getPortal().then((r) => setPortalUrl(r.portal_url)).catch(() => {});
  }, []);

  if (!usage) {
    return (
      <div className="py-12 text-center text-muted">
        {error ? (
          <div className="rounded border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          "Loading billing..."
        )}
      </div>
    );
  }

  const daysUntilRenewal = usage.current_period_end
    ? Math.max(0, Math.ceil((new Date(usage.current_period_end).getTime() - Date.now()) / 86400000))
    : null;

  async function handleCheckout(tier: string) {
    setCheckingOut(tier);
    try {
      const res = await billingApi.createCheckout(tier);
      window.location.href = res.checkout_url;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkout failed");
      setCheckingOut(null);
    }
  }

  return (
    <div className="space-y-8">
      {/* Current plan */}
      <section className="rounded-xl border bg-surface p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Current plan</h2>
            <div className="mt-2 flex items-center gap-3">
              <TierBadge tier={usage.tier} />
              <span className="text-sm text-muted">
                {usage.status === "trialing" && usage.trial_ends_at
                  ? `Trial ends ${new Date(usage.trial_ends_at).toLocaleDateString()}`
                  : daysUntilRenewal !== null
                    ? `Renews in ${daysUntilRenewal} days`
                    : ""}
              </span>
            </div>
          </div>
          {portalUrl && (
            <a
              href={portalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md border border-brand px-4 py-2 text-sm font-medium text-brand hover:bg-brand/5"
            >
              Manage subscription
            </a>
          )}
        </div>
      </section>

      {/* Usage meters */}
      <section className="rounded-xl border bg-surface p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Usage this period</h2>
        <div className="mt-4 space-y-4">
          <UsageMeter
            label="AI requests"
            used={usage.ai_requests_used}
            limit={usage.ai_requests_limit}
          />
          <UsageMeter
            label="Pages generated"
            used={usage.pages_generated}
            limit={usage.pages_limit}
          />
          <UsageMeter
            label="API calls"
            used={usage.api_calls_used}
            limit={usage.api_calls_limit}
          />
        </div>
      </section>

      {/* Business chain status */}
      <section className="rounded-xl border bg-surface p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Business chain</h2>
        <p className="mt-1 text-sm text-muted">
          End-to-end status from payment to delivered reports.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          {CHAIN_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-2">
              <StatusDot status={step.check(usage)} label={step.label} />
              {i < CHAIN_STEPS.length - 1 && (
                <span className="text-muted">&rarr;</span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Plan comparison */}
      {plans.length > 0 && (
        <section className="rounded-xl border bg-surface p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Available plans</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {plans
              .sort((a, b) => TIER_ORDER.indexOf(String(a.tier)) - TIER_ORDER.indexOf(String(b.tier)))
              .map((plan) => {
                const tier = String(plan.tier);
                const isCurrent = tier === usage.tier;
                return (
                  <div
                    key={tier}
                    className={`rounded-lg border p-4 ${
                      isCurrent ? "border-brand bg-brand/5" : "border-line"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <TierBadge tier={tier} />
                      {isCurrent && (
                        <span className="text-xs font-medium text-brand">Current</span>
                      )}
                    </div>
                    <div className="mt-3">
                      <span className="text-2xl font-bold">
                        ${Number(plan.price_monthly ?? 0)}
                      </span>
                      <span className="text-sm text-muted">/mo</span>
                    </div>
                    <ul className="mt-3 space-y-1 text-sm text-muted">
                      {plan.ai_requests_limit != null && (
                        <li>{Number(plan.ai_requests_limit).toLocaleString()} AI requests</li>
                      )}
                      {plan.pages_limit != null && (
                        <li>{Number(plan.pages_limit).toLocaleString()} pages</li>
                      )}
                      {plan.api_calls_limit != null && (
                        <li>{Number(plan.api_calls_limit).toLocaleString()} API calls</li>
                      )}
                    </ul>
                    {!isCurrent && tier !== "free" && (
                      <button
                        onClick={() => handleCheckout(tier)}
                        disabled={checkingOut === tier}
                        className="mt-4 w-full rounded-md bg-brand py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:opacity-50"
                      >
                        {checkingOut === tier ? "Redirecting..." : "Upgrade"}
                      </button>
                    )}
                  </div>
                );
              })}
          </div>
        </section>
      )}

      {/* Invoice / Contact */}
      <section className="rounded-xl border bg-surface p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Need enterprise pricing?</h2>
        <p className="mt-1 text-sm text-muted">
          Contact us for custom pricing, volume discounts, or invoice-based billing.
        </p>
        <div className="mt-4 flex gap-3">
          <a
            href="https://calendly.com/eugenia-sorokina/veriops-discovery-call"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand/90"
          >
            Book a call
          </a>
          <Link
            href="/settings#referrals"
            className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-gray-50"
          >
            Referral program
          </Link>
        </div>
      </section>
    </div>
  );
}

export default function BillingPage() {
  return (
    <AuthGuard>
      <AppShell>
        <div className="mx-auto max-w-4xl px-4 py-8">
          <h1 className="text-2xl font-bold">Billing</h1>
          <p className="mt-1 text-muted">Manage your subscription, usage, and invoices.</p>
          <div className="mt-6">
            <BillingContent />
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
