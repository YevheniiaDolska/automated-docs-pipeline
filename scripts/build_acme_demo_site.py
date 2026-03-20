#!/usr/bin/env python3
"""Validate and build Acme MkDocs demo site from curated docs pages.

This script does not generate demo pages. It enforces a strict demo contract,
runs quality checks, generates demo-local assets, and builds MkDocs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


SCRIPT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PAGES = [
    "index.md",
    "reference/rest-api.md",
    "reference/graphql-playground.md",
    "reference/grpc-gateway.md",
    "reference/asyncapi-events.md",
    "reference/websocket-events.md",
    "guides/tutorial.md",
    "guides/how-to.md",
    "guides/concept.md",
    "guides/troubleshooting.md",
    "quality/evidence.md",
    "quality/review-manifest.md",
]
BADGE_OPTIONAL_PAGES = {"quality/review-manifest.md"}

REQUIRED_NAV_PATHS = set(REQUIRED_PAGES)
POWERED_BADGE_TEXT = "Powered by VeriDoc"
FRONTMATTER_REQUIRED_KEYS = {"title", "description", "content_type", "product", "tags"}

REQUIRED_PIPELINE_ASSETS = [
    "assets/api/openapi.yaml",
    "assets/knowledge-retrieval-index.json",
    "assets/knowledge-graph.jsonld",
    "assets/facets-index.json",
    "reference/swagger-test.html",
]

FORBIDDEN_TOKENS = ["taskstream", "blockstream-demo"]
SECRET_PATTERNS = [
    re.compile(r"\bPMAK-[A-Za-z0-9\-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
]


def _flatten_nav_paths(nav: list[Any]) -> set[str]:
    paths: set[str] = set()

    def walk(item: Any) -> None:
        if isinstance(item, str):
            paths.add(item)
            return
        if isinstance(item, list):
            for child in item:
                walk(child)
            return
        if isinstance(item, dict):
            for _, value in item.items():
                walk(value)

    walk(nav)
    return paths


def _parse_frontmatter(text: str, rel_path: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter: {rel_path}")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"Unterminated YAML frontmatter: {rel_path}")
    payload = yaml.safe_load(text[4:end]) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid frontmatter mapping: {rel_path}")
    return payload


def _read_body_without_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :]


def _validate_page_contract(output_root: Path) -> None:
    mkdocs_path = output_root / "mkdocs.yml"
    docs_dir = output_root / "docs"

    if not mkdocs_path.exists():
        raise FileNotFoundError(
            f"Missing {mkdocs_path}. Create MkDocs config with required navigation first."
        )

    mkdocs_payload = yaml.safe_load(mkdocs_path.read_text(encoding="utf-8")) or {}
    if not isinstance(mkdocs_payload, dict):
        raise ValueError(f"Invalid mkdocs.yml format: {mkdocs_path}")

    nav = mkdocs_payload.get("nav")
    if not isinstance(nav, list):
        raise ValueError("mkdocs.yml must define a nav list.")

    nav_paths = _flatten_nav_paths(nav)
    missing_nav = sorted(p for p in REQUIRED_NAV_PATHS if p not in nav_paths)
    if missing_nav:
        raise ValueError(
            "mkdocs.yml nav is missing required demo pages:\n- " + "\n- ".join(missing_nav)
        )

    missing_files: list[str] = []
    missing_badge: list[str] = []
    frontmatter_errors: list[str] = []

    for rel in REQUIRED_PAGES:
        page = docs_dir / rel
        if not page.exists():
            missing_files.append(rel)
            continue
        text = page.read_text(encoding="utf-8")
        if rel not in BADGE_OPTIONAL_PAGES and POWERED_BADGE_TEXT not in text:
            missing_badge.append(rel)
        if rel not in BADGE_OPTIONAL_PAGES:
            try:
                fm = _parse_frontmatter(text, rel)
                missing_keys = sorted(FRONTMATTER_REQUIRED_KEYS - set(fm.keys()))
                if missing_keys:
                    frontmatter_errors.append(f"{rel}: missing keys {', '.join(missing_keys)}")
            except Exception as exc:  # noqa: BLE001
                frontmatter_errors.append(f"{rel}: {exc}")

    if missing_files:
        raise FileNotFoundError(
            "Required Acme demo pages are missing:\n- " + "\n- ".join(missing_files)
        )

    if missing_badge:
        raise ValueError(
            "These pages are missing 'Powered by VeriDoc' badge text:\n- "
            + "\n- ".join(missing_badge)
        )

    if frontmatter_errors:
        raise ValueError("Frontmatter contract failed:\n- " + "\n- ".join(frontmatter_errors))


def _validate_scope(output_root: Path) -> None:
    docs_dir = output_root / "docs"
    violations: list[str] = []

    patterns = [re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE) for token in FORBIDDEN_TOKENS]
    for path in docs_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(output_root).as_posix()
        if rel == "docs/quality/review-manifest.md":
            # This file may include cross-project mentions from operational logs.
            continue
        if path.suffix.lower() not in {".md", ".yml", ".yaml", ".json", ".graphql", ".html", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in patterns:
            if pattern.search(text):
                rel = path.relative_to(output_root)
                violations.append(f"{rel}: contains forbidden token '{pattern.pattern}'")
                break

    if violations:
        raise ValueError(
            "Project scope guard failed (foreign project tokens detected):\n- "
            + "\n- ".join(violations)
        )


def _validate_no_secrets(output_root: Path) -> None:
    docs_dir = output_root / "docs"
    leaks: list[str] = []
    for path in docs_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".yml", ".yaml", ".json", ".graphql", ".html", ".js"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                leaks.append(f"{path.relative_to(output_root)}: matches {pattern.pattern}")
                break
    if leaks:
        raise ValueError("Secret-leak guard failed:\n- " + "\n- ".join(leaks))


def _validate_local_links(output_root: Path) -> None:
    docs_dir = output_root / "docs"
    problems: list[str] = []
    md_link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    iframe_re = re.compile(r"<iframe[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
    src_re = re.compile(r"\bsrc=[\"']([^\"']+)[\"']", re.IGNORECASE)

    def check_target(src_file: Path, target: str) -> None:
        if not target or target.startswith("#"):
            return
        if target.lower() in {"url", "<url>", "href"}:
            return
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            return
        clean = target.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean:
            return
        # MkDocs nested URLs make some iframe paths valid only in built HTML.
        if src_file.as_posix().endswith("docs/reference/rest-api.md") and clean == "../swagger-test.html":
            built_equivalent = src_file.parent / "swagger-test.html"
            if not built_equivalent.exists():
                problems.append(f"{src_file.relative_to(output_root)} -> {target} (missing)")
            return
        resolved = (src_file.parent / clean).resolve()
        if not resolved.exists():
            problems.append(f"{src_file.relative_to(output_root)} -> {target} (missing)")

    for page in docs_dir.rglob("*.md"):
        text = page.read_text(encoding="utf-8")
        for m in md_link_re.finditer(text):
            check_target(page, m.group(1).strip())
        for m in iframe_re.finditer(text):
            check_target(page, m.group(1).strip())

    for html in docs_dir.rglob("*.html"):
        text = html.read_text(encoding="utf-8")
        for m in src_re.finditer(text):
            check_target(html, m.group(1).strip())

    if problems:
        raise ValueError("Local link integrity failed:\n- " + "\n- ".join(problems))


def _run(cmd: list[str], cwd: Path) -> None:
    printable = " ".join(cmd)
    print(f"[acme-build] $ {printable}")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def _run_allow_fail(cmd: list[str], cwd: Path, label: str) -> int:
    printable = " ".join(cmd)
    print(f"[acme-build] $ {printable}")
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        print(f"[acme-build] warning: {label} failed with rc={completed.returncode}")
    return int(completed.returncode)


def _run_quality_stack(output_root: Path, reports_dir: Path) -> None:
    docs_dir = output_root / "docs"
    smoke_report = reports_dir / "acme_demo_smoke_report.json"
    geo_report = reports_dir / "acme_demo_geo_report.json"
    reports_dir.mkdir(parents=True, exist_ok=True)

    _run(["python3", "scripts/normalize_docs.py", "--check", str(docs_dir)], cwd=SCRIPT_ROOT)
    _run(["python3", "scripts/lint_code_snippets.py", str(docs_dir), "--strict"], cwd=SCRIPT_ROOT)
    _run(
        [
            "python3",
            "scripts/check_code_examples_smoke.py",
            "--paths",
            str(docs_dir),
            "--report",
            str(smoke_report),
            "--allow-empty",
        ],
        cwd=SCRIPT_ROOT,
    )
    _run_allow_fail(
        [
            "python3",
            "scripts/seo_geo_optimizer.py",
            str(docs_dir),
            "--output",
            str(geo_report),
        ],
        cwd=SCRIPT_ROOT,
        label="seo_geo_optimizer",
    )
    _validate_local_links(output_root)
    _validate_no_secrets(output_root)


def _compute_demo_kpi(output_root: Path, reports_dir: Path) -> dict[str, Any]:
    kpi_dir = reports_dir / "demo_scope_kpi"
    kpi_dir.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "python3",
            "scripts/generate_kpi_wall.py",
            "--docs-dir",
            str(output_root / "docs"),
            "--reports-dir",
            str(kpi_dir),
            "--stale-days",
            "180",
        ],
        cwd=SCRIPT_ROOT,
    )
    kpi_path = kpi_dir / "kpi-wall.json"
    if not kpi_path.exists():
        return {}
    try:
        payload = json.loads(kpi_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def _refresh_score_in_page(path: Path, score: int, total_docs: int, stale_docs: int, gaps: int) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    updated: list[str] = []
    quality_note = "Excellent" if score >= 95 else ("Good" if score >= 85 else "Needs improvement")
    gap_note = "No active gaps" if gaps == 0 else f"{gaps} active gaps"
    for line in lines:
        stripped = line.strip().lower()
        if stripped.startswith("| quality score |"):
            updated.append(f"| Quality score | **{score}%** | 80% | {quality_note} |")
            continue
        if stripped.startswith("| total documents |"):
            updated.append(f"| Total documents | **{total_docs}** | -- | Indexed across all protocols |")
            continue
        if stripped.startswith("| stale pages |"):
            updated.append(f"| Stale pages | **{stale_docs}** | 0 | {'No stale pages' if stale_docs == 0 else 'Review required'} |")
            continue
        if stripped.startswith("| documentation gaps |"):
            updated.append(f"| Documentation gaps | **{gaps}** | 0 | {gap_note} |")
            continue
        updated.append(line)
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _ensure_openapi(output_root: Path) -> None:
    openapi_path = output_root / "docs" / "assets" / "api" / "openapi.yaml"
    openapi_path.parent.mkdir(parents=True, exist_ok=True)
    openapi_path.write_text(
        """openapi: 3.0.3
