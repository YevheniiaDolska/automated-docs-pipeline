/**
 * VeriDoc frontend API client.
 *
 * Wraps all backend endpoints used by the web application.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, err.detail ?? err.error ?? "Unknown error");
  }
  return res.json() as Promise<T>;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
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

export interface RunPipelineRequest {
  repo_path: string;
  doc_scope?: string;
  protocols?: string[];
  api_protocols?: string[];
  algolia_enabled?: boolean;
  algolia_config?: Record<string, unknown>;
  sandbox_backend?: string;
}

export interface RunPipelineResponse {
  status: string;
  message: string;
  artifacts: string[];
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

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------

export const pipeline = {
  /** Run the documentation pipeline with protocol and integration params. */
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
