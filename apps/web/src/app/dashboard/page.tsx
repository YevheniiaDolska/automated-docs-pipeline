"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type AutomationSchedule,
  type PhaseResult,
  type RunPipelineResponse,
  type UsageResponse,
  type UserProfile,
  automation as automationApi,
  auth as authApi,
  billing as billingApi,
  pipeline as pipelineApi,
  settings as settingsApi,
} from "@/lib/api";
import AuthGuard from "@/components/auth-guard";
import AppShell from "@/components/app-shell";
import TierBadge from "@/components/tier-badge";
import UsageMeter from "@/components/usage-meter";
import KpiRing from "@/components/kpi-ring";
import StatusDot from "@/components/status-dot";

// ---------------------------------------------------------------------------
// Status badge (kept for phase results table)
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ok: "bg-green-100 text-green-800",
    error: "bg-red-100 text-red-800",
    skipped: "bg-gray-100 text-gray-600",
  };
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
        colors[status] ?? "bg-gray-100 text-gray-600"
      }`}
    >
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Dashboard component
// ---------------------------------------------------------------------------

function DashboardContent() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [lastRun, setLastRun] = useState<RunPipelineResponse | null>(null);
  const [schedules, setSchedules] = useState<AutomationSchedule[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authApi.me().then(setUser).catch(() => {});
    billingApi.getUsage().then(setUsage).catch(() => {});
    automationApi.list().then((res) => setSchedules(res.schedules)).catch(() => {});
  }, []);

  const runPipeline = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      const settingsRes = await settingsApi.get();
      const s = settingsRes.settings;
      const response = await pipelineApi.run({
        repo_path: ".",
        flow_mode: s.flow_mode,
        protocols: s.default_protocols,
        algolia_enabled: s.algolia_enabled,
        sandbox_backend: s.sandbox_backend,
        modules: s.modules,
      });
      setLastRun(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setRunning(false);
    }
  }, []);

  const phases = lastRun?.phases ?? [];
  const okCount = phases.filter((p) => p.status === "ok").length;
  const errCount = phases.filter((p) => p.status === "error").length;
  const totalDuration = phases.reduce((s, p) => s + p.duration_seconds, 0);

  const qualityScore = lastRun?.report
    ? (lastRun.report as Record<string, unknown>).health_summary
      ? ((lastRun.report as Record<string, Record<string, unknown>>).health_summary
          .quality_score as number) ?? null
      : null
    : null;

  const daysUntilRenewal =
    usage?.current_period_end
      ? Math.max(0, Math.ceil((new Date(usage.current_period_end).getTime() - Date.now()) / 86400000))
      : null;

  return (
    <div className="space-y-6">
      {/* Welcome banner */}
      <section className="rounded-xl border bg-surface p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              Welcome back{user ? `, ${user.email}` : ""}
            </h2>
            <div className="mt-1 flex items-center gap-3 text-sm text-muted">
              {usage && <TierBadge tier={usage.tier} />}
              {daysUntilRenewal !== null && (
                <span>{daysUntilRenewal} days until renewal</span>
              )}
            </div>
          </div>
          <button
            onClick={runPipeline}
            disabled={running}
            className="rounded-md bg-brand px-5 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:opacity-50"
          >
            {running ? "Running..." : "Run Pipeline"}
          </button>
        </div>
      </section>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Usage + KPI row */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Usage meters */}
        {usage && (
          <div className="rounded-xl border bg-surface p-6 shadow-sm lg:col-span-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
              Usage overview
            </h3>
            <div className="mt-4 space-y-3">
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
          </div>
        )}

        {/* KPI ring */}
        <div className="rounded-xl border bg-surface p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted">
            Quality score
          </h3>
          <div className="mt-4 flex items-center justify-center">
            <KpiRing
              value={qualityScore ?? 0}
              max={100}
              size={120}
              label={qualityScore !== null ? "Latest run" : "No runs yet"}
            />
          </div>
        </div>
      </div>

      {/* Business chain mini */}
      {usage && (
        <section className="rounded-xl border bg-surface p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-4">
            <StatusDot
              status={usage.status === "active" || usage.status === "trialing" ? "ok" : "error"}
              label="Payment"
            />
            <span className="text-muted">&rarr;</span>
            <StatusDot
              status={usage.tier !== "free" ? "ok" : "idle"}
              label="Plan active"
            />
            <span className="text-muted">&rarr;</span>
            <StatusDot
              status={
                usage.ai_requests_used < usage.ai_requests_limit &&
                usage.pages_generated < usage.pages_limit
                  ? "ok"
                  : "warn"
              }
              label="Limits OK"
            />
            <span className="text-muted">&rarr;</span>
            <StatusDot
              status={usage.status === "active" || usage.status === "trialing" ? "ok" : "error"}
              label="Pipeline"
            />
            <span className="text-muted">&rarr;</span>
            <StatusDot status="ok" label="Reports" />
          </div>
        </section>
      )}

      {/* Summary cards */}
      {lastRun && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border bg-surface p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-ok">{okCount}</div>
            <div className="text-sm text-muted">Phases OK</div>
          </div>
          <div className="rounded-lg border bg-surface p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-red-600">{errCount}</div>
            <div className="text-sm text-muted">Errors</div>
          </div>
          <div className="rounded-lg border bg-surface p-4 text-center shadow-sm">
            <div className="text-2xl font-bold">{totalDuration.toFixed(1)}s</div>
            <div className="text-sm text-muted">Total time</div>
          </div>
          <div className="rounded-lg border bg-surface p-4 text-center shadow-sm">
            <div className="text-2xl font-bold">{phases.length}</div>
            <div className="text-sm text-muted">Total phases</div>
          </div>
        </div>
      )}

      {/* Phase details */}
      {lastRun && phases.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold">Phase results</h2>
          <div className="mt-3 overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-muted">Phase</th>
                  <th className="px-4 py-2 text-left font-medium text-muted">Status</th>
                  <th className="px-4 py-2 text-right font-medium text-muted">Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {phases.map((phase, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs">{phase.name}</td>
                    <td className="px-4 py-2">
                      <StatusBadge status={phase.status} />
                    </td>
                    <td className="px-4 py-2 text-right text-muted">
                      {phase.duration_seconds.toFixed(2)}s
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Errors */}
      {lastRun && lastRun.errors.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-red-700">Errors</h2>
          <ul className="mt-2 space-y-1 text-sm text-red-600">
            {lastRun.errors.map((err, i) => (
              <li key={i} className="rounded bg-red-50 px-3 py-2">
                {err}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Artifacts */}
      {lastRun && lastRun.artifacts.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold">Artifacts</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {lastRun.artifacts.map((a, i) => (
              <li key={i} className="font-mono text-muted">
                {a}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Automation schedules */}
      <section>
        <h2 className="text-lg font-semibold">Automation schedules</h2>
        {schedules.length === 0 ? (
          <p className="mt-2 text-sm text-muted">
            No schedules configured. Requires Pro plan or higher.
          </p>
        ) : (
          <div className="mt-3 overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-muted">Name</th>
                  <th className="px-4 py-2 text-left font-medium text-muted">Cron</th>
                  <th className="px-4 py-2 text-left font-medium text-muted">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {schedules.map((s) => (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">{s.name}</td>
                    <td className="px-4 py-2 font-mono text-xs">{s.cron}</td>
                    <td className="px-4 py-2">
                      <StatusBadge status={s.enabled ? "ok" : "skipped"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <AppShell>
        <div className="mx-auto max-w-5xl px-4 py-8">
          <h1 className="text-2xl font-bold">Pipeline Dashboard</h1>
          <div className="mt-6">
            <DashboardContent />
          </div>
        </div>
      </AppShell>
    </AuthGuard>
  );
}
