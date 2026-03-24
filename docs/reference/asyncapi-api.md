---
title: ASYNCAPI API Reference
description: Auto-generated asyncapi reference from source contract.
content_type: reference
product: both
tags:
- Development
- Documents
- Mnt
- Users
- Auto Doc Pipeline
- Docs
- Kroha
- C
last_reviewed: '2026-03-23'
original_author: Kroha
---


# ASYNCAPI Reference

Source: `/tmp/pytest-of-eudo/pytest-2489/test_multi_protocol_flow_e2e_e0/asyncapi.yaml`

Flow mode: `api-first`

## Top-level Keys

- `asyncapi`
- `channels`
- `info`

## Channels

- Channel count: `1`
- `orders/created`

## Interactive AsyncAPI Tester

> Sandbox semantic mode: this tester returns event-aware responses by `event_type` and payload fields.

<div id="asyncapi-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>WebSocket Endpoint:</strong> <code id="asyncapi-ws-view"></code></p>
  <p><strong>HTTP Publish Endpoint:</strong> <code id="asyncapi-http-view"></code></p>
  <textarea id="asyncapi-message" rows="8" style="width:100%; font-family:monospace;">{
  "event_type": "project.updated",
  "event_id": "evt_001",
  "data": {"project_id": "prj_abc123", "status": "active"}
}</textarea><br/>
  <button id="asyncapi-send-ws">Send via WebSocket</button>
  <button id="asyncapi-send-http">Send via HTTP</button>
  <pre id="asyncapi-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const wsEndpoint = "wss://echo.websocket.events"; const httpEndpoint = "https://postman-echo.com/post";
const wsView = document.getElementById('asyncapi-ws-view');
const httpView = document.getElementById('asyncapi-http-view');
const sendWs = document.getElementById('asyncapi-send-ws');
const sendHttp = document.getElementById('asyncapi-send-http');
const msg = document.getElementById('asyncapi-message');
const out = document.getElementById('asyncapi-output');
if (!wsView || !httpView || !sendWs || !sendHttp || !msg || !out) return;
wsView.textContent = wsEndpoint || 'not configured';
httpView.textContent = httpEndpoint || 'not configured';
function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }
function semanticEvent(input){
  const req = parseJson(input);
  const eventType = String(req.event_type || req.type || req.event || '').toLowerCase();
  const data = (req.data && typeof req.data === 'object') ? req.data : {};
  const eventId = req.event_id || ('evt_' + Math.random().toString(36).slice(2, 10));
  const projectId = String(data.project_id || 'prj_abc123');
  const occurredAt = req.occurred_at || new Date().toISOString();
  if (eventType === 'project.created') return { event_id: eventId, event_type: 'project.created', occurred_at: occurredAt, data: { project_id: projectId, name: data.name || 'New Project', status: data.status || 'draft' } };
  if (eventType === 'project.updated') return { event_id: eventId, event_type: 'project.updated', occurred_at: occurredAt, data: { project_id: projectId, status: data.status || 'active', changed_fields: data.changed_fields || ['status'] } };
  if (eventType === 'task.completed') return { event_id: eventId, event_type: 'task.completed', occurred_at: occurredAt, data: { task_id: data.task_id || 'tsk_123', project_id: projectId, completed_by: data.completed_by || 'usr_demo' } };
  return { event_id: eventId, event_type: eventType || 'custom.event', occurred_at: occurredAt, data: Object.assign({ project_id: projectId, status: 'accepted' }, data), hint: 'Use: project.created, project.updated, task.completed' };
}
sendWs.onclick = function(){
  if (!wsEndpoint) { out.textContent = 'WebSocket endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_ws_endpoint)'; return; }
  try {
    const socket = new WebSocket(wsEndpoint);
    let received = false;
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'sent over websocket'; };
    socket.onmessage = function(e){
      received = true;
      const semantic = semanticEvent(e.data);
      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: semantic }, null, 2);
      socket.close();
    };
    socket.onerror = function(){
      const semantic = semanticEvent(msg.value);
      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: semantic }, null, 2);
    };
    setTimeout(function(){
      if (!received) {
        const semantic = semanticEvent(msg.value);
        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: semantic }, null, 2);
        try { socket.close(); } catch (_) {}
      }
    }, 1500);
  } catch (error) { out.textContent = String(error); }
};
sendHttp.onclick = async function(){
  if (!httpEndpoint) { out.textContent = 'HTTP publish endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_http_publish_endpoint)'; return; }
  out.textContent = 'Loading...';
  try {
    const body = JSON.parse(msg.value || '{}');
    const response = await fetch(httpEndpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    const semantic = semanticEvent(body);
    out.textContent = JSON.stringify({ mode: 'http-plus-semantic', raw: text, simulated_response: semantic }, null, 2);
  } catch (error) {
    const semantic = semanticEvent(msg.value);
    out.textContent = JSON.stringify({ mode: 'http-semantic-fallback', error: String(error), simulated_response: semantic }, null, 2);
  }
};
})();
</script>

## Next steps

- [Documentation index](index.md)
