"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { onboarding as onboardingApi } from "@/lib/api";
import AuthGuard from "@/components/auth-guard";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OnboardingAnswers {
  // Steps 1-5
  projectName: string;
  projectType: string;
  docNeed: string;
  repoUrl: string;
  teamSize: string;
  // Step 6
  apiProtocols: string[];
  // Step 7
  llmProvider: string;
  llmApiKey: string;
  // Step 8
  siteGenerator: string;
  enableAlgolia: boolean;
  algoliaAppId: string;
  algoliaSearchKey: string;
  algoliaIndexName: string;
}

const INITIAL_ANSWERS: OnboardingAnswers = {
  projectName: "",
  projectType: "web_app",
  docNeed: "standard",
  repoUrl: "",
  teamSize: "solo",
  apiProtocols: [],
  llmProvider: "groq",
  llmApiKey: "",
  siteGenerator: "mkdocs",
  enableAlgolia: false,
  algoliaAppId: "",
  algoliaSearchKey: "",
  algoliaIndexName: "",
};

const TOTAL_STEPS = 8;

const PROJECT_TYPES = [
  { value: "web_app", label: "Web Application" },
  { value: "api_service", label: "API Service" },
  { value: "library", label: "Library / SDK" },
  { value: "cli_tool", label: "CLI Tool" },
  { value: "mobile_app", label: "Mobile App" },
  { value: "other", label: "Other" },
];

const DOC_NEEDS = [
  { value: "none", label: "None", desc: "I only need Git features" },
  { value: "basic", label: "Basic", desc: "README and guides" },
  { value: "standard", label: "Standard", desc: "Full docs site" },
  { value: "full", label: "Full", desc: "Docs + API reference + i18n" },
];

const TEAM_SIZES = [
  { value: "solo", label: "Just me" },
  { value: "small", label: "2-5 people" },
  { value: "medium", label: "6-20 people" },
  { value: "large", label: "21-100 people" },
  { value: "enterprise", label: "100+ people" },
];

const API_PROTOCOLS = [
  { value: "rest", label: "REST (OpenAPI)" },
  { value: "graphql", label: "GraphQL" },
  { value: "grpc", label: "gRPC (Protobuf)" },
  { value: "asyncapi", label: "AsyncAPI (event-driven)" },
  { value: "websocket", label: "WebSocket" },
];

const LLM_PROVIDERS = [
  { value: "groq", label: "Groq", desc: "Recommended -- fast, cost-effective" },
  { value: "deepseek", label: "DeepSeek", desc: "Budget-friendly" },
  { value: "openai", label: "OpenAI", desc: "GPT-4o" },
];

