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
    parser.add_argument("--retention-versions", type=int, default=60)
    parser.add_argument("--promote-version", default="")
    parser.add_argument("--rollback-to-version", default="")
    parser.add_argument("--skip-rebuild", action="store_true")
    return parser.parse_args()


def _copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(source), str(target))
    return True


def _load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (RuntimeError, ValueError, TypeError, OSError):  # noqa: BLE001
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _write_history(path: Path, history: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(history, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _prune_versions(versions_dir: Path, keep: int) -> list[str]:
    if keep <= 0:
        return []
    version_dirs = [p for p in versions_dir.iterdir() if p.is_dir()]
    version_dirs.sort(key=lambda item: item.name)
    drop = version_dirs[:-keep] if len(version_dirs) > keep else []
    removed: list[str] = []
    for path in drop:
        shutil.rmtree(path, ignore_errors=True)
        removed.append(path.name)
    return removed


def _promote_pointer(index_path: Path, manifest: dict[str, Any]) -> None:
    pointer_path = index_path.parent / "rag_promoted.json"
    pointer_path.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _manifest_for_version(version: str, version_dir: Path, index_path: Path, provider: str) -> dict[str, Any]:
    version_index = version_dir / "knowledge-retrieval-index.json"
    if not version_index.exists():
        raise FileNotFoundError(f"Version index not found: {version_index}")
    checksum = _sha256(version_index)
    return {
        "version": version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promoted_index_path": str(index_path),
        "versioned_index_path": str(version_index),
        "checksum_sha256": checksum,
        "with_embeddings": (version_dir / "retrieval.faiss").exists(),
        "embeddings_provider": provider,
        "embeddings_generated": (version_dir / "retrieval.faiss").exists(),
        "faiss_versioned": (version_dir / "retrieval.faiss").exists(),
        "faiss_metadata_versioned": (version_dir / "retrieval-metadata.json").exists(),
        "steps": ["promote_existing_version"],
    }


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
    history_path = index_path.parent / "rag_version_history.json"
    history = _load_history(history_path)
    current_manifest = index_path.parent / "rag_current.json"

    if not args.skip_rebuild:
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
    if args.with_embeddings and not args.skip_rebuild:
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

    manifest: dict[str, Any]
    if args.promote_version:
        target_dir = versions_dir / str(args.promote_version).strip()
        manifest = _manifest_for_version(str(args.promote_version).strip(), target_dir, index_path, str(args.provider))
        manifest["steps"] = steps + ["promote_version"]
        _promote_pointer(index_path, manifest)
        current_manifest.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    elif args.rollback_to_version:
        target_version = str(args.rollback_to_version).strip()
        target_dir = versions_dir / target_version
        manifest = _manifest_for_version(target_version, target_dir, index_path, str(args.provider))
        shutil.copy2(str(target_dir / "knowledge-retrieval-index.json"), str(index_path))
        if (target_dir / "retrieval.faiss").exists():
            shutil.copy2(str(target_dir / "retrieval.faiss"), str(index_path.parent / "retrieval.faiss"))
        if (target_dir / "retrieval-metadata.json").exists():
            shutil.copy2(str(target_dir / "retrieval-metadata.json"), str(index_path.parent / "retrieval-metadata.json"))
        manifest["steps"] = steps + ["rollback_to_version"]
        _promote_pointer(index_path, manifest)
        current_manifest.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    else:
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
        _promote_pointer(index_path, manifest)
        current_manifest.write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        history.append(manifest)

    removed_versions = _prune_versions(versions_dir, max(1, int(args.retention_versions)))
    if removed_versions:
        steps.append(f"retention_prune:{len(removed_versions)}")

    history = history[-200:]
    _write_history(history_path, history)

    report_path = reports_dir / "rag_reindex_report.json"
    report_payload = {
        "status": "ok",
        **manifest,
        "retention_versions": max(1, int(args.retention_versions)),
        "pruned_versions": removed_versions,
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print(f"[rag-reindex] ok: version={manifest.get('version', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
