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
      rest:      cfg.rest_base_url      || '',
      asyncapi:  cfg.asyncapi_ws_url    || '',
      websocket: cfg.websocket_url      || ''
    };
  }

  function normalize(str) {
    return String(str || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function graphqlFallback(queryText) {
    var q = normalize(queryText);
    var idMatch = String(queryText || '').match(/id\s*:\s*"([^"]+)"/i);
    var projectId = idMatch ? idMatch[1] : 'prj_abc123';
    var nameMatch = String(queryText || '').match(/name\s*:\s*"([^"]+)"/i);
    var statusMatch = String(queryText || '').match(/status\s*:\s*"([^"]+)"/i);
    if (q.indexOf('health') !== -1) {
      return { data: { health: { status: 'healthy', version: '2.4.1', uptime_seconds: 86400 } } };
    }
    if (q.indexOf('mutation') !== -1 && q.indexOf('updateproject') !== -1) {
      return {
        data: {
          updateProject: {
            id: projectId,
            name: nameMatch ? nameMatch[1] : 'Website Redesign',
            status: statusMatch ? statusMatch[1] : 'active',
            createdAt: '2026-01-15T09:00:00Z',
            updatedAt: new Date().toISOString()
          }
        }
      };
    }
    if (q.indexOf('mutation') !== -1 && q.indexOf('createproject') !== -1) {
      return {
        data: {
          createProject: {
            id: 'prj_' + Math.random().toString(36).slice(2, 8),
            name: nameMatch ? nameMatch[1] : 'New Project',
            status: statusMatch ? statusMatch[1] : 'draft',
            createdAt: new Date().toISOString()
          }
        }
      };
    }
    if (q.indexOf('subscription') !== -1 && q.indexOf('projectupdated') !== -1) {
      return {
        data: {
          projectUpdated: {
            id: projectId,
            name: 'Website Redesign',
            status: 'active',
            updatedAt: new Date().toISOString()
          }
        }
      };
    }
    if (q.indexOf('projects') !== -1) {
      return {
        data: {
          projects: [
            { id: 'prj_abc123', name: 'Website Redesign', status: 'active', createdAt: '2026-01-15T09:00:00Z' },
            { id: 'prj_def456', name: 'Mobile App Launch', status: 'active', createdAt: '2026-02-20T11:00:00Z' },
            { id: 'prj_ghi789', name: 'API Documentation', status: 'draft', createdAt: '2026-03-01T14:30:00Z' }
          ]
        }
      };
    }
    if (q.indexOf('project') !== -1) {
      return {
        data: {
          project: {
            id: projectId,
            name: 'Website Redesign',
            status: 'active',
            createdAt: '2026-01-15T09:00:00Z',
            updatedAt: '2026-03-19T14:30:00Z'
          }
        }
      };
    }
    return { data: null, errors: [{ message: 'Unknown query. Try: health, project, projects, createProject, updateProject, or projectUpdated.', extensions: { code: 'UNKNOWN_QUERY' } }] };
  }


  function grpcFallback(body) {
    var method = String((body && body.method) || 'Unknown');
    var payload = (body && body.payload) || {};
    var methodLc = method.toLowerCase();
    if (methodLc === 'getproject') {
      return {
        id: payload.project_id || 'prj_abc123',
        name: 'Website Redesign',
        status: 'active'
      };
    }
    if (methodLc === 'createproject') {
      return {
        id: 'prj_' + Math.random().toString(36).slice(2, 8),
        name: payload.name || 'New Project',
        status: payload.status || 'draft'
      };
    }
    if (methodLc === 'listprojects') {
      return [
        { id: 'prj_abc123', name: 'Website Redesign', status: 'active' },
        { id: 'prj_def456', name: 'Mobile App Launch', status: 'active' },
        { id: 'prj_ghi789', name: 'API Documentation', status: 'draft' }
      ];
    }
    return { error: { code: 'UNIMPLEMENTED', message: 'Method ' + method + ' is not implemented. Try: GetProject, CreateProject, or ListProjects.' } };
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

  /* GraphQL: local mock responses for reliable demo */
  function initGraphQL(cfg) {
    var btn = document.getElementById('gql-run');
    if (!btn) return;
    var out = document.getElementById('gql-out');
    var query = document.getElementById('gql-q');
    if (out && !out.textContent) { out.textContent = 'Sandbox ready'; }
    btn.onclick = function () {
      out.textContent = 'Executing query...';
      var result = graphqlFallback(query.value);
      setTimeout(function () {
        out.textContent = JSON.stringify(result, null, 2);
      }, 300);
    };
  }

  /* gRPC: local mock responses for reliable demo */
  function initGrpc(cfg) {
    var btn = document.getElementById('grpc-run');
    if (!btn) return;
    var out = document.getElementById('grpc-out');
    if (out && !out.textContent) { out.textContent = 'Sandbox ready'; }
    btn.onclick = function () {
      out.textContent = 'Invoking RPC...';
      var body = null;
      try {
        body = {
          service: document.getElementById('grpc-svc').value,
          method: document.getElementById('grpc-method').value,
          payload: JSON.parse(document.getElementById('grpc-payload').value)
        };
      } catch (e) {
        out.textContent = 'Error: invalid JSON payload';
        return;
      }
      var result = grpcFallback(body);
      setTimeout(function () {
        out.textContent = JSON.stringify(result, null, 2);
      }, 300);
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