const SITE_GENERATORS = [
  { value: "mkdocs", label: "MkDocs Material" },
  { value: "docusaurus", label: "Docusaurus" },
  { value: "hugo", label: "Hugo" },
  { value: "vitepress", label: "VitePress" },
  { value: "custom", label: "Custom" },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

function OnboardingWizard() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState<OnboardingAnswers>(INITIAL_ANSWERS);
  const [submitting, setSubmitting] = useState(false);

  const update = useCallback(
    <K extends keyof OnboardingAnswers>(key: K, value: OnboardingAnswers[K]) => {
      setAnswers((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const toggleProtocol = useCallback((protocol: string) => {
    setAnswers((prev) => {
      const has = prev.apiProtocols.includes(protocol);
      return {
        ...prev,
        apiProtocols: has
          ? prev.apiProtocols.filter((p) => p !== protocol)
          : [...prev.apiProtocols, protocol],
      };
    });
  }, []);

  const canProceed = (): boolean => {
    switch (step) {
      case 1:
        return answers.projectName.trim().length > 0;
      default:
        return true;
    }
  };

  const next = () => {
    if (step < TOTAL_STEPS) {
      // Skip step 6 (protocols) if doc_need is none
      const nextStep = step + 1;
      if (nextStep === 6 && answers.docNeed === "none") {
        setStep(7);
      } else {
        setStep(nextStep);
      }
    }
  };

  const prev = () => {
    if (step > 1) {
      const prevStep = step - 1;
      if (prevStep === 6 && answers.docNeed === "none") {
        setStep(5);
      } else {
        setStep(prevStep);
      }
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await onboardingApi.submit(answers as unknown as Record<string, unknown>);
      router.push("/dashboard");
    } catch {
      // errors surfaced by API client
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <div className="mb-8">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Step {step} of {TOTAL_STEPS}
          </span>
          <span>{Math.round((step / TOTAL_STEPS) * 100)}%</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-gray-200">
          <div
            className="h-2 rounded-full bg-blue-600 transition-all"
            style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
          />
        </div>
      </div>

      <div className="rounded-lg border bg-white p-6 shadow-sm">
        {/* Step 1: Project name */}
        {step === 1 && (
          <div>
            <h2 className="text-xl font-semibold">Project name</h2>
            <p className="mt-1 text-gray-600">What is the name of your project?</p>
            <input
              type="text"
              className="mt-4 w-full rounded border px-3 py-2"
              value={answers.projectName}
              onChange={(e) => update("projectName", e.target.value)}
              placeholder="My Awesome Project"
              autoFocus
            />
          </div>
        )}

        {/* Step 2: Project type */}
        {step === 2 && (
          <div>
            <h2 className="text-xl font-semibold">Project type</h2>
            <p className="mt-1 text-gray-600">
              What type of project are you documenting?
            </p>
            <div className="mt-4 space-y-2">
              {PROJECT_TYPES.map((t) => (
                <label key={t.value} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="projectType"
                    value={t.value}
                    checked={answers.projectType === t.value}
                    onChange={() => update("projectType", t.value)}
                  />
                  {t.label}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Documentation need */}
        {step === 3 && (
          <div>
            <h2 className="text-xl font-semibold">Documentation scope</h2>
            <p className="mt-1 text-gray-600">
              How comprehensive should the documentation be?
            </p>
            <div className="mt-4 space-y-3">
              {DOC_NEEDS.map((d) => (
                <label
                  key={d.value}
                  className="flex cursor-pointer items-start gap-3 rounded border p-3 hover:bg-gray-50"
                >
                  <input
                    type="radio"
                    name="docNeed"
                    value={d.value}
                    checked={answers.docNeed === d.value}
                    onChange={() => update("docNeed", d.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <div className="font-medium">{d.label}</div>
                    <div className="text-sm text-gray-500">{d.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 4: Repository URL */}
        {step === 4 && (
          <div>
            <h2 className="text-xl font-semibold">Repository URL</h2>
            <p className="mt-1 text-gray-600">
              Paste your Git repository URL (optional)
            </p>
            <input
              type="url"
              className="mt-4 w-full rounded border px-3 py-2"
              value={answers.repoUrl}
              onChange={(e) => update("repoUrl", e.target.value)}
              placeholder="https://github.com/your-org/your-repo"
            />
          </div>
        )}

        {/* Step 5: Team size */}
        {step === 5 && (
          <div>
            <h2 className="text-xl font-semibold">Team size</h2>
            <p className="mt-1 text-gray-600">
              How many people will use VeriDoc?
            </p>
            <div className="mt-4 space-y-2">
              {TEAM_SIZES.map((t) => (
                <label key={t.value} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="teamSize"
                    value={t.value}
                    checked={answers.teamSize === t.value}
                    onChange={() => update("teamSize", t.value)}
                  />
                  {t.label}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 6: API Protocols */}
        {step === 6 && (
          <div>
            <h2 className="text-xl font-semibold">API protocols</h2>
            <p className="mt-1 text-gray-600">
              Which API protocols does your project use? Select all that apply.
            </p>
            <div className="mt-4 space-y-2">
              {API_PROTOCOLS.map((p) => (
                <label key={p.value} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={answers.apiProtocols.includes(p.value)}
                    onChange={() => toggleProtocol(p.value)}
                  />
                  {p.label}
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Step 7: LLM Provider + API key */}
        {step === 7 && (
          <div>
            <h2 className="text-xl font-semibold">AI provider</h2>
            <p className="mt-1 text-gray-600">
              Choose your preferred LLM provider for AI-powered features.
            </p>
            <div className="mt-4 space-y-3">
              {LLM_PROVIDERS.map((p) => (
                <label
                  key={p.value}
                  className="flex cursor-pointer items-start gap-3 rounded border p-3 hover:bg-gray-50"
                >
                  <input
                    type="radio"
                    name="llmProvider"
                    value={p.value}
                    checked={answers.llmProvider === p.value}
                    onChange={() => update("llmProvider", p.value)}
                    className="mt-0.5"
                  />
                  <div>
                    <div className="font-medium">{p.label}</div>
                    <div className="text-sm text-gray-500">{p.desc}</div>
                  </div>
                </label>
              ))}
            </div>
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700">
                API key (optional -- you can set this later)
              </label>
              <input
                type="password"
                className="mt-1 w-full rounded border px-3 py-2"
                value={answers.llmApiKey}
                onChange={(e) => update("llmApiKey", e.target.value)}
                placeholder={`Enter your ${answers.llmProvider} API key`}
              />
            </div>
          </div>
        )}

        {/* Step 8: Integrations */}
        {step === 8 && (
          <div>
            <h2 className="text-xl font-semibold">Integrations</h2>
            <p className="mt-1 text-gray-600">
              Configure your site generator and search integration.
            </p>

            {/* Site generator */}
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">
                Site generator
              </label>
              <select
                className="mt-1 w-full rounded border px-3 py-2"
                value={answers.siteGenerator}
                onChange={(e) => update("siteGenerator", e.target.value)}
              >
                {SITE_GENERATORS.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Algolia toggle */}
            <div className="mt-6">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={answers.enableAlgolia}
                  onChange={(e) => update("enableAlgolia", e.target.checked)}
                  className="h-4 w-4"
                />
                <span className="font-medium">Enable Algolia search</span>
              </label>
            </div>

            {/* Algolia config (conditional) */}
            {answers.enableAlgolia && (
              <div className="mt-4 space-y-3 rounded border bg-gray-50 p-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Algolia App ID
                  </label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded border px-3 py-2"
                    value={answers.algoliaAppId}
                    onChange={(e) => update("algoliaAppId", e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Algolia Search API key
                  </label>
                  <input
                    type="password"
                    className="mt-1 w-full rounded border px-3 py-2"
                    value={answers.algoliaSearchKey}
                    onChange={(e) => update("algoliaSearchKey", e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Algolia Index name
                  </label>
                  <input
                    type="text"
                    className="mt-1 w-full rounded border px-3 py-2"
                    value={answers.algoliaIndexName}
                    onChange={(e) => update("algoliaIndexName", e.target.value)}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Navigation buttons */}
      <div className="mt-6 flex justify-between">
        <button
          onClick={prev}
          disabled={step === 1}
          className="rounded border px-4 py-2 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
        >
          Back
        </button>
        {step < TOTAL_STEPS ? (
          <button
            onClick={next}
            disabled={!canProceed()}
            className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700 disabled:opacity-40"
          >
            Continue
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="rounded bg-green-600 px-6 py-2 text-white hover:bg-green-700 disabled:opacity-40"
          >
            {submitting ? "Setting up..." : "Finish setup"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <AuthGuard>
      <OnboardingWizard />
    </AuthGuard>
  );
}
