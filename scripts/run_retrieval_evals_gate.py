#!/usr/bin/env python3
"""Run retrieval evals with strict thresholds and smart mode selection.

Priority order:
1. hybrid+rerank (if OPENAI_API_KEY, FAISS index, and sentence-transformers available)
2. hybrid (if OPENAI_API_KEY and FAISS index available)
3. token (strict fallback for offline/local environments)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _has_sentence_transformers() -> bool:
    try:
        __import__("sentence_transformers")
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    index = REPO_ROOT / "docs/assets/knowledge-retrieval-index.json"
    dataset = REPO_ROOT / "config/retrieval_eval_dataset.yml"
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

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_retrieval_evals.py"),
        "--index",
        str(index),
        "--dataset",
        str(dataset),
        "--report",
        str(report),
        "--top-k",
        "3",
        "--min-precision",
        "0.5",
        "--min-recall",
        "0.5",
        "--max-hallucination-rate",
        "0.5",
        "--mode",
        mode,
    ]

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
