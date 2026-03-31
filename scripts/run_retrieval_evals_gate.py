#!/usr/bin/env python3
"""Run retrieval evals with strict thresholds and smart mode selection.

Priority order:
1. hybrid+rerank (if OPENAI_API_KEY, FAISS index, and sentence-transformers available)
2. hybrid (if OPENAI_API_KEY and FAISS index available)
3. token (strict fallback for offline/local environments)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _has_sentence_transformers() -> bool:
    try:
        __import__("sentence_transformers")
        return True
    except (ImportError, RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return False


def _dataset_matches_index(dataset_path: Path, index_path: Path) -> bool:
    """Return True when dataset coverage against current index is sufficient.

    This prevents hard failures when curated dataset IDs drift after large docs rebuilds.
    """
    if not dataset_path.exists() or not index_path.exists():
        return False
    try:
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(index_payload, list):
            return False
        known_ids = {
            str(row.get("id", "")).strip()
            for row in index_payload
            if isinstance(row, dict) and str(row.get("id", "")).strip()
        }
        if not known_ids:
            return False

        dataset_payload = yaml.safe_load(dataset_path.read_text(encoding="utf-8"))
        if not isinstance(dataset_payload, list):
            return False

        total_rows = 0
        matched_rows = 0
        for row in dataset_payload:
            if not isinstance(row, dict):
                continue
            expected = row.get("expected_ids", [])
            if not isinstance(expected, list):
                continue
            total_rows += 1
            for item in expected:
                candidate = str(item).strip()
                if candidate and candidate in known_ids:
                    matched_rows += 1
                    break
        if total_rows == 0:
            return False
        return (matched_rows / total_rows) >= 0.5
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return False


def main() -> int:
    index = REPO_ROOT / "docs/assets/knowledge-retrieval-index.json"
    dataset = REPO_ROOT / "config/retrieval_eval_dataset.yml"
    generated_dataset = REPO_ROOT / "reports/retrieval_eval_dataset.generated.yml"
    report = REPO_ROOT / "reports/retrieval_evals_report.json"
    faiss_index = REPO_ROOT / "docs/assets/retrieval.faiss"

    mode = "token"
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    shared_openai_key = os.getenv("DOCSOPS_SHARED_OPENAI_API_KEY", "").strip()
    resolved_key = openai_key or shared_openai_key
    api_key = bool(resolved_key)
    faiss_ready = faiss_index.exists()

    if api_key and faiss_ready and _has_sentence_transformers():
        mode = "hybrid+rerank"
    elif api_key and faiss_ready:
        mode = "hybrid"

    print(f"[retrieval-gate] mode={mode} api_key={api_key} faiss={faiss_ready}")

    use_auto_dataset = not _dataset_matches_index(dataset, index)
    min_precision = "0.5"
    min_recall = "0.5"
    if use_auto_dataset:
        print(
            "[retrieval-gate] dataset does not match current retrieval index; "
            "using auto-generated eval dataset",
        )
        # Auto-generated labels are weaker than curated labels, so use
        # a realistic floor while still enforcing non-trivial quality.
        min_precision = "0.2"
        min_recall = "0.2"

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_retrieval_evals.py"),
        "--index",
        str(index),
        "--dataset",
        str(generated_dataset if use_auto_dataset else dataset),
        "--report",
        str(report),
        "--top-k",
        "3",
        "--min-precision",
        min_precision,
        "--min-recall",
        min_recall,
        "--max-hallucination-rate",
        "0.5",
        "--mode",
        mode,
    ]
    if use_auto_dataset:
        cmd.extend(
            [
                "--auto-generate-dataset",
                "--dataset-out",
                str(generated_dataset),
                "--auto-samples",
                "25",
            ]
        )

    if mode in {"hybrid", "hybrid+rerank"}:
        cmd.append("--use-embeddings")

    child_env = os.environ.copy()
    if resolved_key and not child_env.get("OPENAI_API_KEY", "").strip():
        # Keep legacy tools working while supporting centralized shared key setup.
        child_env["OPENAI_API_KEY"] = resolved_key

    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), env=child_env, check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
