---
title: "Intent experience: troubleshoot for beginner"
description: "Assembled guidance for one intent and audience using reusable knowledge modules with verified metadata and channel-ready sections."
content_type: reference
product: both
tags:
  - Reference
  - AI
---

# Intent experience: troubleshoot for beginner

This page is assembled for the `troubleshoot` intent and the `beginner` audience using reusable modules.

```bash
python3 scripts/assemble_intent_experience.py \
  --intent troubleshoot --audience beginner --channel docs
```

## Included modules

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

## Next steps (2)

- Validate modules: `npm run lint:knowledge`
- Rebuild retrieval index: `npm run build:knowledge-index`
- Generate assistant pack: `npm run build:intent -- --channel assistant`
