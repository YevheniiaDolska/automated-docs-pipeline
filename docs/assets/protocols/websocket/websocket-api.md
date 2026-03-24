---
title: WEBSOCKET API Reference
description: Auto-generated websocket reference from source contract.
content_type: reference
product: both
tags:
- Pytest Of Eudo
- Pytest 2489
- Docs
- Tmp
- Test_Multi_Protocol_Flow_Gener0
---


# WEBSOCKET Reference

Source: `/tmp/pytest-of-eudo/pytest-2489/test_multi_protocol_flow_gener0/api/websocket.yaml`

Flow mode: `api-first`

## Top-level Keys

- `channels`
- `info`

## Channels/Events

- Channel count: `1`
- `project.updated`

## Interactive WebSocket Tester

> Sandbox semantic mode: this tester returns protocol-aware responses based on message type/action.

<div id="websocket-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="websocket-endpoint-view"></code></p>
  <textarea id="websocket-message" rows="8" style="width:100%; font-family:monospace;">{
  "type": "subscribe",
  "request_id": "req_001",
  "payload": {"channel": "project.updated", "filters": {"project_id": "prj_abc123"}}
}</textarea><br/>
  <button id="websocket-send">Connect + Send</button>
  <pre id="websocket-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "wss://echo.websocket.events";
const view = document.getElementById('websocket-endpoint-view');
const send = document.getElementById('websocket-send');
const msg = document.getElementById('websocket-message');
const out = document.getElementById('websocket-output');
if (!view || !send || !msg || !out) return;
view.textContent = endpoint || 'not configured';
function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }
function semanticResponse(input){
  const req = parseJson(input);
  const payload = (req && req.payload && typeof req.payload === 'object') ? req.payload : {};
  const type = String(req.type || req.action || '').toLowerCase();
  const requestId = req.request_id || ('req_' + Date.now());
  const channel = String(payload.channel || payload.topic || 'project.updated');
  const projectId = String((payload.filters && payload.filters.project_id) || payload.project_id || 'prj_abc123');
  if (type === 'ping') return { type: 'pong', request_id: requestId, payload: { ts: new Date().toISOString() } };
  if (type === 'subscribe') return { type: 'ack', request_id: requestId, payload: { status: 'subscribed', channel: channel, filters: payload.filters || {} } };
  if (type === 'unsubscribe') return { type: 'ack', request_id: requestId, payload: { status: 'unsubscribed', channel: channel } };
  if (type === 'publish') return { type: 'event', request_id: requestId, payload: { event_type: channel, data: Object.assign({ project_id: projectId, status: 'active' }, (payload.data && typeof payload.data === 'object') ? payload.data : {}) } };
  if (type === 'get_project' || type === 'project.get' || type === 'query') return { type: 'event', request_id: requestId, payload: { event_type: 'project.snapshot', data: { project_id: projectId, name: 'Website Redesign', status: 'active', updated_at: new Date().toISOString() } } };
  if (type === 'list_projects' || type === 'project.list') return { type: 'event', request_id: requestId, payload: { event_type: 'project.list', data: [{ project_id: 'prj_abc123', status: 'active' }, { project_id: 'prj_def456', status: 'draft' }] } };
  return { type: 'ack', request_id: requestId, payload: { status: 'accepted', echo: req, hint: 'Use: ping, subscribe, unsubscribe, publish, get_project, list_projects' } };
}
send.onclick = function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.websocket.websocket_endpoint'; return; }
  try {
    const socket = new WebSocket(endpoint);
    let received = false;
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'message sent'; };
    socket.onmessage = function(e){
      received = true;
      const simulated = semanticResponse(e.data);
      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: simulated }, null, 2);
      socket.close();
    };
    socket.onerror = function(){
      const simulated = semanticResponse(msg.value);
      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: simulated }, null, 2);
    };
    setTimeout(function(){
      if (!received) {
        const simulated = semanticResponse(msg.value);
        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: simulated }, null, 2);
        try { socket.close(); } catch (_) {}
      }
    }, 1500);
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

## Next steps

- [Documentation index](../index.md)
