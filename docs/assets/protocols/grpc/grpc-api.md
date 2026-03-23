---
title: GRPC API Reference
description: Auto-generated grpc reference from source contract.
content_type: reference
product: both
tags:
- Pytest Of Eudo
- Test_Multi_Protocol_Flow_Gener0
- Tmp
- Docs
- Pytest 2467
---


# GRPC Reference

Source: `/tmp/pytest-of-eudo/pytest-2467/test_multi_protocol_flow_gener0/api/proto`

Flow mode: `api-first`

## Top-level Keys

## Service Methods

- RPC method count: `4`
- `AutoDocPipelineService.CreateProject`
- `AutoDocPipelineService.GetProject`
- `AutoDocPipelineService.ListProjects`
- `AutoDocPipelineService.UpdateProject`

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
(function(){ const endpoint = "https://postman-echo.com/post";
const view = document.getElementById('grpc-endpoint-view');
const run = document.getElementById('grpc-run');
const service = document.getElementById('grpc-service');
const method = document.getElementById('grpc-method');
const payload = document.getElementById('grpc-payload');
const out = document.getElementById('grpc-output');
if (!view || !run || !service || !method || !payload || !out) return;
view.textContent = endpoint || 'not configured';
function fallback(body){
  const m = String((body && body.method) || '').toLowerCase();
  const p = (body && body.payload && typeof body.payload === 'object') ? body.payload : {};
  if (m === 'getproject') return { id: p.project_id || 'prj_abc123', name: 'Website Redesign', status: 'active' };
  if (m === 'createproject') return { id: 'prj_demo001', name: p.name || 'New Project', status: p.status || 'draft' };
  if (m === 'listprojects') return [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }];
  return { error: { code: 'UNIMPLEMENTED', message: 'Use GetProject, CreateProject, or ListProjects' } };
}
run.onclick = async function(){
  try {
    const body = { service: service.value.trim(), method: method.value.trim(), payload: JSON.parse(payload.value || '{}') };
    if (!endpoint) {
      out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(body) }, null, 2);
      return;
    }
    out.textContent = 'Loading...';
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });
    const text = await response.text();
    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(body) }, null, 2);
  } catch (error) {
    let body = { method: method.value.trim(), payload: {} };
    try { body.payload = JSON.parse(payload.value || '{}'); } catch (_) {}
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(body) }, null, 2);
  }
};
})();
</script>

## Next steps

- [Documentation index](../index.md)