info:
  title: Acme API
  description: API contract used by Acme demo sandbox and interactive Swagger.
  version: 1.0.0
  contact:
    name: Acme API Support
    email: support@acme.example
servers:
  - url: https://api.acme.example/v1
paths:
  /projects:
    get:
      summary: List projects
      description: Returns all projects available to the caller.
      operationId: listProjects
      tags:
        - Projects
      responses:
        '200':
          description: OK
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProjectsList'
components:
  schemas:
    Project:
      type: object
      required: [id, name, status]
      properties:
        id: { type: string }
        name: { type: string }
        status: { type: string }
    ProjectsList:
      type: object
      required: [items]
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Project'
  responses: {}
""",
        encoding="utf-8",
    )


def _ensure_swagger_html(output_root: Path) -> None:
    html_path = output_root / "docs" / "reference" / "swagger-test.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    if html_path.exists():
        text = html_path.read_text(encoding="utf-8")
        repaired = text.replace("openapi.bundled.json", "openapi.yaml")
        if repaired != text:
            html_path.write_text(repaired, encoding="utf-8")
        return
    html_path.write_text(
        """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Acme Swagger UI</title>
    <link rel=\"stylesheet\" href=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui.css\" />
  </head>
  <body>
    <div id=\"swagger-ui\"></div>
    <script src=\"https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js\"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: '../assets/api/openapi.yaml',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [SwaggerUIBundle.presets.apis],
      });
    </script>
  </body>
