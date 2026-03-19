---
title: GRPC API Reference
description: Auto-generated grpc reference from source contract.
content_type: reference
product: both
tags:
- Documents
- C
- Mnt
- Development
- Docs
- Kroha
- Auto Doc Pipeline
- Users
last_reviewed: null
original_author: null
---


# GRPC Reference

Source: `reports/acme-demo/contracts/grpc`

Flow mode: `api-first`

## Top-level Keys

## Service Methods

- RPC method count: `1`
- `ProjectService.GetProject`

## Interactive gRPC Tester

This tester uses an HTTP gateway/adapter endpoint, so docs users can trigger gRPC methods from browser.

<div id="grpc-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Gateway Endpoint:</strong> <code id="grpc-endpoint-view"></code></p>
  <label>Service</label><br/><input id="grpc-service" style="width:100%" placeholder="GreeterService"/><br/>
  <label>Method</label><br/><input id="grpc-method" style="width:100%" placeholder="SayHello"/><br/>
  <label>Payload (JSON)</label><br/><textarea id="grpc-payload" rows="8" style="width:100%; font-family:monospace;">{
  "name": "world"
}</textarea><br/>
  <button id="grpc-run">Invoke</button>
  <pre id="grpc-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "";
const view = document.getElementById('grpc-endpoint-view');
const run = document.getElementById('grpc-run');
const service = document.getElementById('grpc-service');
const method = document.getElementById('grpc-method');
const payload = document.getElementById('grpc-payload');
const out = document.getElementById('grpc-output');
if (!view || !run || !service || !method || !payload || !out) return;
view.textContent = endpoint || 'not configured';
run.onclick = async function(){
  if (!endpoint) { out.textContent = 'Gateway endpoint is not configured in runtime.api_protocol_settings.grpc.grpc_gateway_endpoint'; return; }
  out.textContent = 'Loading...';
  try {
    const body = { service: service.value.trim(), method: method.value.trim(), payload: JSON.parse(payload.value || '{}') };
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

## Next steps

- [Documentation index](index.md)
