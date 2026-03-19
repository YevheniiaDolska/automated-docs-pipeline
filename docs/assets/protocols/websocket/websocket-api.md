---
title: WEBSOCKET API Reference
description: Auto-generated websocket reference from source contract.
content_type: reference
product: both
tags:
- Mnt
- Development
- Users
- Auto Doc Pipeline
- Kroha
- Documents
- Docs
- C
last_reviewed: null
original_author: null
---


# WEBSOCKET Reference

Source: `reports/acme-demo/contracts/websocket.yaml`

Flow mode: `api-first`

## Top-level Keys

- `channels`

## Channels/Events

- Channel count: `1`
- `project.updated`

## Interactive WebSocket Tester

<div id="websocket-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="websocket-endpoint-view"></code></p>
  <textarea id="websocket-message" rows="8" style="width:100%; font-family:monospace;">{
  "action": "ping"
}</textarea><br/>
  <button id="websocket-send">Connect + Send</button>
  <pre id="websocket-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "";
const view = document.getElementById('websocket-endpoint-view');
const send = document.getElementById('websocket-send');
const msg = document.getElementById('websocket-message');
const out = document.getElementById('websocket-output');
if (!view || !send || !msg || !out) return;
view.textContent = endpoint || 'not configured';
send.onclick = function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.websocket.websocket_endpoint'; return; }
  try {
    const socket = new WebSocket(endpoint);
    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'message sent'; };
    socket.onmessage = function(e){ out.textContent = String(e.data); socket.close(); };
    socket.onerror = function(e){ out.textContent = String(e); };
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

## Next steps

- [Documentation index](../../../index.md)
