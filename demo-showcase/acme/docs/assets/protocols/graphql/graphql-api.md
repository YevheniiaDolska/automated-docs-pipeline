---
title: GRAPHQL API Reference
description: Auto-generated graphql reference from source contract.
content_type: reference
product: both
tags:
- C
- Documents
- Development
- Auto Doc Pipeline
- Users
- Mnt
- Docs
- Kroha
last_reviewed: null
original_author: null
---


# GRAPHQL Reference

Source: `reports/acme-demo/contracts/graphql.schema.graphql`

Flow mode: `api-first`

## Operations

- Query count: `2`
- Mutation count: `1`
- Subscription count: `1`
- Queries: `health`, `project`
- Mutations: `createProject`
- Subscriptions: `projectUpdated`

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
(function(){ const endpoint = "";
const view = document.getElementById('graphql-endpoint-view');
const run = document.getElementById('graphql-run');
const query = document.getElementById('graphql-query');
const out = document.getElementById('graphql-output');
if (!view || !run || !query || !out) return;
view.textContent = endpoint || 'not configured';
run.onclick = async function(){
  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.graphql.graphql_endpoint'; return; }
  out.textContent = 'Loading...';
  try {
    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });
    const text = await response.text();
    out.textContent = text;
  } catch (error) { out.textContent = String(error); }
};
})();
</script>

## Next steps

- [Documentation index](index.md)
