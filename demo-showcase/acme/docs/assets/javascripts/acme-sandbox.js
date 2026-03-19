/*
 * Acme Demo Sandbox Controller
 *
 * Patches all protocol interactive testers to use Postman mock
 * server endpoints with proper authentication headers.
 *
 * Reads config from window.ACME_SANDBOX (set by sandbox-config.js).
 */
(function () {
  'use strict';

  function getConfig() {
    var cfg = window.ACME_SANDBOX || {};
    return {
      apiKey:    cfg.postman_api_key    || '',
      rest:      cfg.rest_base_url      || '',
      graphql:   cfg.graphql_url        || '',
      grpc:      cfg.grpc_gateway_url   || '',
      asyncapi:  cfg.asyncapi_ws_url    || '',
      websocket: cfg.websocket_url      || ''
    };
  }

  function sandboxHeaders(apiKey) {
    var h = { 'content-type': 'application/json' };
    if (apiKey) { h['x-api-key'] = apiKey; }
    return h;
  }

  function safeParseJson(text) {
    try {
      return JSON.parse(text);
    } catch (e) {
      return null;
    }
  }

  function normalize(str) {
    return String(str || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function graphqlFallback(queryText) {
    var q = normalize(queryText);
    var idMatch = String(queryText || '').match(/project\s*\(\s*id\s*:\s*"([^"]+)"/i);
    var projectId = idMatch ? idMatch[1] : 'prj_abc123';
    if (q.indexOf('health') !== -1) {
      return { data: { health: { status: 'ok', version: '1.0.0', timestamp: new Date().toISOString() } } };
    }
    if (q.indexOf('mutation') !== -1 && q.indexOf('createproject') !== -1) {
      return {
        data: {
          createProject: {
            id: 'prj_new_' + Date.now(),
            name: 'Demo Project',
            status: 'active'
          }
        }
      };
    }
    if (q.indexOf('project') !== -1) {
      return {
        data: {
          project: {
            id: projectId,
            name: 'Acme Demo Project',
            status: 'active',
            owner: { id: 'usr_001', email: 'owner@acme.example' }
          }
        }
      };
    }
    return {
      data: {
        echo: {
          note: 'Fallback sandbox response',
          query: String(queryText || '').slice(0, 300)
        }
      }
    };
  }

  function graphqlRelevant(queryText, payload) {
    var q = normalize(queryText);
    if (!payload || typeof payload !== 'object' || !payload.data) return false;
    if (q.indexOf('health') !== -1) return !!(payload.data && payload.data.health);
    if (q.indexOf('createproject') !== -1) return !!(payload.data && payload.data.createProject);
    if (q.indexOf('project') !== -1) return !!(payload.data && payload.data.project);
    return true;
  }

  function grpcFallback(body) {
    var service = String((body && body.service) || 'acme.project.v1.ProjectService');
    var method = String((body && body.method) || 'Unknown');
    var payload = (body && body.payload) || {};
    var methodLc = method.toLowerCase();
    if (methodLc === 'createproject') {
      return {
        code: 0,
        message: 'OK',
        data: {
          id: 'prj_new_' + Date.now(),
          name: payload.name || 'Demo Project',
          status: 'active'
        }
      };
    }
    if (methodLc === 'getproject') {
      return {
        code: 0,
        message: 'OK',
        data: {
          id: payload.id || 'prj_abc123',
          name: 'Acme Demo Project',
          status: 'active'
        }
      };
    }
    if (methodLc === 'listprojects') {
      return {
        code: 0,
        message: 'OK',
        data: {
          items: [
            { id: 'prj_abc123', name: 'Alpha', status: 'active' },
            { id: 'prj_def456', name: 'Beta', status: 'draft' }
          ]
        }
      };
    }
    return { code: 0, message: 'OK', data: { service: service, method: method, echo: payload } };
  }

  function grpcRelevant(body, payload) {
    if (!payload || typeof payload !== 'object') return false;
    var method = String((body && body.method) || '').toLowerCase();
    if (method === 'createproject') return !!(payload.data && payload.data.id);
    if (method === 'getproject') return !!(payload.data && payload.data.id);
    if (method === 'listprojects') return !!(payload.data && payload.data.items);
    return true;
  }

  /* REST: Swagger iframe gets sandbox URL via query param */
  function initRest(cfg) {
    if (!cfg.rest) return;
    var iframe = document.querySelector('iframe[src*="swagger-test"]');
    if (iframe && iframe.src.indexOf('sandbox=') === -1) {
      var sep = iframe.src.indexOf('?') === -1 ? '?' : '&';
      iframe.src = iframe.src + sep + 'sandbox=' + encodeURIComponent(cfg.rest);
    }
  }

  /* GraphQL: patch live query editor */
  function initGraphQL(cfg) {
    if (!cfg.graphql) return;
    var btn = document.getElementById('gql-run');
    if (!btn) return;
    var out = document.getElementById('gql-out');
    var query = document.getElementById('gql-q');
    if (out && !out.textContent) { out.textContent = 'Sandbox ready: ' + cfg.graphql; }
    btn.onclick = async function () {
      out.textContent = 'Executing query against sandbox...';
      try {
        var queryText = query.value;
        var r = await fetch(cfg.graphql, {
          method: 'POST',
          headers: sandboxHeaders(cfg.apiKey),
          body: JSON.stringify({ query: queryText })
        });
        var raw = await r.text();
        var parsed = safeParseJson(raw);
        if (!graphqlRelevant(queryText, parsed)) {
          parsed = graphqlFallback(queryText);
          parsed.__source = 'local-fallback';
        }
        out.textContent = JSON.stringify(parsed || graphqlFallback(queryText), null, 2);
      } catch (e) {
        var fallback = graphqlFallback(query.value);
        fallback.__source = 'local-fallback';
        fallback.__error = String(e);
        out.textContent = JSON.stringify(fallback, null, 2);
      }
    };
  }

  /* gRPC: patch gateway invoker */
  function initGrpc(cfg) {
    if (!cfg.grpc) return;
    var btn = document.getElementById('grpc-run');
    if (!btn) return;
    var out = document.getElementById('grpc-out');
    if (out && !out.textContent) { out.textContent = 'Sandbox ready: ' + cfg.grpc; }
    btn.onclick = async function () {
      out.textContent = 'Invoking RPC against sandbox...';
      var body = null;
      try {
        body = {
          service: document.getElementById('grpc-svc').value,
          method: document.getElementById('grpc-method').value,
          payload: JSON.parse(document.getElementById('grpc-payload').value)
        };
        var r = await fetch(cfg.grpc, {
          method: 'POST',
          headers: sandboxHeaders(cfg.apiKey),
          body: JSON.stringify(body)
        });
        var raw = await r.text();
        var parsed = safeParseJson(raw);
        if (!grpcRelevant(body, parsed)) {
          parsed = grpcFallback(body);
          parsed.__source = 'local-fallback';
        }
        out.textContent = JSON.stringify(parsed || grpcFallback(body), null, 2);
      } catch (e) {
        var fallback = grpcFallback(body || {});
        fallback.__source = 'local-fallback';
        fallback.__error = String(e);
        out.textContent = JSON.stringify(fallback, null, 2);
      }
    };
  }

  /* AsyncAPI: set WebSocket bridge endpoint */
  function initAsyncAPI(cfg) {
    if (!cfg.asyncapi) return;
    var epInput = document.getElementById('async-ep');
    if (epInput) { epInput.value = cfg.asyncapi; }
  }

  /* WebSocket: set tester endpoint */
  function initWebSocket(cfg) {
    if (!cfg.websocket) return;
    var epInput = document.getElementById('ws-ep');
    if (epInput) { epInput.value = cfg.websocket; }
  }

  function init() {
    var cfg = getConfig();
    initRest(cfg);
    initGraphQL(cfg);
    initGrpc(cfg);
    initAsyncAPI(cfg);
    initWebSocket(cfg);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  document.addEventListener('DOMContentSwitch', init);

  if (typeof MutationObserver !== 'undefined') {
    var observer = new MutationObserver(function () {
      if (document.getElementById('gql-run') ||
          document.getElementById('grpc-run') ||
          document.getElementById('async-ep') ||
          document.getElementById('ws-ep')) {
        init();
      }
    });

    function observeContent() {
      var target =
        document.querySelector('[data-md-component="content"]') ||
        document.querySelector('article') ||
        document.body;
      observer.observe(target, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', observeContent);
    } else {
      observeContent();
    }
  }
})();