</html>
""",
        encoding="utf-8",
    )


def _first_paragraph(md_text: str) -> str:
    body = _read_body_without_frontmatter(md_text)
    chunks = [c.strip() for c in body.split("\n\n") if c.strip()]
    for c in chunks:
        if c.startswith("#"):
            continue
        return re.sub(r"\s+", " ", c)[:400]
    return ""


def _build_demo_rag_assets(output_root: Path) -> None:
    docs_dir = output_root / "docs"
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    retrieval_records: list[dict[str, Any]] = []
    graph_nodes: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    facets_records: list[dict[str, Any]] = []

    for rel in REQUIRED_PAGES:
        p = docs_dir / rel
        text = p.read_text(encoding="utf-8")
        fm: dict[str, Any] = {}
        try:
            fm = _parse_frontmatter(text, rel)
        except Exception:  # noqa: BLE001
            fm = {}
        title = str(fm.get("title", rel))
        tags = fm.get("tags", []) if isinstance(fm, dict) else []
        if not isinstance(tags, list):
            tags = []
        excerpt = _first_paragraph(text)
        object_id = _slug(rel.replace(".md", ""))

        retrieval_records.append(
            {
                "objectID": object_id,
                "id": object_id,
                "title": title,
                "url": rel.replace(".md", "/"),
                "tags": tags,
                "assistant_excerpt": excerpt,
                "source_file": f"demo-showcase/acme/docs/{rel}",
            }
        )

        node_id = f"urn:acme:doc:{object_id}"
        graph_nodes.append(
            {
                "@id": node_id,
                "title": title,
                "sourceFile": f"demo-showcase/acme/docs/{rel}",
                "tags": tags,
                "url": rel.replace(".md", "/"),
            }
        )

        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        for link in links:
            if not link.endswith(".md"):
                continue
            target = str(Path(rel).parent.joinpath(link).resolve().as_posix())
            # normalize path from docs root
            if "/docs/" in target:
                target_rel = target.split("/docs/", 1)[1]
            else:
                target_rel = link
            target_id = f"urn:acme:doc:{_slug(target_rel.replace('.md', ''))}"
            graph_edges.append({"from": node_id, "to": target_id, "type": "links_to"})

        facets_records.append(
            {
                "title": title,
                "url": rel.replace(".md", "/"),
                "content_type": fm.get("content_type", "reference"),
                "tags": tags,
                "product": fm.get("product", "both") if isinstance(fm, dict) else "both",
            }
        )

    (assets_dir / "knowledge-retrieval-index.json").write_text(
        json.dumps({"records": retrieval_records}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (assets_dir / "knowledge-graph.jsonld").write_text(
        json.dumps({"nodes": graph_nodes, "edges": graph_edges}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (assets_dir / "facets-index.json").write_text(
        json.dumps({"records": facets_records}, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "doc"


def _generate_embeddings_if_available(output_root: Path) -> None:
    """Generate FAISS embeddings if OPENAI_API_KEY is set. Optional step."""
    import os

    if not os.getenv("OPENAI_API_KEY", "").strip():
        print("[acme-build] Skipping embedding generation (OPENAI_API_KEY not set)")
        return
    assets_dir = output_root / "docs" / "assets"
    index_file = assets_dir / "knowledge-retrieval-index.json"
    if not index_file.exists():
        return
    embed_script = SCRIPT_ROOT / "scripts" / "generate_embeddings.py"
    if not embed_script.exists():
        return
    _run_allow_fail(
        [
            "python3",
            str(embed_script),
            "--index",
            str(index_file),
            "--output-dir",
            str(assets_dir),
        ],
        cwd=SCRIPT_ROOT,
        label="generate_embeddings",
    )


def _sync_pipeline_assets(output_root: Path, reports_dir: Path) -> None:
    docs_dir = output_root / "docs"

    _ensure_openapi(output_root)
    _ensure_swagger_html(output_root)
    _build_demo_rag_assets(output_root)
    _generate_embeddings_if_available(output_root)

    review_md = reports_dir / "REVIEW_MANIFEST.md"
    if review_md.exists():
        target = docs_dir / "quality" / "review-manifest.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(review_md.read_text(encoding="utf-8"), encoding="utf-8")

    kpi = _compute_demo_kpi(output_root, reports_dir)
    if kpi:
        score = int(kpi.get("quality_score", 0) or 0)
        total_docs = int(kpi.get("total_docs", 0) or 0)
        stale_docs = int(kpi.get("stale_docs", 0) or 0)
        gaps = int(kpi.get("gap_total", 0) or 0)
        _refresh_score_in_page(docs_dir / "index.md", score, total_docs, stale_docs, gaps)
        _refresh_score_in_page(docs_dir / "quality" / "evidence.md", score, total_docs, stale_docs, gaps)


def _validate_assets_contract(output_root: Path) -> None:
    docs_dir = output_root / "docs"
    missing: list[str] = []
    for rel in REQUIRED_PIPELINE_ASSETS:
        if not (docs_dir / rel).exists():
            missing.append(rel)
    if missing:
        raise FileNotFoundError(
            "Missing required pipeline assets in demo site:\n- " + "\n- ".join(missing)
        )
    sandbox_cfg = docs_dir / "assets" / "javascripts" / "sandbox-config.js"
    if sandbox_cfg.exists():
        text = sandbox_cfg.read_text(encoding="utf-8", errors="ignore")
        required_tokens = [
            "asyncapi_ws_fallback_urls",
            "websocket_fallback_urls",
            "wss://echo.websocket.events",
        ]
        missing_tokens = [token for token in required_tokens if token not in text]
        if missing_tokens:
            raise ValueError(
                "Sandbox config is missing required failover settings:\n- "
                + "\n- ".join(missing_tokens)
            )
    ws_page = docs_dir / "reference" / "websocket-events.md"
    async_page = docs_dir / "reference" / "asyncapi-events.md"
    if ws_page.exists():
        ws_text = ws_page.read_text(encoding="utf-8", errors="ignore")
        ws_required = [
            "__ACME_SANDBOX_CONTROLLER__",
            "live-echo-plus-semantic",
            "offline-semantic-fallback",
            "simulated_response",
        ]
        ws_missing = [token for token in ws_required if token not in ws_text]
        if ws_missing:
            raise ValueError(
                "WebSocket demo page is missing semantic response contract tokens:\n- "
                + "\n- ".join(ws_missing)
            )
    if async_page.exists():
        async_text = async_page.read_text(encoding="utf-8", errors="ignore")
        async_required = [
            "__ACME_SANDBOX_CONTROLLER__",
            "live-echo-plus-semantic",
            "offline-semantic-fallback",
            "simulated_response",
            "project.updated",
            "task.completed",
        ]
        async_missing = [token for token in async_required if token not in async_text]
        if async_missing:
            raise ValueError(
                "AsyncAPI demo page is missing semantic response contract tokens:\n- "
                + "\n- ".join(async_missing)
            )


def _validate_built_site_contract(output_root: Path) -> None:
    site_root = output_root / "site"
    rest_html = site_root / "reference" / "rest-api" / "index.html"
    swagger_html = site_root / "reference" / "swagger-test.html"
    if not rest_html.exists():
        raise FileNotFoundError(f"Missing built REST page: {rest_html}")
    if not swagger_html.exists():
        raise FileNotFoundError(f"Missing built Swagger page: {swagger_html}")

    rest_text = rest_html.read_text(encoding="utf-8", errors="ignore")
    if "../swagger-test.html" not in rest_text:
        raise ValueError(
            "Built REST page is not linked to swagger-test with ../swagger-test.html; "
            "this causes runtime 404 in iframe."
        )

    # Ensure copy-to-clipboard feature is configured and clipboard runtime exists.
    if '"content.code.copy"' not in rest_text:
        raise ValueError(
            "Built REST page is missing content.code.copy feature in MkDocs config payload."
        )
    clipboard_runtime = site_root / "assets" / "javascripts"
    has_clipboard_runtime = any("clipboard.js" in p.read_text(encoding="utf-8", errors="ignore") for p in clipboard_runtime.glob("*.js"))
    if not has_clipboard_runtime:
        raise ValueError("Clipboard runtime not found in built site assets.")


def build_demo(output_root: Path, reports_dir: Path, build_site: bool, strict_quality: bool) -> None:
    _validate_page_contract(output_root)
    _sync_pipeline_assets(output_root, reports_dir)
    _validate_assets_contract(output_root)
    _validate_scope(output_root)

    if strict_quality:
        _run_quality_stack(output_root=output_root, reports_dir=reports_dir)

    if build_site:
        _run(["mkdocs", "build", "--strict"], cwd=output_root)
        _validate_built_site_contract(output_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and build Acme API mkdocs demo site")
    parser.add_argument("--output-root", default="demo-showcase/acme")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--build", action="store_true", help="Run mkdocs build after validation")
    parser.add_argument(
        "--skip-strict-quality",
        action="store_true",
        help="Skip strict quality stack (not recommended)",
    )
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    reports_dir = Path(args.reports_dir).resolve()

    build_demo(
        output_root=output_root,
        reports_dir=reports_dir,
        build_site=args.build,
        strict_quality=not args.skip_strict_quality,
    )
    print(f"Acme demo site contract passed: {output_root}")
    if args.build:
        print(f"MkDocs build complete: {output_root / 'site' / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
