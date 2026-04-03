#!/usr/bin/env python3
"""RAG reindex lifecycle: rebuild, validate, version, and promote index artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _run(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed rc={completed.returncode}: {' '.join(cmd)}\n"
            f"stdout={completed.stdout[-2000:]}\nstderr={completed.stderr[-2000:]}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run versioned RAG reindex lifecycle")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--index-path", default="docs/assets/knowledge-retrieval-index.json")
    parser.add_argument("--versions-dir", default="docs/assets/rag-versions")
    parser.add_argument("--with-embeddings", action="store_true")
    parser.add_argument("--provider", default="local", choices=["local", "openai"])
    return parser.parse_args()


def _copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(source), str(target))
    return True


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    docs_dir = (repo_root / args.docs_dir).resolve()
    modules_dir = (repo_root / args.modules_dir).resolve()
    reports_dir = (repo_root / args.reports_dir).resolve()
    index_path = (repo_root / args.index_path).resolve()
    versions_dir = (repo_root / args.versions_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)
    versions_dir.mkdir(parents=True, exist_ok=True)

    py = sys.executable
    steps: list[str] = []
    started = datetime.now(timezone.utc)

    _run(
        [
            py,
            "scripts/extract_knowledge_modules_from_docs.py",
            "--docs-dir",
            str(docs_dir),
            "--modules-dir",
            str(modules_dir),
            "--report",
            str(reports_dir / "knowledge_auto_extract_report.json"),
        ],
        cwd=repo_root,
    )
    steps.append("extract_knowledge_modules")

    _run(
        [
            py,
            "scripts/validate_knowledge_modules.py",
            "--modules-dir",
            str(modules_dir),
            "--report",
            str(reports_dir / "knowledge_modules_report.json"),
        ],
        cwd=repo_root,
    )
    steps.append("validate_knowledge_modules")

    _run(
        [
            py,
            "scripts/generate_knowledge_retrieval_index.py",
            "--modules-dir",
            str(modules_dir),
            "--output",
            str(index_path),
        ],
        cwd=repo_root,
    )
    steps.append("generate_knowledge_retrieval_index")

    embeddings_generated = False
    if args.with_embeddings:
        _run(
            [
                py,
                "scripts/generate_embeddings.py",
                "--index",
                str(index_path),
                "--output-dir",
                str(index_path.parent),
                "--provider",
                str(args.provider),
            ],
            cwd=repo_root,
        )
        steps.append(f"generate_embeddings:{args.provider}")
        embeddings_generated = True

    if not index_path.exists():
        raise FileNotFoundError(f"Missing retrieval index after lifecycle: {index_path}")

    checksum = _sha256(index_path)
    version = f"{started.strftime('%Y%m%dT%H%M%SZ')}-{checksum[:12]}"
    version_dir = versions_dir / version
    version_dir.mkdir(parents=True, exist_ok=True)

    version_index = version_dir / "knowledge-retrieval-index.json"
    _copy_if_exists(index_path, version_index)

    faiss_src = index_path.parent / "retrieval.faiss"
    faiss_meta_src = index_path.parent / "retrieval-metadata.json"
    faiss_copied = _copy_if_exists(faiss_src, version_dir / "retrieval.faiss")
    faiss_meta_copied = _copy_if_exists(faiss_meta_src, version_dir / "retrieval-metadata.json")

    manifest = {
        "version": version,
        "generated_at_utc": started.isoformat(),
        "promoted_index_path": str(index_path),
        "versioned_index_path": str(version_index),
        "checksum_sha256": checksum,
        "with_embeddings": bool(args.with_embeddings),
        "embeddings_provider": str(args.provider),
        "embeddings_generated": embeddings_generated,
        "faiss_versioned": bool(faiss_copied),
        "faiss_metadata_versioned": bool(faiss_meta_copied),
        "steps": steps,
    }

    current_manifest = index_path.parent / "rag_current.json"
    current_manifest.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    history_path = index_path.parent / "rag_version_history.json"
    history: list[dict[str, Any]] = []
    if history_path.exists():
        try:
            payload = json.loads(history_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                history = [item for item in payload if isinstance(item, dict)]
        except (ValueError, TypeError):
            history = []
    history.append(manifest)
    history = history[-200:]
    history_path.write_text(json.dumps(history, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    report_path = reports_dir / "rag_reindex_report.json"
    report_path.write_text(json.dumps({"status": "ok", **manifest}, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"[rag-reindex] ok: version={version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
