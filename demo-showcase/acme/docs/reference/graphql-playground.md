---
title: "GraphQL playground"
description: "Interactive GraphQL playground for Acme API with schema explorer, live query editor, subscription support, and advanced RAG retrieval pipeline."
content_type: reference
product: both
tags:
  - Reference
  - API
last_reviewed: "2026-03-20"
---

# GraphQL playground

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-6366f1?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-6366f1?style=flat-square)

</div>

The Acme GraphQL API provides a single endpoint for flexible queries across projects, tasks, and users. This page documents the full schema, provides a live query editor, covers authentication, error handling, performance limits, and the advanced RAG retrieval pipeline that powers AI-driven search across GraphQL documentation.

## Endpoint and authentication

| Setting | Value |
| --- | --- |
| Endpoint | [`https://api.acme.example/graphql`](https://api.acme.example/graphql) |
| Method | POST |
| Authentication | Bearer token in `Authorization` header |
| Content type | `application/json` |
| Max query depth | 10 levels |
| Max query complexity | 500 points |
| Rate limit | 60 requests per minute |
| Introspection | Enabled in development, disabled in production |

## Schema overview

The Acme GraphQL schema exposes three operation types and one core object type:

### Query type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `health` | -- | `Health!` | Returns API health status, version, and uptime |
| `project` | `id: ID!` | `Project` | Fetch a single project by ID |
| `projects` | `status: String`, `limit: Int` | `[Project!]!` | List projects with optional status filter |

### Mutation type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `createProject` | `name: String!`, `status: String` | `Project!` | Create a new project resource |
| `updateProject` | `id: ID!`, `name: String`, `status: String` | `Project!` | Update an existing project |

### Subscription type

| Field | Arguments | Return type | Description |
| --- | --- | --- | --- |
| `projectUpdated` | `projectId: ID` | `Project!` | Real-time stream of project changes |

### Project type

| Field | Type | Description |
| --- | --- | --- |
| `id` | `ID!` | Unique project identifier (format: `prj_*`) |
| `name` | `String!` | Project name (3-100 characters) |
| `status` | `String!` | Current status: `draft`, `active`, `archived` |
| `createdAt` | `DateTime` | ISO 8601 creation timestamp |
| `updatedAt` | `DateTime` | ISO 8601 last update timestamp |

## Quick start: query a project

```graphql
query GetProject {
  project(id: "prj_abc123") {
    id
    name
    status
    createdAt
    updatedAt
  }
}
```

Send this query with curl:

```bash
curl -X POST https://api.acme.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetProject { project(id: \"prj_abc123\") { id name status } }"
  }'
```

<!-- requires: api-key -->

**Example response:**

```json
{
  "data": {
    "project": {
      "id": "prj_abc123",
      "name": "Website Redesign",
      "status": "active"
    }
  }
}
```

## Query examples

### Check API health

```graphql
query Health {
  health {
    status
    version
    uptime_seconds
  }
}
```

### List active projects

```graphql
query ActiveProjects {
  projects(status: "active", limit: 10) {
    id
    name
    status
    createdAt
  }
}
```

### Create a project (mutation)

```graphql
mutation CreateProject {
  createProject(name: "Mobile App Launch", status: "active") {
    id
    name
    status
    createdAt
  }
}
```

### Subscribe to project updates

```graphql
subscription WatchProject {
  projectUpdated(projectId: "prj_abc123") {
    id
    name
    status
    updatedAt
  }
}
```

Subscriptions require a WebSocket connection to `wss://api.acme.example/graphql/ws`.

## Live query editor

Enter a GraphQL query and click **Run query** to execute it against the Postman mock sandbox.

!!! info "Sandbox mode"
    Queries route to the Postman mock server at
    [`https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/graphql`](https://662b99a9-ac2a-4096-8a8e-480a73cef3e3.mock.pstmn.io/graphql).
    No API key is required for sandbox requests.

<div style="border:1px solid #dbe2ea;border-radius:10px;padding:16px;background:#f8f9fa">
<label><strong>GraphQL query:</strong></label>
<textarea id="gql-q" rows="10" style="width:100%;font-family:monospace;padding:12px;border:1px solid #ccc;border-radius:8px;font-size:14px;margin:4px 0 8px;">query Health {
  health {
    status
    version
    uptime_seconds
  }
}</textarea>
<button id="gql-run" style="margin:8px 0;padding:8px 24px;background:#1a73e8;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:14px">Run query</button>
<pre id="gql-out" style="max-height:320px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:10px;background:#fff;margin-top:8px;"></pre>
</div>

<script>
/* Sandbox onclick is set by acme-sandbox.js with local mock responses */
</script>

## Advanced RAG retrieval pipeline

The pipeline uses six advanced retrieval features to power AI-driven search across GraphQL and all five protocol documentation sets. These features are enabled by default in `config/ask-ai.yml`.

### Token-aware chunking

The pipeline splits long documentation modules into overlapping chunks of 750 tokens each (100-token overlap) using the `cl100k_base` tokenizer. This matches the `text-embedding-3-small` embedding model tokenization. Short modules that fit within the token limit remain as single chunks.

| Parameter | Default | Description |
| --- | --- | --- |
| `chunking.max_tokens` | 750 | Maximum tokens per chunk |
| `chunking.overlap_tokens` | 100 | Overlap between consecutive chunks |
| Tokenizer | `cl100k_base` | Matches OpenAI embedding models |

### Hybrid search with Reciprocal Rank Fusion

The retrieval pipeline combines two search strategies using Reciprocal Rank Fusion (RRF, k=60):

1. **Semantic search** queries the FAISS vector index with cosine similarity over `text-embedding-3-small` embeddings
1. **Token-overlap search** scores modules by keyword overlap between query and document text

RRF merges both rankings into a single fused list. This improves recall for queries that combine specific terminology (matched by tokens) with conceptual intent (matched by embeddings).

### HyDE query expansion

When HyDE is enabled, the pipeline generates a hypothetical documentation passage using `gpt-4.1-mini` (temperature 0.0, max 300 tokens) before embedding the query. The generated passage captures domain-specific vocabulary that the raw user question may lack. The pipeline embeds this hypothetical document instead of the raw query, which improves retrieval for vague or high-level questions.

### Cross-encoder reranking

After initial retrieval returns 20 candidates, a cross-encoder model (`cross-encoder/ms-marco-MiniLM-L-6-v2`) reranks them by scoring (query, document) pairs. The reranker uses the concatenation of each candidate's title, summary, and assistant excerpt. This reduces false positives and surfaces the most relevant modules for the final top-N context window.

### Embedding cache

An in-memory LRU cache stores embedding vectors with a 3,600-second TTL and a maximum of 512 entries. Repeated queries skip the OpenAI embedding API call entirely, reducing latency and API costs. The cache evicts the oldest entry when full.

### Multi-mode retrieval evaluation

The `run_retrieval_evals.py` script supports four search modes for comparison:

| Mode | Strategy | Use case |
| --- | --- | --- |
| `token` | Token-overlap scoring | Baseline, no API key required |
| `semantic` | FAISS cosine similarity | Embedding-based retrieval |
| `hybrid` | RRF fusion of token + semantic | Best recall for mixed queries |
| `hybrid+rerank` | Hybrid + cross-encoder reranking | Highest precision for production |

Run a full comparison:

```bash
python3 scripts/run_retrieval_evals.py \
  --mode all \
  --use-embeddings \
  --dataset config/retrieval_eval_dataset.yml \
  --report reports/retrieval_comparison.json
```

<!-- requires: OPENAI_API_KEY, faiss-cpu, sentence-transformers -->

## Error handling

GraphQL errors appear in the `errors` array alongside partial `data`:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Project not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["project"],
      "extensions": {
        "code": "NOT_FOUND",
        "timestamp": "2026-03-20T14:30:00Z"
      }
    }
  ]
}
```

### Error codes

| Code | HTTP equivalent | Meaning | Resolution |
| --- | --- | --- | --- |
| `UNAUTHENTICATED` | 401 | Missing or invalid bearer token | Provide a valid `Authorization: Bearer` header |
| `FORBIDDEN` | 403 | Token valid but lacks required scope | Request the `graphql:read` or `graphql:write` scope |
| `NOT_FOUND` | 404 | Requested resource does not exist | Verify the resource ID |
| `QUERY_TOO_COMPLEX` | 400 | Query exceeds 500 complexity points | Reduce nesting depth or remove unnecessary fields |
| `QUERY_TOO_DEEP` | 400 | Query exceeds 10 levels of nesting | Flatten the query or use separate requests |
| `RATE_LIMITED` | 429 | Exceeded 60 requests per minute | Implement request throttling on the client |
| `INTERNAL_ERROR` | 500 | Server error | Retry with exponential backoff (max 3 attempts) |

## Performance limits

| Limit | Value | Notes |
| --- | --- | --- |
| Max query depth | 10 levels | Nested field resolution depth |
| Max complexity | 500 points | Each field costs 1 point, lists cost 10 points |
| Max query size | 10 KB | Request body size limit |
| Timeout | 30 seconds | Per-query execution timeout |
| Batch queries | Up to 5 | Multiple queries in one request |

## Next steps

- [REST API reference](rest-api.md) for standard CRUD operations
- [gRPC gateway invoke](grpc-gateway.md) for high-performance Remote Procedure Calls
- [AsyncAPI event docs](asyncapi-events.md) for event-driven channels
- [WebSocket event playground](websocket-events.md) for bidirectional real-time messaging
- [Tutorial: launch your first integration](../guides/tutorial.md) to use GraphQL in practice
