---
title: "gRPC Gateway Invoke"
description: "Invoke gRPC services through HTTP gateway from docs."
content_type: reference
product: both
tags:
  - API
  - gRPC
---

# gRPC Gateway Invoke

> **Powered by VeriDoc**

Use an HTTP gateway endpoint to trigger gRPC service methods.

- Gateway endpoint: `https://api.acme.example/grpc/invoke`
- Payload shape: `{ service, method, payload }`

```json
{
  "service": "ProjectService",
  "method": "GetProject",
  "payload": {"project_id": "prj_123"}
}
```

## Next steps

- [Documentation index](../index.md)
