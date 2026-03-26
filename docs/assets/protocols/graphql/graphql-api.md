---
title: GRAPHQL API Reference
description: Auto-generated graphql reference from source contract.
content_type: reference
product: both
tags:
- Kroha
- Docs
- Users
- Development
- Mnt
- C
- Auto Doc Pipeline
- Documents
last_reviewed: '2026-03-26'
original_author: Kroha
---


# GRAPHQL Reference

Source: `/tmp/pytest-of-eudo/pytest-2642/test_multi_protocol_flow_e2e_e0/schema.graphql`

Flow mode: `api-first`

## Operations

- Query count: `1`
- Mutation count: `0`
- Subscription count: `0`
- Queries: `health`

## Interactive GraphQL Playground

<div id="graphql-playground" style="border:1px solid #d1d5db; padding:12px; border-radius:8px;">
  <p><strong>Endpoint:</strong> <code id="graphql-endpoint-view"></code></p>
  <textarea id="graphql-query" rows="12" style="width:100%; font-family:monospace;">query HealthCheck {
  __typename
}</textarea>
  <br/>
  <button id="graphql-run">Run Query</button>
  <pre id="graphql-output" style="margin-top:12px; max-height:320px; overflow:auto;"></pre>
</div>
<script>
(function(){ const endpoint = "https://postman-echo.com/post";
const view = document.getElementById('graphql-endpoint-view');
const run = document.getElementById('graphql-run');
const query = document.getElementById('graphql-query');
const out = document.getElementById('graphql-output');
if (!view || !run || !query || !out) return;
view.textContent = endpoint || 'not configured';
function normalize(v){ return String(v || '').replace(/\s+/g, ' ').trim().toLowerCase(); }
function fallback(queryText){
  const q = normalize(queryText);
  const idMatch = String(queryText || '').match(/id\s*:\s*\"([^\"]+)\"/i);
  const projectId = idMatch ? idMatch[1] : 'prj_abc123';
  if (q.indexOf('health') !== -1) return { data: { health: { status: 'healthy', version: '1.0.0' } } };
  if (q.indexOf('mutation') !== -1 && q.indexOf('createproject') !== -1) return { data: { createProject: { id: 'prj_demo001', name: 'New Project', status: 'draft' } } };
  if (q.indexOf('mutation') !== -1 && q.indexOf('updateproject') !== -1) return { data: { updateProject: { id: projectId, status: 'active', updatedAt: new Date().toISOString() } } };
  if (q.indexOf('projects') !== -1) return { data: { projects: [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }] } };
  if (q.indexOf('project') !== -1) return { data: { project: { id: projectId, name: 'Website Redesign', status: 'active' } } };
  return { data: null, errors: [{ message: 'Unknown query. Use: health, project, projects, createProject, updateProject' }] };
}
run.onclick = async function(){
  if (!endpoint) {
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(query.value) }, null, 2);
    return;
  }
  out.textContent = 'Loading...';
  try {
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });
    const text = await response.text();
    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(query.value) }, null, 2);
  } catch (error) {
    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(query.value) }, null, 2);
  }
};
})();
</script>

## Next steps

- [Documentation index](index.md)
