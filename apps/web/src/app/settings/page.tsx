"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type ReferralSummaryResponse,
  type ModuleInfo,
  type PipelineSettings,
  type SettingsResponse,
  billing as billingApi,
  settings as settingsApi,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FLOW_MODES = [
  { value: "hybrid", label: "Hybrid", desc: "API-first + code-first combined" },
  { value: "api-first", label: "API-first", desc: "OpenAPI spec is source of truth" },
  { value: "code-first", label: "Code-first", desc: "Source code is source of truth" },
];

const SANDBOX_BACKENDS = [
  { value: "external", label: "External (Postman)" },
  { value: "docker", label: "Docker (Prism)" },
  { value: "prism", label: "Local Prism" },
];

const PROTOCOL_OPTIONS = [
  { value: "rest", label: "REST (OpenAPI)" },
  { value: "graphql", label: "GraphQL" },
  { value: "grpc", label: "gRPC" },
  { value: "asyncapi", label: "AsyncAPI" },
  { value: "websocket", label: "WebSocket" },
];

const TIER_LABELS: Record<string, string> = {
  starter: "Starter",
  pro: "Pro",
  business: "Business",
  enterprise: "Enterprise",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const [data, setData] = useState<SettingsResponse | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [referrals, setReferrals] = useState<ReferralSummaryResponse | null>(null);
  const [savingReferrals, setSavingReferrals] = useState(false);
  const [payoutRecipientId, setPayoutRecipientId] = useState("");
  const [payoutEmail, setPayoutEmail] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await settingsApi.get();
      setData(res);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    }
  }, []);

  useEffect(() => {
    load();
    billingApi.getReferrals().then((res) => {
      setReferrals(res);
      setPayoutRecipientId(res.profile.payout_recipient_id ?? "");
      setPayoutEmail(res.profile.payout_email ?? "");
    }).catch(() => {});
  }, [load]);

  const saveReferralSettings = useCallback(async (updates: Record<string, unknown>) => {
    setSavingReferrals(true);
    try {
      const res = await billingApi.updateReferrals(updates);
      setReferrals(res);
      setError(null);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save referral settings");
    } finally {
      setSavingReferrals(false);
    }
  }, []);

  const toggleModule = useCallback(
    async (key: string, enabled: boolean) => {
      setSaving(true);
      setSuccess(false);
      try {
        const res = await settingsApi.update({ modules: { [key]: enabled } });
        setData(res);
        setSuccess(true);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update");
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const updateSetting = useCallback(
    async (updates: Record<string, unknown>) => {
      setSaving(true);
      setSuccess(false);
      try {
        const res = await settingsApi.update(updates);
        setData(res);
        setSuccess(true);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update");
      } finally {
        setSaving(false);
      }
    },
    [],
  );

  const toggleProtocol = useCallback(
    (protocol: string) => {
      if (!data) return;
      const current = data.settings.default_protocols;
      const next = current.includes(protocol)
        ? current.filter((p) => p !== protocol)
        : [...current, protocol];
      updateSetting({ default_protocols: next });
    },
    [data, updateSetting],
  );

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        {error ? (
          <div className="rounded border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        ) : (
          <p className="text-gray-500">Loading settings...</p>
        )}
      </div>
    );
  }

  // Group modules by tier for display
  const tierGroups: Record<string, ModuleInfo[]> = {};
  for (const mod of data.modules) {
    const tier = mod.min_tier;
    if (!tierGroups[tier]) tierGroups[tier] = [];
    tierGroups[tier].push(mod);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-bold">Pipeline Settings</h1>
      <p className="mt-1 text-gray-600">
        Configure which pipeline modules run and how the pipeline behaves.
      </p>

      {error && (
        <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="mt-4 rounded border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          Settings saved.
        </div>
      )}

      {/* Flow mode */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold">Flow mode</h2>
        <div className="mt-3 space-y-2">
          {FLOW_MODES.map((fm) => (
            <label
              key={fm.value}
              className="flex cursor-pointer items-start gap-3 rounded border p-3 hover:bg-gray-50"
            >
              <input
                type="radio"
                name="flowMode"
                value={fm.value}
                checked={data.settings.flow_mode === fm.value}
                onChange={() => updateSetting({ flow_mode: fm.value })}
                disabled={saving}
                className="mt-0.5"
              />
              <div>
                <div className="font-medium">{fm.label}</div>
                <div className="text-sm text-gray-500">{fm.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </section>

      {/* Protocols */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold">Default protocols</h2>
        <div className="mt-3 space-y-2">
          {PROTOCOL_OPTIONS.map((p) => (
            <label key={p.value} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={data.settings.default_protocols.includes(p.value)}
                onChange={() => toggleProtocol(p.value)}
                disabled={saving}
              />
              {p.label}
            </label>
          ))}
        </div>
      </section>

      {/* Sandbox backend */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold">Sandbox backend</h2>
        <select
          className="mt-2 rounded border px-3 py-2"
          value={data.settings.sandbox_backend}
          onChange={(e) => updateSetting({ sandbox_backend: e.target.value })}
          disabled={saving}
        >
          {SANDBOX_BACKENDS.map((sb) => (
            <option key={sb.value} value={sb.value}>
              {sb.label}
            </option>
          ))}
        </select>
      </section>

      {/* Algolia */}
      <section className="mt-8">
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={data.settings.algolia_enabled}
            onChange={(e) => updateSetting({ algolia_enabled: e.target.checked })}
            disabled={saving}
            className="h-4 w-4"
          />
          <span className="font-semibold">Algolia search integration</span>
        </label>
      </section>

      {/* Pipeline modules */}
      <section className="mt-10">
        <h2 className="text-lg font-semibold">Pipeline modules</h2>
        <p className="mt-1 text-sm text-gray-500">
          Toggle individual pipeline phases. Locked modules require a plan
          upgrade.
        </p>

        {["starter", "pro", "business", "enterprise"].map((tier) => {
          const mods = tierGroups[tier];
          if (!mods || mods.length === 0) return null;
          return (
            <div key={tier} className="mt-6">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
                {TIER_LABELS[tier]} tier
              </h3>
              <div className="mt-2 space-y-1">
                {mods.map((mod) => (
                  <label
                    key={mod.key}
                    className={`flex items-center gap-3 rounded px-3 py-2 ${
                      mod.available
                        ? "cursor-pointer hover:bg-gray-50"
                        : "cursor-not-allowed opacity-50"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={mod.enabled}
                      onChange={(e) => toggleModule(mod.key, e.target.checked)}
                      disabled={!mod.available || saving}
                      className="h-4 w-4"
                    />
                    <span>{mod.label}</span>
                    {!mod.available && (
                      <span className="ml-auto text-xs text-gray-400">
                        Requires {TIER_LABELS[mod.min_tier]}
                      </span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </section>

      {/* Referral policy and payouts */}
      <section className="mt-10" id="referrals">
        <h2 className="text-lg font-semibold">Badge and referral income</h2>
        <p className="mt-1 text-sm text-gray-500">
          For Free and the cheapest paid plan, the Powered by VeriDoc badge is mandatory and does not pay commissions.
          For higher paid plans, you can disable the badge here, or keep it enabled and earn recurring referral commissions.
        </p>
        <p className="mt-2 text-sm text-blue-700">
          Upgrade tip: after upgrading to Pro, Business, or Enterprise, open this section to configure badge opt-out and payouts.
        </p>
        <p className="mt-1 text-sm">
          <a className="text-blue-700 underline" href="/referral-terms">
            Read referral terms and recurring payout rules
          </a>
        </p>

        {!referrals ? (
          <p className="mt-3 text-sm text-gray-500">Loading referral settings...</p>
        ) : (
          <div className="mt-4 rounded border bg-white p-4">
            <div className="grid gap-2 text-sm">
              <p><strong>Referral code:</strong> <span className="font-mono">{referrals.profile.referral_code}</span></p>
              <p><strong>Referral link:</strong> <span className="font-mono">{referrals.profile.referral_link}</span></p>
              <p><strong>Policy:</strong> {referrals.policy.policy_message}</p>
              <p><strong>Recurring rule:</strong> {referrals.earnings.recurring_rule}</p>
              <p><strong>Accrued:</strong> ${(referrals.earnings.accrued_cents / 100).toFixed(2)}</p>
              <p><strong>Queued:</strong> ${(referrals.earnings.queued_cents / 100).toFixed(2)}</p>
              <p><strong>Paid:</strong> ${(referrals.earnings.paid_cents / 100).toFixed(2)}</p>
            </div>

            <div className="mt-4 border-t pt-4">
              <label className="flex items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  checked={referrals.profile.badge_opt_out}
                  disabled={!referrals.profile.badge_opt_out_allowed || savingReferrals}
                  onChange={(e) => saveReferralSettings({ badge_opt_out: e.target.checked })}
                />
                <span>
                  Disable Powered by VeriDoc badge (available only on higher paid tiers)
                </span>
              </label>
              {!referrals.profile.badge_opt_out_allowed && (
                <p className="mt-2 text-xs text-amber-700">
                  Badge is mandatory on your current plan. Upgrade to a higher paid plan to choose opt-out.
                </p>
              )}
            </div>

            <div className="mt-4 border-t pt-4">
              <h3 className="text-sm font-semibold">Payout settings</h3>
              <p className="mt-1 text-xs text-gray-500">
                Set payout provider and recipient details for recurring referral payouts.
              </p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <select
                  className="rounded border px-3 py-2 text-sm"
                  value={referrals.profile.payout_provider}
                  disabled={savingReferrals}
                  onChange={(e) => saveReferralSettings({ payout_provider: e.target.value })}
                >
                  <option value="manual">Manual</option>
                  <option value="wise">Wise</option>
                </select>
                <input
                  className="rounded border px-3 py-2 text-sm"
                  placeholder="Wise recipient id"
                  value={payoutRecipientId}
                  onChange={(e) => setPayoutRecipientId(e.target.value)}
                  disabled={savingReferrals}
                />
                <input
                  className="rounded border px-3 py-2 text-sm sm:col-span-2"
                  placeholder="Payout email"
                  value={payoutEmail}
                  onChange={(e) => setPayoutEmail(e.target.value)}
                  disabled={savingReferrals}
                />
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className="rounded bg-blue-600 px-3 py-2 text-sm text-white disabled:opacity-50"
                  disabled={savingReferrals}
                  onClick={() => saveReferralSettings({
                    payout_recipient_id: payoutRecipientId,
                    payout_email: payoutEmail,
                    accept_terms: true,
                  })}
                >
                  Save payout settings
                </button>
                <button
                  className="rounded border px-3 py-2 text-sm disabled:opacity-50"
                  disabled={savingReferrals}
                  onClick={async () => {
                    try {
                      await billingApi.runPayouts();
                    } catch {
                      // no-op for now; errors are shown by API exception to global banner
                    }
                  }}
                >
                  Run payout queue
                </button>
              </div>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
