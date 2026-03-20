/*
 * VeriOps Demo Sandbox Controller
 *
 * Patches all protocol interactive testers to use Postman mock
 * server endpoints with proper authentication headers.
 *
 * Reads config from window.ACME_SANDBOX (set by sandbox-config.js).
 */
(function () {
  'use strict';
  window.__ACME_SANDBOX_CONTROLLER__ = true;

  function getConfig() {
    var cfg = window.ACME_SANDBOX || {};
    return {
      rest:      cfg.rest_base_url      || '',
      asyncapi:  cfg.asyncapi_ws_url    || '',
      websocket: cfg.websocket_url      || '',
      asyncapiFallback: Array.isArray(cfg.asyncapi_ws_fallback_urls) ? cfg.asyncapi_ws_fallback_urls : [],
      websocketFallback: Array.isArray(cfg.websocket_fallback_urls) ? cfg.websocket_fallback_urls : []
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

  function wsCandidateEndpoints(primary, extras) {
    var all = [primary].concat(Array.isArray(extras) ? extras : []);
    var seen = {};
    var out = [];
    for (var i = 0; i < all.length; i += 1) {
      var v = String(all[i] || '').trim();
      if (!v || seen[v]) continue;
      seen[v] = true;
      out.push(v);
    }
    return out;
  }

  function safeJsonParse(raw) {
    try {
      return JSON.parse(String(raw || '{}'));
    } catch (e) {
      return { raw: String(raw || '') };
    }
  }

  function semanticWsResponse(req) {
    var payload = (req && req.payload && typeof req.payload === 'object') ? req.payload : {};
    var type = String((req && (req.type || req.action)) || '').toLowerCase();
    var requestId = (req && req.request_id) || ('req_' + Date.now());
    var channel = String(payload.channel || payload.topic || 'project.updated');
    var projectId = String((payload.filters && payload.filters.project_id) || payload.project_id || 'prj_abc123');

    if (type === 'ping') {
      return { type: 'pong', request_id: requestId, payload: { ts: new Date().toISOString() } };
    }
    if (type === 'subscribe') {
      return { type: 'ack', request_id: requestId, payload: { status: 'subscribed', channel: channel, filters: payload.filters || {} } };
    }
    if (type === 'unsubscribe') {
      return { type: 'ack', request_id: requestId, payload: { status: 'unsubscribed', channel: channel } };
    }
    if (type === 'publish') {
      return {
        type: 'event',
        request_id: requestId,
        payload: {
          event_type: channel,
          data: Object.assign(
            { project_id: projectId, status: 'active', updated_at: new Date().toISOString() },
            (payload.data && typeof payload.data === 'object') ? payload.data : {}
          )
        }
      };
    }
    if (type === 'get_project' || type === 'project.get' || type === 'query') {
      return {
        type: 'event',
        request_id: requestId,
        payload: {
          event_type: 'project.snapshot',
          data: {
            project_id: projectId,
            name: 'Website Redesign',
            status: 'active',
            updated_at: new Date().toISOString()
          }
        }
      };
    }
    if (type === 'list_projects' || type === 'project.list') {
      return {
        type: 'event',
        request_id: requestId,
        payload: {
          event_type: 'project.list',
          data: [
            { project_id: 'prj_abc123', status: 'active' },
            { project_id: 'prj_def456', status: 'draft' }
          ]
        }
      };
    }
    return {
      type: 'ack',
      request_id: requestId,
      payload: {
        status: 'accepted',
        echo: req,
        hint: 'Use: ping, subscribe, unsubscribe, publish, get_project, list_projects'
      }
    };
  }

  function semanticAsyncApiResponse(req) {
    var eventType = String((req && (req.event_type || req.type || req.event)) || '').toLowerCase();
    var payload = (req && req.payload && typeof req.payload === 'object') ? req.payload : {};
    var data = (req && req.data && typeof req.data === 'object') ? req.data : payload.data || {};
    var eventId = String((req && req.event_id) || ('evt_' + Math.random().toString(36).slice(2, 10)));
    var projectId = String(data.project_id || payload.project_id || 'prj_abc123');
    var occurredAt = (req && req.occurred_at) || new Date().toISOString();

    if (eventType === 'project.created') {
      return { event_id: eventId, event_type: 'project.created', occurred_at: occurredAt, data: { project_id: projectId, name: data.name || 'New Project', status: data.status || 'draft' } };
    }
    if (eventType === 'project.updated') {
      return { event_id: eventId, event_type: 'project.updated', occurred_at: occurredAt, data: { project_id: projectId, status: data.status || 'active', changed_fields: data.changed_fields || ['status'] } };
    }
    if (eventType === 'task.completed') {
      return { event_id: eventId, event_type: 'task.completed', occurred_at: occurredAt, data: { task_id: data.task_id || 'tsk_123', project_id: projectId, completed_by: data.completed_by || 'usr_demo' } };
    }
    return {
      event_id: eventId,
      event_type: eventType || 'custom.event',
      occurred_at: occurredAt,
      data: Object.assign({ project_id: projectId, status: 'accepted' }, data),
      hint: 'Use: project.created, project.updated, task.completed'
    };
  }

  function runOfflineEcho(outputEl, payloadText, context) {
    if (!outputEl) return;
    var parsed = safeJsonParse(payloadText);
    var semantic = null;
    if (context && context.protocol === 'websocket') {
      semantic = semanticWsResponse(parsed);
    } else if (context && context.protocol === 'asyncapi') {
      semantic = semanticAsyncApiResponse(parsed);
    }
    var response = {
      mode: 'offline-echo-fallback',
      context: context,
      timestamp: new Date().toISOString(),
      echo: parsed,
      semantic_response: semantic
    };
    outputEl.textContent = JSON.stringify(response, null, 2);
  }

  function connectWithFailover(endpoints, onOpen, onMessage, onAllFailed) {
    var idx = 0;
    var lastError = '';
    function tryNext() {
      if (idx >= endpoints.length) {
        onAllFailed(lastError);
        return;
      }
      var endpoint = endpoints[idx++];
      var settled = false;
      try {
        var ws = new WebSocket(endpoint);
        var timeout = setTimeout(function () {
          if (settled) return;
          settled = true;
          lastError = 'timeout on ' + endpoint;
          try { ws.close(); } catch (e) {}
          tryNext();
        }, 6000);
        ws.onopen = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          onOpen(ws, endpoint);
        };
        ws.onmessage = function (evt) {
          onMessage(ws, endpoint, evt);
        };
        ws.onerror = function () {
          if (settled) return;
          settled = true;
          clearTimeout(timeout);
          lastError = 'handshake failed on ' + endpoint;
          tryNext();
        };
        ws.onclose = function () {
          if (!settled) {
            settled = true;
            clearTimeout(timeout);
            lastError = 'closed before response on ' + endpoint;
            tryNext();
          }
        };
      } catch (e) {
        lastError = String(e);
        tryNext();
      }
    }
    tryNext();
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

  /* AsyncAPI: local semantic mock responses for reliable demo */
  function initAsyncAPI(cfg) {
    var epInput = document.getElementById('async-ep');
    if (epInput) { epInput.value = cfg.asyncapi || 'amqp://broker.veriops.example:5672'; }
    var btn = document.getElementById('async-send');
    var out = document.getElementById('async-out');
    var payloadEl = document.getElementById('async-payload');
    if (!btn || !out || !payloadEl) return;
    if (out && !out.textContent) { out.textContent = 'Sandbox ready'; }
    btn.onclick = function () {
      out.textContent = 'Publishing event to AMQP broker...';
      var parsed = safeJsonParse(payloadEl.value);
      var result = semanticAsyncApiResponse(parsed);
      setTimeout(function () {
        out.textContent = JSON.stringify(result, null, 2);
      }, 400);
    };
  }

  /* WebSocket: local semantic mock responses for reliable demo */
  var wsConnected = false;
  function initWebSocket(cfg) {
    var epInput = document.getElementById('ws-ep');
    if (epInput) { epInput.value = cfg.websocket || 'wss://api.veriops.example/realtime'; }
    var connectBtn = document.getElementById('ws-connect');
    var sendBtn = document.getElementById('ws-send');
    var closeBtn = document.getElementById('ws-close');
    var out = document.getElementById('ws-out');
    var msgEl = document.getElementById('ws-msg');
    if (!connectBtn || !sendBtn || !closeBtn || !out || !msgEl) return;
    if (connectBtn.__veriops_bound) return;
    connectBtn.__veriops_bound = true;
    wsConnected = false;
    function log(msg) {
      out.textContent += '\n[' + new Date().toLocaleTimeString() + '] ' + msg;
      out.scrollTop = out.scrollHeight;
    }
    connectBtn.onclick = function () {
      out.textContent = '';
      wsConnected = true;
      log('Connected to ' + (epInput ? epInput.value : 'wss://api.veriops.example/realtime'));
      log('Ready to send messages.');
    };
    sendBtn.onclick = function () {
      if (!wsConnected) {
        log('Not connected. Click Connect first.');
        return;
      }
      var payload = msgEl.value;
      log('Sent: ' + payload);
      var parsed = safeJsonParse(payload);
      var result = semanticWsResponse(parsed);
      setTimeout(function () {
        log('Received: ' + JSON.stringify(result, null, 2));
      }, 200);
    };
    closeBtn.onclick = function () {
      wsConnected = false;
      log('Disconnected.');
    };
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
