---
title: 'Intent experience: integrate for beginner'
description: Assembled guidance for one intent and audience using reusable knowledge
  modules with verified metadata and channel-ready sections.
content_type: reference
product: both
tags:
- Reference
- AI
app_version: '7.68'
last_reviewed: '2026-03-26'
original_author: Kroha
---


<!-- VERIDOC_POWERED_BADGE:START -->
[![Powered by VeriDoc](https://img.shields.io/badge/Powered%20by-VeriDoc-0ea5e9?style=flat-square)](https://veridoc.app)
<!-- VERIDOC_POWERED_BADGE:END -->

# Intent experience: integrate for beginner

This page is assembled for the `integrate` intent and the `beginner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent integrate --audience beginner --channel docs
```

## Included modules

### Tutorial: launch your first VeriOps API integration

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

# Tutorial: launch your first VeriOps API integration

<div class="veriops-badges" markdown>

![Powered by VeriOps](https://img.shields.io/badge/Powered%20by-VeriOps-7c3aed?style=flat-square)
![Quality Score](https://img.shields.io/badge/Quality%20Score-100%25-10b981?style=flat-square)
![Protocols](https://img.shields.io/badge/Protocols-5-7c3aed?style=flat-square)

</div>

This tutorial walks you through creating your first VeriOps API project, sending authenticated requests across three protocols (REST, GraphQL, and WebSocket), and verifying the integration works. You complete all five steps in under 15 minutes.

## What you will build

By the end of this tutorial, you will have:

- A working REST API client that creates and retrieves projects
- A GraphQL query that fetches project data with custom field selection
- A WebSocket subscription that receives real-time project update events
- A test script that verifies all three protocols work together

**Time to first success:** 5 minutes for REST, 15 minutes for the complete multi-protocol integration.

### Tutorial: launch your first VeriOps API integration (Part 2)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Before you start

You need:

- An VeriOps API key from the [developer dashboard](https://app.veriops.example/settings/api)
- `curl` version 7.68 or later (run `curl --version` to verify)
- Node.js version 18 or later for the WebSocket client (run `node --version` to verify)
- A terminal with internet access
- About 15 minutes

!!! tip "Save time"
    Export your API key as an environment variable to avoid repeating it in every command:
    `export VERIOPS_API_KEY="YOUR_API_KEY"`

### Tutorial: launch your first VeriOps API integration (Part 3)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 1: verify your API key (2 minutes)

Run this command to confirm your API key authenticates against the VeriOps REST API:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.veriops.example/v1/projects
```

<!-- requires: api-key -->

A `200` response confirms your key works. A `401` response means the key is invalid or expired. Generate a new key in the [dashboard](https://app.veriops.example/settings/api) if you receive `401`.

Next, verify the GraphQL endpoint:

```bash
curl -s -X POST https://api.veriops.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ health { status version } }"}' \
  | python3 -m json.tool
```

<!-- requires: api-key -->

**Expected response:**

```json
{
    "data": {
        "health": {
            "status": "ok",
            "version": "1.0.0"
        }
    }
}
```

### Tutorial: launch your first VeriOps API integration (Part 4)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 2: create a project via REST (3 minutes)

Create your first project resource using the REST API:

```bash
curl -X POST https://api.veriops.example/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tutorial Integration Project",
    "description": "Created during the VeriOps API tutorial",
    "status": "active"
  }'
```

<!-- requires: api-key -->

**Expected response (HTTP 201):**

```json
{
  "id": "prj_abc123",
  "name": "Tutorial Integration Project",
  "description": "Created during the VeriOps API tutorial",
  "status": "active",
  "created_at": "2026-03-19T10:00:00Z",
  "updated_at": "2026-03-19T10:00:00Z",
  "task_count": 0,
  "owner_id": "usr_789"
}
```

Save the `id` value (for example, `prj_abc123`). You need it for steps 3 and 4.

### Tutorial: launch your first VeriOps API integration (Part 5)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 3: query the project via GraphQL (3 minutes)

Use GraphQL to fetch the project you created with custom field selection. GraphQL returns only the fields you request, which reduces payload size.

```bash
curl -s -X POST https://api.veriops.example/graphql \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetProject($id: ID!) { project(id: $id) { id name status createdAt } }",
    "variables": {"id": "prj_abc123"}
  }' \
  | python3 -m json.tool
```

<!-- requires: api-key -->

**Expected response:**

```json
{
    "data": {
        "project": {
            "id": "prj_abc123",
            "name": "Tutorial Integration Project",
            "status": "active",
            "createdAt": "2026-03-19T10:00:00Z"
        }
    }
}
```

Notice that the response contains only the four fields you requested (`id`, `name`, `status`, `createdAt`), not the full project object. This is a key advantage of GraphQL over REST for bandwidth-sensitive clients.

### Tutorial: launch your first VeriOps API integration (Part 6)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 4: subscribe to real-time updates via WebSocket (5 minutes)

Open a WebSocket connection to receive live project change events. Create this Node.js script:

```javascript
// tutorial-websocket.js
// Connect to VeriOps WebSocket API and subscribe to project updates
// Requires: Node.js 18+ (built-in WebSocket support)
const ws = new WebSocket(
  'wss://api.veriops.example/realtime?token=YOUR_API_KEY'
);

ws.addEventListener('open', () => {
  console.log('Connected to VeriOps WebSocket API');

// Subscribe to updates for the project you created in Step 2
  ws.send(JSON.stringify({
    type: 'subscribe',
    request_id: 'tutorial-001',
    sent_at: new Date().toISOString(),
    payload: {
      channel: 'project.updated',
      filters: { project_id: 'prj_abc123' }
    }
  }));
});

ws.addEventListener('message', (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'ack') {
    console.log('Subscription confirmed:', msg.request_id);
  } else if (msg.type === 'event') {
    console.log('Project update received:');
    console.log('  Status:', msg.payload.data.status);
    console.log('  Updated by:', msg.payload.data.updated_by);
  } else if (msg.type === 'ping') {
    ws.send(JSON.stringify({ type: 'pong', request_id: msg.request_id }));
  }
});

ws.addEventListener('close', (event) => {
  console.log('Disconnected:', event.code, event.reason);
});

```

### Tutorial: launch your first VeriOps API integration (Part 7)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

```javascript
// Keep the script running for 60 seconds to receive events
setTimeout(() => {
  ws.close(1000, 'Tutorial complete');
  console.log('Tutorial WebSocket client closed');
}, 60000);
```

<!-- requires: api-key -->

Run the script:

```bash
node tutorial-websocket.js
```

While the script runs, update the project status from another terminal to trigger an event:

```bash
curl -X PUT https://api.veriops.example/v1/projects/prj_abc123 \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "archived"}'
```

<!-- requires: api-key -->

The WebSocket client prints the update event within 1-2 seconds.

### Tutorial: launch your first VeriOps API integration (Part 8)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Step 5: verify the integration (2 minutes)

Run this checklist to confirm all three protocols work:

| Protocol | Test command | Expected result |
| --- | --- | --- |
| REST | `GET /v1/projects` | HTTP 200 with project list |
| GraphQL | `query { health { status } }` | `{"data": {"health": {"status": "ok"}}}` |
| WebSocket | Connect to `wss://api.veriops.example/realtime` | Connection opens, subscription confirmed |

If any step fails:

- **HTTP 401 on REST or GraphQL**: Your API key is invalid. Generate a new one in the [dashboard](https://app.veriops.example/settings/api).
- **WebSocket connection error**: Verify you use `wss://` (not `ws://`) and the key is passed as `?token=` query parameter.
- **Timeout on any request**: Check your network allows outbound connections on port 443.

## What you accomplished

| Step | Protocol | Outcome |
| --- | --- | --- |
| Verify API key | REST + GraphQL | Confirmed authentication across two protocols |
| Create project | REST | Created a project resource via `POST /v1/projects` |
| Query project | GraphQL | Fetched project with custom field selection |
| Subscribe to events | WebSocket | Received real-time project update events |
| Verify integration | All three | Confirmed multi-protocol integration works end-to-end |

### Tutorial: launch your first VeriOps API integration (Part 9)

Build a working VeriOps API integration in 15 minutes with authenticated requests, project creation, and real-time WebSocket subscriptions.

## Next steps

- [REST API reference](../reference/rest-api.md) for all 14 endpoints across five resources
- [GraphQL playground](../reference/graphql-playground.md) to explore the full schema interactively
- [gRPC gateway invoke](../reference/grpc-gateway.md) for high-performance RPC calls
- [How-to: keep docs aligned with every release](how-to.md) for the operator workflow
- [Troubleshooting: common pipeline issues](troubleshooting.md) if you encounter errors

## Knowledge module pipeline steps

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
