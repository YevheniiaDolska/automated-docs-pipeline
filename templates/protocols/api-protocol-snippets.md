---
title: "API protocol snippet pack"
description: "Reusable Stripe-style snippets for REST, GraphQL, gRPC, AsyncAPI, and WebSocket docs generation with consistent structure."
content_type: reference
product: both
tags:
  - API
  - Snippets
  - Reference
---

# API protocol snippet pack

Use these snippets in generated docs for consistent, high-signal structure.

## REST request block

````md
### Request

=== "cURL"

    ```bash smoke
    curl -X GET "https://{{ api_host }}/v1/resources/res_1" \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Accept: application/json"
    ```

=== "JavaScript"

    ```javascript smoke
    const response = await fetch('https://{{ api_host }}/v1/resources/res_1', {
      method: 'GET',
      headers: {
        "Authorization": "Bearer ${TOKEN}",
        "Accept": "application/json",
      },
    });
    const payload = await response.json();
    console.log(payload);
    ```

=== "Python"

    ```python smoke
    import requests

    response = requests.request(
        'GET',
        'https://{{ api_host }}/v1/resources/res_1',
        headers={'Authorization': 'Bearer ${TOKEN}', 'Accept': 'application/json'},
        timeout=30,
    )
    response.raise_for_status()
    print(response.json())
    ```

```json
{
  "id": "res_1",
  "name": "Primary resource",
  "status": "active"
}
```
````

## GraphQL quick op block

````md
### Quick operation

```graphql
query GetResource($id: ID!) {
  resource(id: $id) {
    id
    name
    status
  }
}
```

```json
{ "data": { "resource": { "id": "res_1", "name": "Core", "status": "active" } } }
```
````

## gRPC method block

````md
### Method: Service/Action

- Type: unary|server-stream|client-stream|bidi-stream
- Deadline: 2s
- Retry: UNAVAILABLE, DEADLINE_EXCEEDED

```bash
grpcurl -d '{"id":"res_1"}' {{ endpoint }} {{ package }}.Service/Action
```
````

## AsyncAPI event block

````md
### Event: domain.event.v1

- Producer: service-name
- Ordering key: resource_id
- Delivery: at-least-once
- Dedup key: event_id

```json
{ "event_type": "domain.event.v1", "event_id": "evt_1", "data": { "resource_id": "res_1" } }
```
````

## WebSocket message block

````md
### Event: resource.updated

- Direction: server -> client
- Requires subscription: yes

```json
{ "type": "resource.updated", "request_id": "req_1", "payload": { "id": "res_1" } }
```
````

## Next steps

- [Documentation index](../index.md)
