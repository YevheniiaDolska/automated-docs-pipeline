#!/usr/bin/env python3
"""Conservative fixer for broken markdown links.

Repairs only high-confidence internal docs links:
- adds `.md` or `index.md` variants when the target clearly exists
- rewrites to a unique markdown file when basename/slug match is unambiguous
- normalizes anchor fragments to existing heading slugs

Optionally repairs high-confidence external links too:
- same-host redirect targets
- same-host canonical URLs from fetched HTML pages

Ambiguous, cross-host, and unreachable links are reported for human review.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


_INLINE_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_CUSTOM_ID_RE = re.compile(r"\s*\{#([A-Za-z0-9_\-:.]+)\}\s*$")


@dataclass(frozen=True)
class LinkCandidate:
    target_path: Path
    fragment: str


@dataclass(frozen=True)
class ExternalCandidate:
    target_url: str


class _CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical_href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link" or self.canonical_href:
            return
        payload = {k.lower(): (v or "") for k, v in attrs}
        rel = payload.get("rel", "").lower()
        href = payload.get("href", "").strip()
        if "canonical" in rel and href:
            self.canonical_href = href


def _slugify_anchor(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("_", "-")
    text = re.sub(r"[^\w\s\-]", "", text)
    text = re.sub(r"[\s\-]+", "-", text)
    return text.strip("-")


def _split_code_fences(text: str) -> list[tuple[bool, str]]:
    parts: list[tuple[bool, str]] = []
    current: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            if current:
                parts.append((in_fence, "".join(current)))
                current = []
            parts.append((True, line))
            in_fence = not in_fence
            continue
        current.append(line)
    if current:
        parts.append((in_fence, "".join(current)))
    return parts


def _extract_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = defaultdict(int)
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        match = _HEADING_RE.match(line)
        if not match:
            continue
        heading_text = match.group(2).strip()
        custom_id = _CUSTOM_ID_RE.search(heading_text)
        if custom_id:
            anchors.add(custom_id.group(1).strip().lower())
            heading_text = _CUSTOM_ID_RE.sub("", heading_text).strip()
        slug = _slugify_anchor(heading_text)
        if not slug:
            continue
        idx = counts[slug]
        counts[slug] += 1
        anchors.add(slug if idx == 0 else f"{slug}-{idx}")
    return anchors


def _is_external(target: str) -> bool:
    lowered = target.strip().lower()
    return lowered.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "data:"))


def _normalize_url(value: str) -> str:
    parsed = urlparse(value.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return parsed._replace(scheme=scheme, netloc=netloc, path=path, fragment="").geturl()


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _extract_canonical_url(html_text: str, base_url: str) -> str:
    parser = _CanonicalParser()
    try:
        parser.feed(html_text)
    except Exception:
        return ""
    if not parser.canonical_href:
        return ""
    return urljoin(base_url, html.unescape(parser.canonical_href).strip())


def _probe_external_link(raw_target: str, timeout_seconds: float) -> tuple[ExternalCandidate | None, str]:
    req = Request(
        raw_target,
        headers={"User-Agent": "VeriOps-LinkFix/1.0", "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
        method="GET",
    )
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            final_url = str(resp.geturl()).strip()
            status = int(getattr(resp, "status", 200) or 200)
            content_type = str(resp.headers.get("Content-Type", "")).lower()
            body = b""
            if "text/html" in content_type:
                body = resp.read(65536)
    except HTTPError as exc:
        return None, f"http-{exc.code}"
    except (URLError, OSError, TimeoutError):
        return None, "network-error"

    if status >= 400:
        return None, f"http-{status}"

    normalized_original = _normalize_url(raw_target)
    normalized_final = _normalize_url(final_url)
    if normalized_final != normalized_original and _same_host(normalized_original, normalized_final):
        return ExternalCandidate(normalized_final), ""

    if body:
        canonical = _extract_canonical_url(body.decode("utf-8", errors="ignore"), final_url)
        if canonical:
            normalized_canonical = _normalize_url(canonical)
            if normalized_canonical != normalized_original and _same_host(normalized_original, normalized_canonical):
                return ExternalCandidate(normalized_canonical), ""

    return None, "no-high-confidence-replacement"


def _parse_target(raw_target: str) -> tuple[str, str]:
    target = raw_target.strip()
    if "#" in target:
        path_part, frag = target.split("#", 1)
        return path_part, frag.strip()
    return target, ""


def _candidate_variants(source_file: Path, docs_root: Path, raw_path: str) -> list[Path]:
    raw = raw_path.strip()
    if not raw:
        return [source_file]
    base = docs_root if raw.startswith("/") else source_file.parent
    normalized = raw.lstrip("/")
    raw_candidate = (base / normalized).resolve()
    variants = [raw_candidate]
    if raw_candidate.suffix == "":
        variants.append((base / f"{normalized}.md").resolve())
        variants.append((base / normalized / "index.md").resolve())
    elif raw_candidate.name == "index":
        variants.append((raw_candidate.parent / "index.md").resolve())
    if raw.endswith("/"):
        variants.append((base / normalized / "index.md").resolve())
    deduped: list[Path] = []
    seen: set[Path] = set()
    for item in variants:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def _build_doc_index(docs_root: Path) -> tuple[list[Path], dict[Path, set[str]], dict[str, list[Path]]]:
    docs_files = sorted(p.resolve() for p in docs_root.rglob("*.md") if p.is_file())
    anchors_by_file = {path: _extract_anchors(path) for path in docs_files}
    slug_map: dict[str, list[Path]] = defaultdict(list)
    for path in docs_files:
        rel = path.relative_to(docs_root).as_posix()
        stem = path.stem.lower()
        slug_map[stem].append(path)
        norm_stem = _slugify_anchor(stem)
        if norm_stem and path not in slug_map[norm_stem]:
            slug_map[norm_stem].append(path)
        if path.name == "index.md":
            parent_slug = _slugify_anchor(path.parent.name)
            if parent_slug:
                slug_map[parent_slug].append(path)
        rel_slug = _slugify_anchor(Path(rel).stem)
        if rel_slug and path not in slug_map[rel_slug]:
            slug_map[rel_slug].append(path)
    return docs_files, anchors_by_file, slug_map


def _resolve_candidate(
    source_file: Path,
    docs_root: Path,
    raw_target: str,
    docs_files: list[Path],
    anchors_by_file: dict[Path, set[str]],
    slug_map: dict[str, list[Path]],
) -> tuple[LinkCandidate | None, str]:
    path_part, fragment = _parse_target(raw_target)
    for candidate in _candidate_variants(source_file, docs_root, path_part):
        if candidate.exists() and candidate.is_file():
            return LinkCandidate(candidate, fragment), ""

    if path_part:
        lookup_key = _slugify_anchor(Path(path_part.rstrip("/")).name)
        candidates = [path for path in slug_map.get(lookup_key, []) if path in docs_files]
        unique_candidates = sorted(set(candidates))
        if len(unique_candidates) == 1:
            return LinkCandidate(unique_candidates[0], fragment), ""
        if len(unique_candidates) > 1:
            return None, "ambiguous-target"

    if not path_part:
        return LinkCandidate(source_file.resolve(), fragment), ""
    return None, "missing-target"


def _normalize_fragment(fragment: str, anchors: set[str]) -> tuple[str, bool]:
    if not fragment:
        return "", True
    direct = fragment.strip().lower()
    if direct in anchors:
        return direct, True
    normalized = _slugify_anchor(fragment)
    if normalized in anchors:
        return normalized, True
    return fragment, False


def fix_markdown_links(
    docs_root: Path,
    *,
    write: bool = False,
    check_external: bool = False,
    external_timeout_seconds: float = 5.0,
) -> dict[str, Any]:
    docs_root = docs_root.resolve()
    docs_files, anchors_by_file, slug_map = _build_doc_index(docs_root)
    checked_links = 0
    external_links_checked = 0
    fixed_links = 0
    unresolved_links = 0
    skipped_links = 0
    edited_files: list[str] = []
    changes: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    external_cache: dict[str, tuple[ExternalCandidate | None, str]] = {}

    for source_file in docs_files:
        original_text = source_file.read_text(encoding="utf-8")
        parts = _split_code_fences(original_text)
        changed = False
        rebuilt: list[str] = []

        for in_code_fence, chunk in parts:
            if in_code_fence:
                rebuilt.append(chunk)
                continue

            def _replace(match: re.Match[str]) -> str:
                nonlocal checked_links, external_links_checked, fixed_links, unresolved_links, skipped_links, changed
                label = match.group(1)
                raw_target = match.group(2)
                if _is_external(raw_target):
                    if not check_external:
                        skipped_links += 1
                        return match.group(0)
                    external_links_checked += 1
                    if raw_target not in external_cache:
                        external_cache[raw_target] = _probe_external_link(raw_target, external_timeout_seconds)
                    external_candidate, reason = external_cache[raw_target]
                    if external_candidate is None:
                        unresolved_links += 1
                        unresolved.append(
                            {
                                "source_file": source_file.relative_to(docs_root).as_posix(),
                                "link_text": label,
                                "target": raw_target,
                                "reason": reason or "external-unresolved",
                            }
                        )
                        return match.group(0)
                    rewritten_target = external_candidate.target_url
                    if rewritten_target == raw_target:
                        return match.group(0)
                    fixed_links += 1
                    changed = True
                    changes.append(
                        {
                            "source_file": source_file.relative_to(docs_root).as_posix(),
                            "from": raw_target,
                            "to": rewritten_target,
                        }
                    )
                    return f"[{label}]({rewritten_target})"
                path_part, _ = _parse_target(raw_target)
                if path_part.startswith("../") or path_part.startswith("./") or path_part.startswith("/") or path_part == "" or "." not in Path(path_part).name or path_part.endswith(".md"):
                    checked_links += 1
                else:
                    skipped_links += 1
                    return match.group(0)

                candidate, error = _resolve_candidate(source_file.resolve(), docs_root, raw_target, docs_files, anchors_by_file, slug_map)
                if candidate is None:
                    unresolved_links += 1
                    unresolved.append(
                        {
                            "source_file": source_file.relative_to(docs_root).as_posix(),
                            "link_text": label,
                            "target": raw_target,
                            "reason": error or "unresolved",
                        }
                    )
                    return match.group(0)

                anchors = anchors_by_file.get(candidate.target_path, set())
                fragment, fragment_ok = _normalize_fragment(candidate.fragment, anchors)
                if candidate.fragment and not fragment_ok:
                    unresolved_links += 1
                    unresolved.append(
                        {
                            "source_file": source_file.relative_to(docs_root).as_posix(),
                            "link_text": label,
                            "target": raw_target,
                            "reason": "missing-anchor",
                        }
                    )
                    return match.group(0)

                rewritten_target = _relative_link(source_file.resolve(), candidate.target_path, fragment)
                if rewritten_target == raw_target:
                    return match.group(0)

                fixed_links += 1
                changed = True
                changes.append(
                    {
                        "source_file": source_file.relative_to(docs_root).as_posix(),
                        "from": raw_target,
                        "to": rewritten_target,
                    }
                )
                return f"[{label}]({rewritten_target})"

            rebuilt.append(_INLINE_LINK_RE.sub(_replace, chunk))

        updated_text = "".join(rebuilt)
        if changed and write:
            source_file.write_text(updated_text, encoding="utf-8")
            edited_files.append(source_file.relative_to(docs_root).as_posix())

    return {
        "docs_root": docs_root.as_posix(),
        "scanned_files": len(docs_files),
        "checked_links": checked_links,
        "external_links_checked": external_links_checked,
        "fixed_links": fixed_links,
        "unresolved_links": unresolved_links,
        "skipped_links": skipped_links,
        "edited_files": edited_files,
        "changes": changes,
        "unresolved": unresolved,
    }


def _relative_link(source_file: Path, target_file: Path, fragment: str) -> str:
    if source_file.resolve() == target_file.resolve():
        path_part = ""
    else:
        path_part = Path(os.path.relpath(target_file, start=source_file.parent)).as_posix()
    if fragment:
        return f"{path_part}#{fragment}" if path_part else f"#{fragment}"
    return path_part or ""


def _write_review_reports(
    report: dict[str, Any],
    review_json_path: Path,
    review_md_path: Path,
) -> None:
    payload = {
        "docs_root": report.get("docs_root", ""),
        "unresolved_links": report.get("unresolved_links", 0),
        "items": report.get("unresolved", []),
    }
    review_json_path.parent.mkdir(parents=True, exist_ok=True)
    review_json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Link Fix Needs Review",
        "",
        f"- Unresolved links: `{int(report.get('unresolved_links', 0) or 0)}`",
        f"- Docs root: `{report.get('docs_root', '')}`",
        "",
    ]
    items = report.get("unresolved", [])
    if isinstance(items, list) and items:
        lines.extend(
            [
                "| Source file | Link text | Target | Reason |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "| {source} | {label} | `{target}` | `{reason}` |".format(
                    source=str(item.get("source_file", "")).replace("|", "\\|"),
                    label=str(item.get("link_text", "")).replace("|", "\\|"),
                    target=str(item.get("target", "")).replace("|", "\\|"),
                    reason=str(item.get("reason", "")).replace("|", "\\|"),
                )
            )
    else:
        lines.append("No unresolved links.")
    lines.append("")
    review_md_path.parent.mkdir(parents=True, exist_ok=True)
    review_md_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fix high-confidence broken markdown links")
    parser.add_argument("docs_root", nargs="?", default="docs")
    parser.add_argument("--write", action="store_true", help="Rewrite markdown files in place")
    parser.add_argument("--report", default="reports/link_fix_report.json", help="JSON report output path")
    parser.add_argument("--check-external", action="store_true", help="Probe external HTTP(S) links for same-host redirects/canonical targets")
    parser.add_argument("--external-timeout", type=float, default=5.0, help="Timeout in seconds for one external link probe")
    parser.add_argument("--review-report-json", default="reports/link_fix_needs_review.json", help="Needs-review JSON output path")
    parser.add_argument("--review-report-md", default="reports/link_fix_needs_review.md", help="Needs-review Markdown output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    docs_root = Path(args.docs_root).resolve()
    report = fix_markdown_links(
        docs_root,
        write=bool(args.write),
        check_external=bool(args.check_external),
        external_timeout_seconds=float(args.external_timeout),
    )
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    review_json_path = Path(args.review_report_json).resolve()
    review_md_path = Path(args.review_report_md).resolve()
    _write_review_reports(report, review_json_path, review_md_path)
    print(
        "[ok] link fix scan: files={} checked_links={} external_checked={} fixed={} unresolved={}".format(
            report["scanned_files"],
            report["checked_links"],
            report["external_links_checked"],
            report["fixed_links"],
            report["unresolved_links"],
        )
    )
    print(f"[ok] link fix report: {report_path}")
    if int(report.get("unresolved_links", 0) or 0) > 0:
        print(f"[notify] manual link review required: {review_md_path}")
        print(f"[notify] structured review JSON: {review_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
