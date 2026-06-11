#!/usr/bin/env python3
"""Build docs screenshot manifest from capture metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def _sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _normalize_doc_path(raw: str, docs_root: Path) -> str:
    text = str(raw).strip().replace("\\", "/")
    if not text:
        return ""
    if text.startswith("docs/"):
        text = text[len("docs/") :]
    candidate = docs_root / text
    if candidate.exists():
        return text
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Build screenshot manifest from capture metadata.")
    parser.add_argument("--capture-manifest", default="reports/screenshot_capture_manifest.json")
    parser.add_argument("--output-manifest", default="docs/screenshots.yml")
    parser.add_argument("--report", default="reports/screenshot_manifest_build_report.json")
    args = parser.parse_args()

    repo_root = Path.cwd()
    capture_manifest = (repo_root / args.capture_manifest).resolve()
    output_manifest = (repo_root / args.output_manifest).resolve()
    report_path = (repo_root / args.report).resolve()
    docs_root = (repo_root / "docs").resolve()

    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.parent.mkdir(parents=True, exist_ok=True)

    if not capture_manifest.exists():
        report_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "capture_manifest_not_found",
                    "capture_manifest": str(capture_manifest),
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[screenshots] skipped manifest build: {capture_manifest} not found")
        return 0

    payload = _read_json(capture_manifest)
    captures = payload.get("captures", [])
    if not isinstance(captures, list):
        raise ValueError("capture manifest must contain list field 'captures'")

    screenshots: list[dict[str, Any]] = []
    errors = 0
    for item in captures:
        if not isinstance(item, dict):
            continue
        output = str(item.get("output", "")).strip().replace("\\", "/")
        doc_path = _normalize_doc_path(str(item.get("doc_path", "")).strip(), docs_root)
        section_anchor = str(item.get("section_anchor", "")).strip()
        section_heading = str(item.get("section_heading", "")).strip()
        alt = str(item.get("alt", "")).strip()
        if not output or not doc_path:
            errors += 1
            continue
        stable_key = f"{doc_path}|{section_anchor}|{section_heading}|{output}"
        rec_id = f"shot-{_sha1_text(stable_key)[:12]}"
        rec: dict[str, Any] = {
            "id": rec_id,
            "output": output,
            "target": {
                "doc": doc_path,
            },
        }
        if section_anchor:
            rec["target"]["anchor"] = section_anchor
        if section_heading:
            rec["target"]["heading"] = section_heading
        if alt:
            rec["alt"] = alt
        screenshots.append(rec)

    output_manifest.write_text(
        yaml.safe_dump({"screenshots": screenshots}, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    report_payload = {
        "ok": errors == 0,
        "capture_manifest": str(capture_manifest),
        "output_manifest": str(output_manifest),
        "records_written": len(screenshots),
        "errors": errors,
    }
    report_path.write_text(json.dumps(report_payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"[screenshots] manifest built: {output_manifest}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

