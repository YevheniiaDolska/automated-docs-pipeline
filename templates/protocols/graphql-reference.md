---
title: "GraphQL API reference"
description: "Stripe-quality GraphQL reference template with query, mutation, and subscription patterns, error handling, and performance guidance."
content_type: reference
product: both
tags:
  - API
  - GraphQL
  - Reference
---

# GraphQL API reference

Use this template to document a GraphQL schema with production-grade examples.
Start with one query, one mutation, and one subscription that match real user jobs.

## Endpoint and auth

```text
Endpoint: https://{{ api_url }}/graphql
Auth: Authorization: Bearer {{ api_token_example }}
```

## Quick start query

```graphql
query ViewerProfile {
  viewer {
    id
    email
    organization {
      id
      name
    }
  }
}
```

```json
{
  "data": {
    "viewer": {
      "id": "usr_01HXYZ",
      "email": "owner@example.com",
      "organization": {
        "id": "org_01A9",
        "name": "Acme Platform"
      }
    }
  }
}
```

## Operations catalog

### Queries

- `viewer`
- `project(id: ID!)`
- `projects(limit: Int, after: String)`

### Mutations

- `createProject(input: CreateProjectInput!)`
- `updateProject(id: ID!, input: UpdateProjectInput!)`
- `archiveProject(id: ID!)`

### Subscriptions

- `projectUpdated(projectId: ID!)`
- `deploymentStatusChanged(projectId: ID!)`

## Mutation example

```graphql
mutation CreateProject {
  createProject(input: {
    name: "Payments API"
    environment: PRODUCTION
    labels: ["critical", "customer-facing"]
  }) {
    project {
      id
      name
      status
      createdAt
    }
    warnings {
      code
      message
    }
  }
}
```

## Subscription example

```graphql
subscription ProjectEvents {
  deploymentStatusChanged(projectId: "prj_123") {
    deploymentId
    state
    changedAt
    actor {
      id
      email
    }
  }
}
```

## Errors and reliability

| Error | Meaning | Action |
| --- | --- | --- |
| `UNAUTHENTICATED` | Missing/invalid token | Refresh token and retry |
| `FORBIDDEN` | No permission for field/resource | Request proper role scope |
| `BAD_USER_INPUT` | Invalid input shape or enum | Validate payload before sending |
| `RATE_LIMITED` | Request quota exceeded | Backoff with jitter and retry |

## Performance guidance

- Prefer persisted queries for high-traffic routes.
- Set per-request complexity limits and max depth.
- Use cursor pagination for lists over 100 items.
- Track p95 latency per operation name.

## Testing matrix

- Happy path for each high-value operation.
- Auth failures and permission boundaries.
- Schema regression checks on each deploy.
- Subscription reconnect and missed-event behavior.

## Next steps

- [Documentation index](../index.md)
