"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type AutomationSchedule,
  type PhaseResult,
  type RunPipelineResponse,
  automation as automationApi,
  pipeline as pipelineApi,
  settings as settingsApi,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// Status badge
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

export default function DashboardPage() {
  const [lastRun, setLastRun] = useState<RunPipelineResponse | null>(null);
  const [schedules, setSchedules] = useState<AutomationSchedule[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load schedules on mount
  useEffect(() => {
    automationApi.list().then((res) => setSchedules(res.schedules)).catch(() => {});
  }, []);

  const runPipeline = useCallback(async () => {
    setRunning(true);
    setError(null);
    try {
      // Load current settings to use as defaults
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

  // Compute phase stats
  const phases = lastRun?.phases ?? [];
  const okCount = phases.filter((p) => p.status === "ok").length;
  const errCount = phases.filter((p) => p.status === "error").length;
  const totalDuration = phases.reduce((s, p) => s + p.duration_seconds, 0);

  // Health score from consolidated report
  const qualityScore = lastRun?.report
    ? (lastRun.report as Record<string, unknown>).health_summary
      ? ((lastRun.report as Record<string, Record<string, unknown>>).health_summary
          .quality_score as number) ?? null
      : null
    : null;

  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pipeline Dashboard</h1>
        <button
          onClick={runPipeline}
          disabled={running}
          className="rounded bg-blue-600 px-5 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {running ? "Running..." : "Run Pipeline"}
        </button>
      </div>

      {error && (
        <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Summary cards */}
      {lastRun && (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-green-600">{okCount}</div>
            <div className="text-sm text-gray-500">Phases OK</div>
          </div>
          <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-red-600">{errCount}</div>
            <div className="text-sm text-gray-500">Errors</div>
          </div>
          <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
            <div className="text-2xl font-bold">{totalDuration.toFixed(1)}s</div>
            <div className="text-sm text-gray-500">Total time</div>
          </div>
          {qualityScore !== null && (
            <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
              <div className="text-2xl font-bold">{qualityScore}</div>
              <div className="text-sm text-gray-500">Quality score</div>
            </div>
          )}
        </div>
      )}

      {/* Phase details */}
      {lastRun && phases.length > 0 && (
        <section className="mt-8">
          <h2 className="text-lg font-semibold">Phase results</h2>
          <div className="mt-3 overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Phase
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Status
                  </th>
                  <th className="px-4 py-2 text-right font-medium text-gray-600">
                    Duration
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {phases.map((phase, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-mono text-xs">
                      {phase.name}
                    </td>
                    <td className="px-4 py-2">
                      <StatusBadge status={phase.status} />
                    </td>
                    <td className="px-4 py-2 text-right text-gray-500">
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
        <section className="mt-6">
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
        <section className="mt-6">
          <h2 className="text-lg font-semibold">Artifacts</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {lastRun.artifacts.map((a, i) => (
              <li key={i} className="font-mono text-gray-600">
                {a}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Automation schedules */}
      <section className="mt-10">
        <h2 className="text-lg font-semibold">Automation schedules</h2>
        {schedules.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">
            No schedules configured. Requires Pro plan or higher.
          </p>
        ) : (
          <div className="mt-3 overflow-hidden rounded-lg border">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Name
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Cron
                  </th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">
                    Status
                  </th>
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
