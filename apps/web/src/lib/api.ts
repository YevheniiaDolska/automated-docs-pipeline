/**
 * VeriDoc frontend API client.
 *
 * Wraps all backend endpoints used by the web application.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

// ---------------------------------------------------------------------------
// Token management
// ---------------------------------------------------------------------------

let _token: string | null = null;

export function setToken(token: string | null) {
  _token = token;
  if (token) {
    localStorage.setItem("veridoc_token", token);
  } else {
    localStorage.removeItem("veridoc_token");
  }
}

export function getToken(): string | null {
  if (!_token) {
    _token = localStorage.getItem("veridoc_token");
  }
  return _token;
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? err.error ?? "Unknown error");
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? err.error ?? "Unknown error");
  }
  return res.json() as Promise<T>;
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? err.error ?? "Unknown error");
  }
  return res.json() as Promise<T>;
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? err.error ?? "Unknown error");
  }
  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ---------------------------------------------------------------------------
// Request / Response types
// ---------------------------------------------------------------------------

export interface PhaseResult {
  name: string;
  status: "ok" | "error" | "skipped";
  duration_seconds: number;
  error?: string;
}

export interface RunPipelineRequest {
  repo_path: string;
  doc_scope?: string;
  protocols?: string[];
  api_protocols?: string[];
  algolia_enabled?: boolean;
  algolia_config?: Record<string, unknown>;
  sandbox_backend?: string;
  modules?: Record<string, boolean>;
  flow_mode?: string;
}

export interface RunPipelineResponse {
  status: string;
  message: string;
  artifacts: string[];
  report?: Record<string, unknown>;
  phases: PhaseResult[];
  errors: string[];
}

export interface RagTestRequest {
  repo_path: string;
  test_dir?: string;
  description: string;
  category?: string;
  top_k?: number;
}

export interface RagTestResponse {
  status: string;
  generated_test?: Record<string, unknown>;
  index_stats?: Record<string, unknown>;
  error?: string;
}

export interface RagTestIndexRequest {
  repo_path: string;
  test_dir?: string;
}

export interface RagTestIndexResponse {
  status: string;
  stats?: Record<string, unknown>;
  error?: string;
}

export interface AlgoliaWidgetRequest {
  generator: string;
  app_id: string;
  search_key: string;
  index_name: string;
  output_dir?: string;
}

export interface AlgoliaWidgetResponse {
  status: string;
  files_generated: string[];
  error?: string;
}

export interface DocCompilerRequest {
  repo_path: string;
  modalities?: string;
  generate_faq_doc?: boolean;
}

export interface DocCompilerResponse {
  status: string;
  modalities_run: string[];
  report?: Record<string, unknown>;
  error?: string;
}

// --- Settings types ---

export interface ModuleInfo {
  key: string;
  label: string;
  min_tier: string;
  enabled: boolean;
  available: boolean;
}

export interface PipelineSettings {
  modules: Record<string, boolean>;
  flow_mode: string;
  default_protocols: string[];
  algolia_enabled: boolean;
  sandbox_backend: string;
}

export interface SettingsResponse {
  settings: PipelineSettings;
  modules: ModuleInfo[];
}

export interface UpdateSettingsRequest {
  modules?: Record<string, boolean>;
  flow_mode?: string;
  default_protocols?: string[];
  algolia_enabled?: boolean;
  sandbox_backend?: string;
}

// --- Automation types ---

export interface AutomationSchedule {
  id: string;
  name: string;
  cron: string;
  enabled: boolean;
  flow_mode?: string;
  modules?: Record<string, boolean>;
}

export interface AutomationListResponse {
  schedules: AutomationSchedule[];
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const pipeline = {
  /** Run the 3-phase documentation pipeline. */
  run(request: RunPipelineRequest): Promise<RunPipelineResponse> {
    return post("/pipeline/run", request);
  },

  /** Generate a test using RAG from existing test codebase. */
  generateRagTests(request: RagTestRequest): Promise<RagTestResponse> {
    return post("/pipeline/rag-tests", request);
  },

  /** Build a RAG index from existing tests. */
  indexRagTests(request: RagTestIndexRequest): Promise<RagTestIndexResponse> {
    return post("/pipeline/rag-tests/index", request);
  },

  /** Generate Algolia search widget files for a site generator. */
  generateAlgoliaWidget(
    request: AlgoliaWidgetRequest,
  ): Promise<AlgoliaWidgetResponse> {
    return post("/pipeline/algolia-widget", request);
  },

  /** Run doc compiler to produce documentation overview artifacts. */
  compileDocOverview(
    request: DocCompilerRequest,
  ): Promise<DocCompilerResponse> {
    return post("/pipeline/doc-compiler", request);
  },
};

export const settings = {
  /** Get current pipeline settings with module availability. */
  get(): Promise<SettingsResponse> {
    return get("/settings");
  },

  /** Update pipeline settings. */
  update(request: UpdateSettingsRequest): Promise<SettingsResponse> {
    return put("/settings", request);
  },

  /** Get available modules with tier info. */
  getModules(): Promise<ModuleInfo[]> {
    return get("/settings/modules");
  },
};

