/*
 * Acme Demo Sandbox Configuration
 *
 * Provides sandbox endpoint URLs for all protocol testers
 * (REST, GraphQL, gRPC, AsyncAPI, WebSocket) in the Acme demo site.
 *
 * Endpoints are read from window.ACME_SANDBOX (set by mkdocs.yml extra JS)
 * and injected into each interactive tester at page load.
 */
(function () {
  'use strict';

  // Default config -- overridden by mkdocs.yml extra.sandbox
  var defaults = {
    rest_base_url: '',
    graphql_url: '',
    grpc_gateway_url: '',
    asyncapi_ws_url: '',
    websocket_url: ''
  };

  function getConfig() {
    // mkdocs.yml `extra` values are available in the page context.
    // We read from a global that the extra_javascript block sets,
    // or fall back to data attributes on a sentinel element.
    var cfg = window.ACME_SANDBOX || {};
    return {
      rest:      cfg.rest_base_url      || defaults.rest_base_url,
      graphql:   cfg.graphql_url        || defaults.graphql_url,
      grpc:      cfg.grpc_gateway_url   || defaults.grpc_gateway_url,
      asyncapi:  cfg.asyncapi_ws_url    || defaults.asyncapi_ws_url,
      websocket: cfg.websocket_url      || defaults.websocket_url
    };
  }

  /* ------------------------------------------------------------------ */
  /*  REST: update Swagger UI iframe src with sandbox query param        */
  /* ------------------------------------------------------------------ */
  function initRest(cfg) {
    if (!cfg.rest) return;
    var iframe = document.querySelector('iframe[src*="swagger-test"]');
    if (iframe) {
      var sep = iframe.src.indexOf('?') === -1 ? '?' : '&';
      iframe.src = iframe.src + sep + 'sandbox=' + encodeURIComponent(cfg.rest);
    }
  }

  /* ------------------------------------------------------------------ */
  /*  GraphQL: patch the live query editor fetch URL                     */
  /* ------------------------------------------------------------------ */
  function initGraphQL(cfg) {
    if (!cfg.graphql) return;
    var btn = document.getElementById('gql-run');
    if (!btn) return;
    // Replace the existing onclick with one that hits the sandbox
    btn.onclick = async function () {
      var out = document.getElementById('gql-out');
      var query = document.getElementById('gql-q');
      out.textContent = 'Executing query against sandbox...';
      try {
        var r = await fetch(cfg.graphql, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ query: query.value })
        });
        out.textContent = JSON.stringify(JSON.parse(await r.text()), null, 2);
      } catch (e) {
        out.textContent = 'Sandbox error: ' + String(e);
      }
    };
  }

  /* ------------------------------------------------------------------ */
  /*  gRPC: patch the gateway tester fetch URL                           */
  /* ------------------------------------------------------------------ */
  function initGrpc(cfg) {
    if (!cfg.grpc) return;
    var btn = document.getElementById('grpc-run');
    if (!btn) return;
    btn.onclick = async function () {
      var out = document.getElementById('grpc-out');
      out.textContent = 'Invoking RPC against sandbox...';
      try {
        var body = {
          service: document.getElementById('grpc-svc').value,
          method: document.getElementById('grpc-method').value,
          payload: JSON.parse(document.getElementById('grpc-payload').value)
        };
        var r = await fetch(cfg.grpc, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body)
        });
        out.textContent = JSON.stringify(JSON.parse(await r.text()), null, 2);
      } catch (e) {
        out.textContent = 'Sandbox error: ' + String(e);
      }
    };
  }

  /* ------------------------------------------------------------------ */
  /*  AsyncAPI: patch the WebSocket bridge tester endpoint               */
  /* ------------------------------------------------------------------ */
  function initAsyncAPI(cfg) {
    if (!cfg.asyncapi) return;
    var epInput = document.getElementById('async-ep');
    if (epInput) {
      epInput.value = cfg.asyncapi;
    }
  }

  /* ------------------------------------------------------------------ */
  /*  WebSocket: patch the WebSocket tester endpoint                     */
  /* ------------------------------------------------------------------ */
  function initWebSocket(cfg) {
    if (!cfg.websocket) return;
    var epInput = document.getElementById('ws-ep');
    if (epInput) {
      epInput.value = cfg.websocket;
    }
  }

  /* ------------------------------------------------------------------ */
  /*  Bootstrap                                                          */
  /* ------------------------------------------------------------------ */
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

  // MkDocs Material instant navigation support
  document.addEventListener('DOMContentSwitch', init);

  if (typeof MutationObserver !== 'undefined') {
    var observer = new MutationObserver(function () {
      // Re-init if new tester elements appear after SPA navigation
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
