from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_generate_knowledge_graph_jsonld(tmp_path: Path) -> None:
    from scripts.generate_knowledge_graph_jsonld import build_graph

    modules = [
        {
            "id": "module-a",
            "title": "Module A",
            "summary": "Summary A",
            "status": "active",
            "priority": 90,
            "intents": ["configure"],
            "audiences": ["operator"],
            "channels": ["docs"],
            "dependencies": [],
            "source_file": "knowledge_modules/module-a.yml",
        },
        {
            "id": "module-b",
            "title": "Module B",
            "summary": "Summary B",
            "status": "active",
            "priority": 80,
            "intents": ["secure"],
            "audiences": ["developer"],
            "channels": ["assistant"],
            "dependencies": ["module-a"],
            "source_file": "knowledge_modules/module-b.yml",
        },
    ]
    graph = build_graph(modules)
    assert "@graph" in graph
    module_nodes = [n for n in graph["@graph"] if n.get("@type") == "KnowledgeModule"]
    assert len(module_nodes) == 2
    dep_edges = [n for n in graph["@graph"] if n.get("@type") == "DependsOn"]
    assert len(dep_edges) == 1


def test_run_retrieval_evals_auto_dataset(tmp_path: Path) -> None:
    from scripts.run_retrieval_evals import evaluate

    index_rows = [
        {
            "id": "module-a",
            "title": "Configure webhook signing",
            "summary": "Setup HMAC validation and replay checks",
            "docs_excerpt": "Configure signature validation",
            "assistant_excerpt": "Use HMAC",
            "intents": ["configure"],
            "audiences": ["operator"],
        },
        {
            "id": "module-b",
            "title": "Secure API tokens",
            "summary": "Rotate tokens and enforce scopes",
            "docs_excerpt": "Secure token flow",
            "assistant_excerpt": "Rotate secrets",
            "intents": ["secure"],
            "audiences": ["developer"],
        },
    ]
    dataset_rows = [
        {"query": "configure webhook signing", "expected_ids": ["module-a"]},
        {"query": "secure api tokens", "expected_ids": ["module-b"]},
    ]

    report = evaluate(index_rows=index_rows, dataset_rows=dataset_rows, top_k=1)
    assert report["precision_at_k"] >= 0.5
    assert report["recall_at_k"] >= 0.5
    assert report["hallucination_rate"] <= 0.5
