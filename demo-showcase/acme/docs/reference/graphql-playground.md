---
title: "GraphQL Playground"
description: "Interactive GraphQL query playground for Acme API."
content_type: reference
product: both
tags:
  - API
  - GraphQL
---

# GraphQL Playground

> **Powered by VeriDoc**

Endpoint (configure for your env): `https://api.acme.example/graphql`

<textarea id="gql-q" style="width:100%;height:180px;font-family:monospace">query Health { __typename }</textarea>
<button id="gql-run">Run query</button>
<pre id="gql-out" style="max-height:320px;overflow:auto;border:1px solid #dbe2ea;padding:12px;border-radius:10px"></pre>

<script>
(() => {
  const endpoint = 'https://api.acme.example/graphql';
  const run = document.getElementById('gql-run');
  const query = document.getElementById('gql-q');
  const out = document.getElementById('gql-out');
  run.onclick = async () => {
    out.textContent = 'Loading...';
    try {
      const r = await fetch(endpoint, {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({query: query.value})});
      out.textContent = await r.text();
    } catch (e) { out.textContent = String(e); }
  };
})();
</script>

## Next steps

- [Documentation index](../index.md)
