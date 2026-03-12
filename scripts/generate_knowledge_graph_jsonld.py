#!/usr/bin/env python3
"""Generate a lightweight JSON-LD knowledge graph from knowledge modules."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


def _load_modules(modules_dir: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("status") == "active":
            payload["source_file"] = str(path)
            modules.append(payload)
    return modules


def _module_node(module: dict[str, Any]) -> dict[str, Any]:
    module_id = str(module.get("id", "")).strip()
    return {
        "@id": f"urn:module:{module_id}",
        "@type": "KnowledgeModule",
        "name": module.get("title", module_id),
        "description": module.get("summary", ""),
        "status": module.get("status", "active"),
        "priority": int(module.get("priority", 0) or 0),
        "intents": [str(v) for v in module.get("intents", []) if str(v).strip()],
        "audiences": [str(v) for v in module.get("audiences", []) if str(v).strip()],
        "channels": [str(v) for v in module.get("channels", []) if str(v).strip()],
        "dependsOn": [
            {"@id": f"urn:module:{dep}"}
            for dep in module.get("dependencies", [])
            if str(dep).strip()
        ],
        "sourceFile": module.get("source_file", ""),
        "lastVerified": module.get("last_verified", ""),
    }


def _concept_nodes(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    intents = sorted({str(v) for m in modules for v in m.get("intents", []) if str(v).strip()})
    audiences = sorted({str(v) for m in modules for v in m.get("audiences", []) if str(v).strip()})
    channels = sorted({str(v) for m in modules for v in m.get("channels", []) if str(v).strip()})
    nodes: list[dict[str, Any]] = []

    for value in intents:
        nodes.append({"@id": f"urn:intent:{value}", "@type": "Intent", "name": value})
    for value in audiences:
        nodes.append({"@id": f"urn:audience:{value}", "@type": "Audience", "name": value})
    for value in channels:
        nodes.append({"@id": f"urn:channel:{value}", "@type": "Channel", "name": value})
    return nodes


def _relation_edges(modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for module in modules:
        module_id = str(module.get("id", "")).strip()
        if not module_id:
            continue
        src = f"urn:module:{module_id}"
        for intent in module.get("intents", []):
            value = str(intent).strip()
            if value:
                edges.append({"@id": f"{src}#intent:{value}", "@type": "HasIntent", "source": {"@id": src}, "target": {"@id": f"urn:intent:{value}"}})
        for audience in module.get("audiences", []):
            value = str(audience).strip()
            if value:
                edges.append({"@id": f"{src}#audience:{value}", "@type": "HasAudience", "source": {"@id": src}, "target": {"@id": f"urn:audience:{value}"}})
        for channel in module.get("channels", []):
            value = str(channel).strip()
            if value:
                edges.append({"@id": f"{src}#channel:{value}", "@type": "HasChannel", "source": {"@id": src}, "target": {"@id": f"urn:channel:{value}"}})
        for dep in module.get("dependencies", []):
            value = str(dep).strip()
            if value:
                edges.append({"@id": f"{src}#dep:{value}", "@type": "DependsOn", "source": {"@id": src}, "target": {"@id": f"urn:module:{value}"}})
    return edges


def build_graph(modules: list[dict[str, Any]]) -> dict[str, Any]:
    module_nodes = [_module_node(module) for module in modules]
    concept_nodes = _concept_nodes(modules)
    relation_edges = _relation_edges(modules)
    return {
        "@context": {
            "@vocab": "https://docsops.example/schema#",
            "name": "http://schema.org/name",
            "description": "http://schema.org/description",
            "sourceFile": "https://docsops.example/schema#sourceFile",
            "status": "https://docsops.example/schema#status",
            "dependsOn": {"@id": "https://docsops.example/schema#dependsOn", "@type": "@id"},
            "source": {"@id": "https://docsops.example/schema#source", "@type": "@id"},
            "target": {"@id": "https://docsops.example/schema#target", "@type": "@id"},
        },
        "@graph": module_nodes + concept_nodes + relation_edges,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate JSON-LD knowledge graph from modules")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--output", default="docs/assets/knowledge-graph.jsonld")
    parser.add_argument("--report", default="reports/knowledge_graph_report.json")
    parser.add_argument("--min-graph-nodes", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modules = _load_modules(Path(args.modules_dir))
    graph = build_graph(modules)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    edge_count = sum(1 for node in graph["@graph"] if "source" in node and "target" in node)
    graph_nodes = len(graph["@graph"])
    min_nodes = max(int(args.min_graph_nodes), 0)
    status = "ok" if graph_nodes >= min_nodes else "breach"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "modules_count": len(modules),
        "graph_nodes": graph_nodes,
        "module_nodes": len([n for n in graph["@graph"] if n.get("@type") == "KnowledgeModule"]),
        "edge_count": edge_count,
        "output_file": str(output_path),
        "min_graph_nodes": min_nodes,
        "breach": "" if status == "ok" else f"graph_nodes={graph_nodes} < {min_nodes}",
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"Generated knowledge graph: {output_path}")
    if status != "ok":
        print(report["breach"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
