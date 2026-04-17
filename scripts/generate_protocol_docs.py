#!/usr/bin/env python3
"""Generate protocol reference markdown from contract sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.api_protocols import default_asyncapi_ws_endpoint, default_websocket_endpoint

def _load_source(path: Path) -> Any:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    return text


def _extract_graphql_ops(schema_text: str, type_name: str) -> list[str]:
    block = re.search(rf"type\s+{re.escape(type_name)}\s*\{{(.*?)\}}", schema_text, re.DOTALL)
    if not block:
        return []
    body = block.group(1)
    ops: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split("(", 1)[0].split(":", 1)[0].strip()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            ops.append(name)
    return sorted(set(ops))


def _extract_grpc_methods(source_path: Path, payload: Any) -> list[tuple[str, str]]:
    methods: list[tuple[str, str]] = []

    def parse_proto_text(text: str) -> None:
        current_service = ""
        for raw in text.splitlines():
            line = raw.strip()
            svc = re.match(r"^service\s+([A-Za-z0-9_]+)\s*\{", line)
            if svc:
                current_service = svc.group(1)
                continue
            if line == "}":
                current_service = ""
                continue
            rpc = re.match(r"^rpc\s+([A-Za-z0-9_]+)\s*\(", line)
            if rpc and current_service:
                methods.append((current_service, rpc.group(1)))

    if isinstance(payload, str) and source_path.suffix.lower() == ".proto":
        parse_proto_text(payload)
        return methods

    if source_path.is_dir():
        for proto in sorted(source_path.rglob("*.proto")):
            parse_proto_text(proto.read_text(encoding="utf-8"))

    return sorted(set(methods))


def _extract_async_channels(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    channels = payload.get("channels", {})
    if not isinstance(channels, dict):
        return []
    return sorted(str(key) for key in channels.keys())


def _extract_websocket_channels(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    channels = payload.get("channels", payload.get("events", {}))
    if isinstance(channels, dict):
        return sorted(str(key) for key in channels.keys())
    return []


def _render_graphql_playground(endpoint: str) -> list[str]:
    endpoint_js = json.dumps(endpoint)
    return [
        "## Interactive GraphQL Playground",
        "",
        "<!-- vale off -->",
        "<div id=\"graphql-playground\" style=\"border:1px solid #d1d5db; padding:12px; border-radius:8px;\">",
        "  <p><strong>Endpoint:</strong> <code id=\"graphql-endpoint-view\"></code></p>",
        "  <textarea id=\"graphql-query\" rows=\"12\" style=\"width:100%; font-family:monospace;\">query HealthCheck {\n  __typename\n}</textarea>",
        "  <br/>",
        "  <button id=\"graphql-run\">Run Query</button>",
        "  <pre id=\"graphql-output\" style=\"margin-top:12px; max-height:320px; overflow:auto;\"></pre>",
        "</div>",
        "<script>",
        f"(function(){{ const endpoint = {endpoint_js};",
        "const view = document.getElementById('graphql-endpoint-view');",
        "const run = document.getElementById('graphql-run');",
        "const query = document.getElementById('graphql-query');",
        "const out = document.getElementById('graphql-output');",
        "if (!view || !run || !query || !out) return;",
        "view.textContent = endpoint || 'not configured';",
        "function normalize(v){ return String(v || '').replace(/\\s+/g, ' ').trim().toLowerCase(); }",
        "function fallback(queryText){",
        "  const q = normalize(queryText);",
        "  const idMatch = String(queryText || '').match(/id\\s*:\\s*\\\"([^\\\"]+)\\\"/i);",
        "  const projectId = idMatch ? idMatch[1] : 'prj_abc123';",
        "  if (q.indexOf('health') !== -1) return { data: { health: { status: 'healthy', version: '1.0.0' } } };",
        "  if (q.indexOf('mutation') !== -1 && q.indexOf('createproject') !== -1) return { data: { createProject: { id: 'prj_demo001', name: 'New Project', status: 'draft' } } };",
        "  if (q.indexOf('mutation') !== -1 && q.indexOf('updateproject') !== -1) return { data: { updateProject: { id: projectId, status: 'active', updatedAt: new Date().toISOString() } } };",
        "  if (q.indexOf('projects') !== -1) return { data: { projects: [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }] } };",
        "  if (q.indexOf('project') !== -1) return { data: { project: { id: projectId, name: 'Website Redesign', status: 'active' } } };",
        "  return { data: null, errors: [{ message: 'Unknown query. Use: health, project, projects, createProject, updateProject' }] };",
        "}",
        "run.onclick = async function(){",
        "  if (!endpoint) {",
        "    out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(query.value) }, null, 2);",
        "    return;",
        "  }",
        "  out.textContent = 'Loading...';",
        "  try {",
        "    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ query: query.value }) });",
        "    const text = await response.text();",
        "    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(query.value) }, null, 2);",
        "  } catch (error) {",
        "    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(query.value) }, null, 2);",
        "  }",
        "};",
        "})();",
        "</script>",
        "<!-- vale on -->",
        "",
    ]


def _render_grpc_tester(endpoint: str) -> list[str]:
    endpoint_js = json.dumps(endpoint)
    return [
        "## Interactive gRPC Tester",
        "",
        "This tester uses an HTTP gateway/adapter endpoint, so docs users can trigger gRPC methods from browser.",
        "",
        "<!-- vale off -->",
        "<div id=\"grpc-playground\" style=\"border:1px solid #d1d5db; padding:12px; border-radius:8px;\">",
        "  <p><strong>Gateway Endpoint:</strong> <code id=\"grpc-endpoint-view\"></code></p>",
        "  <label>Service</label><br/><input id=\"grpc-service\" style=\"width:100%\" placeholder=\"GreeterService\"/><br/>",
        "  <label>Method</label><br/><input id=\"grpc-method\" style=\"width:100%\" placeholder=\"SayHello\"/><br/>",
        "  <label>Payload (JSON)</label><br/><textarea id=\"grpc-payload\" rows=\"8\" style=\"width:100%; font-family:monospace;\">{\n  \"name\": \"world\"\n}</textarea><br/>",
        "  <button id=\"grpc-run\">Invoke</button>",
        "  <pre id=\"grpc-output\" style=\"margin-top:12px; max-height:320px; overflow:auto;\"></pre>",
        "</div>",
        "<script>",
        f"(function(){{ const endpoint = {endpoint_js};",
        "const view = document.getElementById('grpc-endpoint-view');",
        "const run = document.getElementById('grpc-run');",
        "const service = document.getElementById('grpc-service');",
        "const method = document.getElementById('grpc-method');",
        "const payload = document.getElementById('grpc-payload');",
        "const out = document.getElementById('grpc-output');",
        "if (!view || !run || !service || !method || !payload || !out) return;",
        "view.textContent = endpoint || 'not configured';",
        "function fallback(body){",
        "  const m = String((body && body.method) || '').toLowerCase();",
        "  const p = (body && body.payload && typeof body.payload === 'object') ? body.payload : {};",
        "  if (m === 'getproject') return { id: p.project_id || 'prj_abc123', name: 'Website Redesign', status: 'active' };",
        "  if (m === 'createproject') return { id: 'prj_demo001', name: p.name || 'New Project', status: p.status || 'draft' };",
        "  if (m === 'listprojects') return [{ id: 'prj_abc123', status: 'active' }, { id: 'prj_def456', status: 'draft' }];",
        "  return { error: { code: 'UNIMPLEMENTED', message: 'Use GetProject, CreateProject, or ListProjects' } };",
        "}",
        "run.onclick = async function(){",
        "  try {",
        "    const body = { service: service.value.trim(), method: method.value.trim(), payload: JSON.parse(payload.value || '{}') };",
        "    if (!endpoint) {",
        "      out.textContent = JSON.stringify({ mode: 'semantic-fallback', simulated_response: fallback(body) }, null, 2);",
        "      return;",
        "    }",
        "    out.textContent = 'Loading...';",
        "    const response = await fetch(endpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });",
        "    const text = await response.text();",
        "    out.textContent = JSON.stringify({ mode: 'live', raw: text, simulated_response: fallback(body) }, null, 2);",
        "  } catch (error) {",
        "    let body = { method: method.value.trim(), payload: {} };",
        "    try { body.payload = JSON.parse(payload.value || '{}'); } catch (_) {}",
        "    out.textContent = JSON.stringify({ mode: 'semantic-fallback', error: String(error), simulated_response: fallback(body) }, null, 2);",
        "  }",
        "};",
        "})();",
        "</script>",
        "<!-- vale on -->",
        "",
    ]


def _render_asyncapi_tester(ws_endpoint: str, http_endpoint: str) -> list[str]:
    ws_js = json.dumps(ws_endpoint)
    http_js = json.dumps(http_endpoint)
    return [
        "## Interactive AsyncAPI Tester",
        "",
        "> Sandbox semantic mode: this tester returns event-aware responses by `event_type` and payload fields.",
        "",
        "<!-- vale off -->",
        "<div id=\"asyncapi-playground\" style=\"border:1px solid #d1d5db; padding:12px; border-radius:8px;\">",
        "  <p><strong>WebSocket Endpoint:</strong> <code id=\"asyncapi-ws-view\"></code></p>",
        "  <p><strong>HTTP Publish Endpoint:</strong> <code id=\"asyncapi-http-view\"></code></p>",
        "  <textarea id=\"asyncapi-message\" rows=\"8\" style=\"width:100%; font-family:monospace;\">{\n  \"event_type\": \"project.updated\",\n  \"event_id\": \"evt_001\",\n  \"data\": {\"project_id\": \"prj_abc123\", \"status\": \"active\"}\n}</textarea><br/>",
        "  <button id=\"asyncapi-send-ws\">Send via WebSocket</button>",
        "  <button id=\"asyncapi-send-http\">Send via HTTP</button>",
        "  <pre id=\"asyncapi-output\" style=\"margin-top:12px; max-height:320px; overflow:auto;\"></pre>",
        "</div>",
        "<script>",
        f"(function(){{ const wsEndpoint = {ws_js}; const httpEndpoint = {http_js};",
        "const wsView = document.getElementById('asyncapi-ws-view');",
        "const httpView = document.getElementById('asyncapi-http-view');",
        "const sendWs = document.getElementById('asyncapi-send-ws');",
        "const sendHttp = document.getElementById('asyncapi-send-http');",
        "const msg = document.getElementById('asyncapi-message');",
        "const out = document.getElementById('asyncapi-output');",
        "if (!wsView || !httpView || !sendWs || !sendHttp || !msg || !out) return;",
        "wsView.textContent = wsEndpoint || 'not configured';",
        "httpView.textContent = httpEndpoint || 'not configured';",
        "function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }",
        "function semanticEvent(input){",
        "  const req = parseJson(input);",
        "  const eventType = String(req.event_type || req.type || req.event || '').toLowerCase();",
        "  const data = (req.data && typeof req.data === 'object') ? req.data : {};",
        "  const eventId = req.event_id || ('evt_' + Math.random().toString(36).slice(2, 10));",
        "  const projectId = String(data.project_id || 'prj_abc123');",
        "  const occurredAt = req.occurred_at || new Date().toISOString();",
        "  if (eventType === 'project.created') return { event_id: eventId, event_type: 'project.created', occurred_at: occurredAt, data: { project_id: projectId, name: data.name || 'New Project', status: data.status || 'draft' } };",
        "  if (eventType === 'project.updated') return { event_id: eventId, event_type: 'project.updated', occurred_at: occurredAt, data: { project_id: projectId, status: data.status || 'active', changed_fields: data.changed_fields || ['status'] } };",
        "  if (eventType === 'task.completed') return { event_id: eventId, event_type: 'task.completed', occurred_at: occurredAt, data: { task_id: data.task_id || 'tsk_123', project_id: projectId, completed_by: data.completed_by || 'usr_demo' } };",
        "  return { event_id: eventId, event_type: eventType || 'custom.event', occurred_at: occurredAt, data: Object.assign({ project_id: projectId, status: 'accepted' }, data), hint: 'Use: project.created, project.updated, task.completed' };",
        "}",
        "sendWs.onclick = function(){",
        "  if (!wsEndpoint) { out.textContent = 'WebSocket endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_ws_endpoint)'; return; }",
        "  try {",
        "    const socket = new WebSocket(wsEndpoint);",
        "    let received = false;",
        "    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'sent over websocket'; };",
        "    socket.onmessage = function(e){",
        "      received = true;",
        "      const semantic = semanticEvent(e.data);",
        "      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: semantic }, null, 2);",
        "      socket.close();",
        "    };",
        "    socket.onerror = function(){",
        "      const semantic = semanticEvent(msg.value);",
        "      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: semantic }, null, 2);",
        "    };",
        "    setTimeout(function(){",
        "      if (!received) {",
        "        const semantic = semanticEvent(msg.value);",
        "        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: semantic }, null, 2);",
        "        try { socket.close(); } catch (_) {}",
        "      }",
        "    }, 1500);",
        "  } catch (error) { out.textContent = String(error); }",
        "};",
        "sendHttp.onclick = async function(){",
        "  if (!httpEndpoint) { out.textContent = 'HTTP publish endpoint is not configured (runtime.api_protocol_settings.asyncapi.asyncapi_http_publish_endpoint)'; return; }",
        "  out.textContent = 'Loading...';",
        "  try {",
        "    const body = JSON.parse(msg.value || '{}');",
        "    const response = await fetch(httpEndpoint, { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify(body) });",
        "    const text = await response.text();",
        "    const semantic = semanticEvent(body);",
        "    out.textContent = JSON.stringify({ mode: 'http-plus-semantic', raw: text, simulated_response: semantic }, null, 2);",
        "  } catch (error) {",
        "    const semantic = semanticEvent(msg.value);",
        "    out.textContent = JSON.stringify({ mode: 'http-semantic-fallback', error: String(error), simulated_response: semantic }, null, 2);",
        "  }",
        "};",
        "})();",
        "</script>",
        "<!-- vale on -->",
        "",
    ]


def _render_websocket_tester(ws_endpoint: str) -> list[str]:
    ws_js = json.dumps(ws_endpoint)
    return [
        "## Interactive WebSocket Tester",
        "",
        "> Sandbox semantic mode: this tester returns protocol-aware responses based on message type/action.",
        "",
        "<!-- vale off -->",
        "<div id=\"websocket-playground\" style=\"border:1px solid #d1d5db; padding:12px; border-radius:8px;\">",
        "  <p><strong>Endpoint:</strong> <code id=\"websocket-endpoint-view\"></code></p>",
        "  <textarea id=\"websocket-message\" rows=\"8\" style=\"width:100%; font-family:monospace;\">{\n  \"type\": \"subscribe\",\n  \"request_id\": \"req_001\",\n  \"payload\": {\"channel\": \"project.updated\", \"filters\": {\"project_id\": \"prj_abc123\"}}\n}</textarea><br/>",
        "  <button id=\"websocket-send\">Connect + Send</button>",
        "  <pre id=\"websocket-output\" style=\"margin-top:12px; max-height:320px; overflow:auto;\"></pre>",
        "</div>",
        "<script>",
        f"(function(){{ const endpoint = {ws_js};",
        "const view = document.getElementById('websocket-endpoint-view');",
        "const send = document.getElementById('websocket-send');",
        "const msg = document.getElementById('websocket-message');",
        "const out = document.getElementById('websocket-output');",
        "if (!view || !send || !msg || !out) return;",
        "view.textContent = endpoint || 'not configured';",
        "function parseJson(raw){ try { return JSON.parse(String(raw || '{}')); } catch (_) { return { raw: String(raw || '') }; } }",
        "function semanticResponse(input){",
        "  const req = parseJson(input);",
        "  const payload = (req && req.payload && typeof req.payload === 'object') ? req.payload : {};",
        "  const type = String(req.type || req.action || '').toLowerCase();",
        "  const requestId = req.request_id || ('req_' + Date.now());",
        "  const channel = String(payload.channel || payload.topic || 'project.updated');",
        "  const projectId = String((payload.filters && payload.filters.project_id) || payload.project_id || 'prj_abc123');",
        "  if (type === 'ping') return { type: 'pong', request_id: requestId, payload: { ts: new Date().toISOString() } };",
        "  if (type === 'subscribe') return { type: 'ack', request_id: requestId, payload: { status: 'subscribed', channel: channel, filters: payload.filters || {} } };",
        "  if (type === 'unsubscribe') return { type: 'ack', request_id: requestId, payload: { status: 'unsubscribed', channel: channel } };",
        "  if (type === 'publish') return { type: 'event', request_id: requestId, payload: { event_type: channel, data: Object.assign({ project_id: projectId, status: 'active' }, (payload.data && typeof payload.data === 'object') ? payload.data : {}) } };",
        "  if (type === 'get_project' || type === 'project.get' || type === 'query') return { type: 'event', request_id: requestId, payload: { event_type: 'project.snapshot', data: { project_id: projectId, name: 'Website Redesign', status: 'active', updated_at: new Date().toISOString() } } };",
        "  if (type === 'list_projects' || type === 'project.list') return { type: 'event', request_id: requestId, payload: { event_type: 'project.list', data: [{ project_id: 'prj_abc123', status: 'active' }, { project_id: 'prj_def456', status: 'draft' }] } };",
        "  return { type: 'ack', request_id: requestId, payload: { status: 'accepted', echo: req, hint: 'Use: ping, subscribe, unsubscribe, publish, get_project, list_projects' } };",
        "}",
        "send.onclick = function(){",
        "  if (!endpoint) { out.textContent = 'Endpoint is not configured in runtime.api_protocol_settings.websocket.websocket_endpoint'; return; }",
        "  try {",
        "    const socket = new WebSocket(endpoint);",
        "    let received = false;",
        "    socket.onopen = function(){ socket.send(msg.value); out.textContent = 'message sent'; };",
        "    socket.onmessage = function(e){",
        "      received = true;",
        "      const simulated = semanticResponse(e.data);",
        "      out.textContent = JSON.stringify({ mode: 'live-echo-plus-semantic', raw: String(e.data || ''), simulated_response: simulated }, null, 2);",
        "      socket.close();",
        "    };",
        "    socket.onerror = function(){",
        "      const simulated = semanticResponse(msg.value);",
        "      out.textContent = JSON.stringify({ mode: 'offline-semantic-fallback', simulated_response: simulated }, null, 2);",
        "    };",
        "    setTimeout(function(){",
        "      if (!received) {",
        "        const simulated = semanticResponse(msg.value);",
        "        out.textContent = JSON.stringify({ mode: 'timeout-semantic-fallback', simulated_response: simulated }, null, 2);",
        "        try { socket.close(); } catch (_) {}",
        "      }",
        "    }, 1500);",
        "  } catch (error) { out.textContent = String(error); }",
        "};",
        "})();",
        "</script>",
        "<!-- vale on -->",
        "",
    ]


def _relative_docs_index_link(output_path: Path) -> str:
    output_parent = output_path.resolve().parent
    for base in [output_parent, *output_parent.parents]:
        if base.name != "docs":
            continue
        target = base / "index.md"
        try:
            rel = target.relative_to(output_parent)
            rel_str = rel.as_posix()
        except ValueError:
            rel_str = ""
        if not rel_str:
            rel_str = str(Path(*([".."] * len(output_parent.relative_to(base).parts)), "index.md").as_posix())
        return rel_str or "index.md"
    return "../index.md"


def _render_summary(
    protocol: str,
    source_path: Path,
    payload: Any,
    *,
    mode: str,
    endpoint: str,
    ws_endpoint: str,
    http_endpoint: str,
    index_link: str,
) -> str:
    title = f"{protocol.upper()} API Reference"
    lines = [
        "---",
        f'title: "{title}"',
        f'description: "Auto-generated {protocol} reference from source contract."',
        "content_type: reference",
        "product: both",
        "---",
        "",
        f"# {protocol.upper()} Reference",
        "",
        f"Source: `{source_path.as_posix()}`",
        "",
        f"Flow mode: `{mode}`",
        "",
    ]

    if isinstance(payload, dict):
        keys = sorted(payload.keys())
        lines.append("## Top-level Keys")
        lines.append("")
        for key in keys[:50]:
            lines.append(f"- `{key}`")
        lines.append("")

    if protocol == "graphql":
        schema_text = payload if isinstance(payload, str) else ""
        query_ops = _extract_graphql_ops(schema_text, "Query")
        mutation_ops = _extract_graphql_ops(schema_text, "Mutation")
        subscription_ops = _extract_graphql_ops(schema_text, "Subscription")
        lines.append("## Operations")
        lines.append("")
        lines.append(f"- Query count: `{len(query_ops)}`")
        lines.append(f"- Mutation count: `{len(mutation_ops)}`")
        lines.append(f"- Subscription count: `{len(subscription_ops)}`")
        if query_ops:
            lines.append(f"- Queries: {', '.join(f'`{op}`' for op in query_ops[:30])}")
        if mutation_ops:
            lines.append(f"- Mutations: {', '.join(f'`{op}`' for op in mutation_ops[:30])}")
        if subscription_ops:
            lines.append(f"- Subscriptions: {', '.join(f'`{op}`' for op in subscription_ops[:30])}")
        lines.append("")
        lines.extend(_render_graphql_playground(endpoint))

    elif protocol == "grpc":
        methods = _extract_grpc_methods(source_path, payload)
        lines.append("## Service Methods")
        lines.append("")
        lines.append(f"- RPC method count: `{len(methods)}`")
        for service, method in methods[:60]:
            lines.append(f"- `{service}.{method}`")
        lines.append("")
        lines.extend(_render_grpc_tester(endpoint))

    elif protocol == "asyncapi":
        channels = _extract_async_channels(payload)
        lines.append("## Channels")
        lines.append("")
        lines.append(f"- Channel count: `{len(channels)}`")
        for channel in channels[:60]:
            lines.append(f"- `{channel}`")
        lines.append("")
        lines.extend(_render_asyncapi_tester(ws_endpoint, http_endpoint))

    elif protocol == "websocket":
        channels = _extract_websocket_channels(payload)
        lines.append("## Channels/Events")
        lines.append("")
        lines.append(f"- Channel count: `{len(channels)}`")
        for channel in channels[:60]:
            lines.append(f"- `{channel}`")
        lines.append("")
        lines.extend(_render_websocket_tester(ws_endpoint or endpoint))

    else:
        lines.append("## Notes")
        lines.append("")
        lines.append("- Generated from source contract.")
        lines.append("")

    lines.extend(
        [
            "",
            "## Next steps",
            "",
            f"- [Documentation index]({index_link})",
        ]
    )

    # Keep markdownlint MD012 clean for generated docs by collapsing
    # accidental runs of empty lines when section renderers are composed.
    collapsed: list[str] = []
    prev_blank = False
    for line in lines:
        is_blank = line.strip() == ""
        if is_blank and prev_blank:
            continue
        collapsed.append(line)
        prev_blank = is_blank

    return "\n".join(collapsed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate protocol markdown reference")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", default="api-first")
    parser.add_argument("--endpoint", default="")
    parser.add_argument("--ws-endpoint", default="")
    parser.add_argument("--http-endpoint", default="")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise FileNotFoundError(f"Source not found: {source}")

    payload = _load_source(source) if source.is_file() else {}
    ws_endpoint = str(args.ws_endpoint).strip()
    if args.protocol == "asyncapi" and not ws_endpoint:
        ws_endpoint = default_asyncapi_ws_endpoint()
    if args.protocol == "websocket" and not ws_endpoint:
        ws_endpoint = default_websocket_endpoint()

    rendered = _render_summary(
        args.protocol,
        source,
        payload,
        mode=str(args.mode).strip().lower() or "api-first",
        endpoint=str(args.endpoint).strip(),
        ws_endpoint=ws_endpoint,
        http_endpoint=str(args.http_endpoint).strip(),
        index_link=_relative_docs_index_link(Path(args.output)),
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    print(f"[protocol-docs] generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
