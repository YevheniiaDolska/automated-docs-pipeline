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
        var r = await fetch(cfg.graphql, {
          method: 'POST',
          headers: sandboxHeaders(cfg.apiKey),
          body: JSON.stringify({ query: query.value })
        });
        out.textContent = JSON.stringify(JSON.parse(await r.text()), null, 2);
      } catch (e) {
        out.textContent = 'Sandbox error: ' + String(e);
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
      try {
        var body = {
          service: document.getElementById('grpc-svc').value,
          method: document.getElementById('grpc-method').value,
          payload: JSON.parse(document.getElementById('grpc-payload').value)
        };
        var r = await fetch(cfg.grpc, {
          method: 'POST',
          headers: sandboxHeaders(cfg.apiKey),
          body: JSON.stringify(body)
        });
        out.textContent = JSON.stringify(JSON.parse(await r.text()), null, 2);
      } catch (e) {
        out.textContent = 'Sandbox error: ' + String(e);
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