export const automation = {
  /** List all automation schedules. */
  list(): Promise<AutomationListResponse> {
    return get("/automation/schedules");
  },

  /** Create a new automation schedule. */
  create(schedule: Omit<AutomationSchedule, "id">): Promise<AutomationSchedule> {
    return post("/automation/schedules", schedule);
  },

  /** Update an existing schedule. */
  update(
    id: string,
    updates: Partial<AutomationSchedule>,
  ): Promise<AutomationSchedule> {
    return put(`/automation/schedules/${id}`, updates);
  },

  /** Delete a schedule. */
  remove(id: string): Promise<{ status: string; message: string }> {
    return del(`/automation/schedules/${id}`);
  },

  /** Trigger a schedule manually. */
  trigger(id: string): Promise<{ status: string; message: string }> {
    return post(`/automation/schedules/${id}/trigger`, {});
  },
};

export const pricing = {
  /** Fetch all available pricing plans. */
  getPlans(): Promise<Record<string, unknown>[]> {
    return get("/pricing/plans");
  },
};

export const onboarding = {
  /** Submit onboarding answers and receive recommended config. */
  submit(answers: Record<string, unknown>): Promise<Record<string, unknown>> {
    return post("/onboarding", answers);
  },
};

// --- Auth types ---

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  tier: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  tier: string;
  is_active: boolean;
  created_at: string;
}

export const auth = {
  async register(request: RegisterRequest): Promise<TokenResponse> {
    const result = await post<TokenResponse>("/auth/register", request);
    setToken(result.access_token);
    return result;
  },

  async login(request: LoginRequest): Promise<TokenResponse> {
    const result = await post<TokenResponse>("/auth/login", request);
    setToken(result.access_token);
    return result;
  },

  logout() {
    setToken(null);
  },

  me(): Promise<UserProfile> {
    return get("/auth/me");
  },
};

// --- Billing types ---

export interface UsageResponse {
  tier: string;
  status: string;
  ai_requests_used: number;
  ai_requests_limit: number;
  pages_generated: number;
  pages_limit: number;
  api_calls_used: number;
  api_calls_limit: number;
  current_period_end: string | null;
  trial_ends_at: string | null;
}

export interface CheckoutResponse {
  checkout_url: string;
  badge_settings_url?: string;
  badge_settings_hint?: string;
}

export interface PortalResponse {
  portal_url: string;
}

export interface ReferralSummaryResponse {
  policy: {
    cheapest_paid_tier: string;
    commission_rate: number;
    mandatory_badge: boolean;
    commission_eligible: boolean;
    policy_message: string;
    ui_hint: string;
  };
  profile: {
    referral_code: string;
    referral_link: string;
    badge_opt_out: boolean;
    badge_opt_out_allowed: boolean;
    payout_provider: string;
    payout_recipient_id: string | null;
    payout_email: string | null;
    payout_status: string;
    terms_accepted_at: string | null;
  };
  earnings: {
    currency: string;
    accrued_cents: number;
    queued_cents: number;
    paid_cents: number;
    reversed_cents: number;
    payout_min_cents: number;
    is_recurring: boolean;
    recurring_rule: string;
  };
  recent_ledger: Array<{
    id: string;
    referred_user_id: string;
    subscription_id: string | null;
    status: string;
    event_type: string;
    amount_cents: number;
    commission_rate: number;
    created_at: string | null;
    available_at: string | null;
    paid_out_at: string | null;
  }>;
  payouts: Array<{
    id: string;
    status: string;
    provider: string;
    provider_payout_id: string | null;
    amount_cents: number;
    currency: string;
    error_message: string | null;
    created_at: string | null;
    processed_at: string | null;
  }>;
}

export const billing = {
  getUsage(): Promise<UsageResponse> {
    return get("/billing/usage");
  },

  createCheckout(tier: string, annual = false): Promise<CheckoutResponse> {
    return post("/billing/checkout", { tier, annual, success_url: window.location.origin + "/billing/success" });
  },

  getPortal(): Promise<PortalResponse> {
    return get("/billing/portal");
  },

  getReferrals(): Promise<ReferralSummaryResponse> {
    return get("/billing/referrals");
  },

  updateReferrals(request: {
    badge_opt_out?: boolean;
    payout_provider?: "manual" | "wise";
    payout_recipient_id?: string;
    payout_email?: string;
    accept_terms?: boolean;
  }): Promise<ReferralSummaryResponse> {
    return put("/billing/referrals", request);
  },

  runPayouts(): Promise<{ entries_considered: number; payouts_created: number; payouts_submitted: number }> {
    return post("/billing/referrals/payouts/run", {});
  },

  requestAudit(data: { name: string; email: string; company: string }): Promise<{ status: string }> {
    return post("/contact/audit-request", data);
  },

  requestInvoice(data: {
    company: string;
    billing_email: string;
    tier: string;
    notes: string;
  }): Promise<{ status: string }> {
    return post("/billing/invoice-request", data);
  },
};

// --- Pipeline runs ---

export interface PipelineRunSummary {
  id: string;
  status: string;
  trigger: string;
  flow_mode: string | null;
  duration_seconds: number;
  quality_score: number | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface PipelineRunDetail extends PipelineRunSummary {
  phases: PhaseResult[];
  artifacts: string[];
  errors: string[];
  report: Record<string, unknown> | null;
  started_at: string | null;
}

export const pipelineRuns = {
  list(limit = 20, offset = 0): Promise<{ runs: PipelineRunSummary[] }> {
    return get(`/pipeline/runs?limit=${limit}&offset=${offset}`);
  },

  get(runId: string): Promise<PipelineRunDetail> {
    return get(`/pipeline/runs/${runId}`);
  },

  start(request: {
    repo_path: string;
    flow_mode?: string;
    modules?: Record<string, boolean>;
    protocols?: string[];
  }): Promise<{ run_id: string; status: string; message: string }> {
    return post("/pipeline/run", request);
  },
};
