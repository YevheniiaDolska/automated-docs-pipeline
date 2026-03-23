"""VeriDoc pipeline API endpoints.

Exposes REST endpoints for:
- Running documentation pipelines (with protocol and integration params)
- RAG-based test generation
- Algolia search widget generation
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Ensure scripts/ is importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
_scripts_dir = str(REPO_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class RunPipelineRequest(BaseModel):
    """Request body for the main pipeline run endpoint."""

    repo_path: str
    doc_scope: str = "standard"
    protocols: list[str] | None = Field(
        default=None,
        description=(
            "API protocols to process: rest, graphql, grpc, asyncapi, websocket"
        ),
    )
    api_protocols: list[str] | None = Field(
        default=None,
        description="Alias for protocols (frontend compat)",
    )
    algolia_enabled: bool | None = None
    algolia_config: dict[str, Any] | None = None
    sandbox_backend: str | None = Field(
        default=None,
        description="Sandbox backend: external, docker, or prism",
    )


class RunPipelineResponse(BaseModel):
    status: str
    message: str
    artifacts: list[str] = Field(default_factory=list)


class RagTestRequest(BaseModel):
    """Request body for RAG test generation."""

    repo_path: str = Field(description="Path to the repository root")
    test_dir: str = Field(
        default="tests",
        description="Subdirectory containing existing tests to index",
    )
    description: str = Field(
        description="Natural-language description of what to test",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter: test, step, fixture, helper",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of similar examples to retrieve",
    )


class RagTestResponse(BaseModel):
    status: str
    generated_test: dict[str, Any] | None = None
    index_stats: dict[str, Any] | None = None
    error: str | None = None


class RagTestIndexRequest(BaseModel):
    """Request body for RAG test index building."""

    repo_path: str
    test_dir: str = "tests"


class RagTestIndexResponse(BaseModel):
    status: str
    stats: dict[str, Any] | None = None
    error: str | None = None


class AlgoliaWidgetRequest(BaseModel):
    """Request body for Algolia widget generation."""

    generator: str = Field(
        description="Site generator: mkdocs, docusaurus, hugo, vitepress, custom",
    )
    app_id: str = Field(description="Algolia Application ID")
    search_key: str = Field(description="Algolia search-only API key")
    index_name: str = Field(description="Algolia index name")
    output_dir: str = Field(
        default=".",
        description="Output directory for generated widget files",
    )


class AlgoliaWidgetResponse(BaseModel):
    status: str
    files_generated: list[str] = Field(default_factory=list)
    error: str | None = None


class DocCompilerRequest(BaseModel):
    """Request body for the doc compiler endpoint."""

    repo_path: str = Field(description="Path to the repository root")
    modalities: str = Field(
        default="all",
        description=(
            "Comma-separated modalities: executive_briefing, "
            "cross_doc_consistency, auto_faq, architecture_diagram, "
            "doc_critique, or 'all'"
        ),
    )
    generate_faq_doc: bool = Field(
        default=False,
        description="Generate a FAQ markdown file in docs/",
    )


class DocCompilerResponse(BaseModel):
    status: str
    modalities_run: list[str] = Field(default_factory=list)
    report: dict[str, Any] | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Feature gate helper
# ---------------------------------------------------------------------------


def _check_feature_gate(tier: str, feature: str) -> dict[str, Any] | None:
    """Return an error dict if the feature is not available, else None."""
    try:
        from gitspeak_core.config.pricing import has_feature
    except ImportError:
        # Fallback: import from this package
        from packages.core.gitspeak_core.config.pricing import has_feature

    if not has_feature(tier, feature):
        return {
            "status": "error",
            "error": (
                f"Feature '{feature}' requires a plan upgrade. "
                f"Current tier: {tier}"
            ),
            "status_code": 402,
        }
    return None


# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------


def handle_run_pipeline(
    request: RunPipelineRequest,
    user_tier: str = "free",
) -> RunPipelineResponse:
    """Run the documentation pipeline with protocol and integration params."""
    # Merge protocol fields (frontend sends api_protocols, backend uses protocols)
    protocols = request.protocols or request.api_protocols or []

    artifacts: list[str] = []
    messages: list[str] = []

    if protocols:
        messages.append(f"Protocols: {', '.join(protocols)}")
    if request.algolia_enabled:
        messages.append("Algolia search enabled")
    if request.sandbox_backend:
        messages.append(f"Sandbox: {request.sandbox_backend}")

    # Auto-run doc compiler if tier supports it (non-blocking)
    if not _check_feature_gate(user_tier, "doc_compiler"):
        try:
            from compile_doc_overview import ALL_MODALITIES, run_doc_compiler

            repo = Path(request.repo_path)
            result = run_doc_compiler(
                docs_dir=repo / "docs",
                reports_dir=repo / "reports",
                glossary_path=repo / "glossary.yml",
                modalities=list(ALL_MODALITIES),
            )
            artifacts.append(str(repo / "reports" / "doc_compiler_report.json"))
            messages.append("Docs health reports generated")
        except Exception:
            pass  # Non-blocking: doc compiler failure never blocks pipeline

    return RunPipelineResponse(
        status="ok",
        message="; ".join(messages) if messages else "Pipeline queued",
        artifacts=artifacts,
    )


def handle_rag_test_generate(
    request: RagTestRequest,
    user_tier: str = "free",
) -> RagTestResponse:
    """Generate a test using RAG from existing test codebase."""
    gate = _check_feature_gate(user_tier, "rag_test_generation")
    if gate:
        return RagTestResponse(
            status="error",
            error=gate["error"],
        )

    try:
        from generate_tests_from_rag import (
            generate_test_from_description,
            scan_directory,
        )

        source_dir = Path(request.repo_path) / request.test_dir
        index = scan_directory(source_dir)

        result = generate_test_from_description(
            description=request.description,
            index=index,
            test_type="unit",
            framework="pytest",
            top_k=request.top_k,
        )

        return RagTestResponse(
            status="ok",
            generated_test={
                "prompt": result.prompt,
                "similar_count": len(result.similar_records),
                "target_module": result.target_module,
            },
            index_stats={
                "total_functions": index.total_functions_indexed,
                "total_files": index.total_files_scanned,
                "frameworks": index.framework_stats,
            },
        )
    except Exception as exc:
        return RagTestResponse(
            status="error",
            error=f"RAG test generation failed: {exc}",
        )


def handle_rag_test_index(
    request: RagTestIndexRequest,
    user_tier: str = "free",
) -> RagTestIndexResponse:
    """Build a RAG index from existing tests."""
    gate = _check_feature_gate(user_tier, "rag_test_generation")
    if gate:
        return RagTestIndexResponse(status="error", error=gate["error"])

    try:
        from generate_tests_from_rag import scan_directory

        source_dir = Path(request.repo_path) / request.test_dir
        index = scan_directory(source_dir)

        return RagTestIndexResponse(
            status="ok",
            stats={
                "total_functions": index.total_functions_indexed,
                "total_files": index.total_files_scanned,
                "frameworks": index.framework_stats,
            },
        )
    except Exception as exc:
        return RagTestIndexResponse(
            status="error",
            error=f"Index build failed: {exc}",
        )


def handle_algolia_widget(
    request: AlgoliaWidgetRequest,
    user_tier: str = "free",
) -> AlgoliaWidgetResponse:
    """Generate Algolia search widget files for a site generator."""
    gate = _check_feature_gate(user_tier, "algolia_search")
    if gate:
        return AlgoliaWidgetResponse(status="error", error=gate["error"])

    try:
        from generate_algolia_widget import GENERATORS, generate_widget

        if request.generator not in GENERATORS:
            return AlgoliaWidgetResponse(
                status="error",
                error=(
                    f"Unsupported generator '{request.generator}'. "
                    f"Supported: {', '.join(GENERATORS)}"
                ),
            )

        output_dir = Path(request.output_dir)
        files = generate_widget(
            generator=request.generator,
            app_id=request.app_id,
            search_key=request.search_key,
            index_name=request.index_name,
            output_dir=output_dir,
        )

        return AlgoliaWidgetResponse(
            status="ok",
            files_generated=files,
        )
    except Exception as exc:
        return AlgoliaWidgetResponse(
            status="error",
            error=f"Widget generation failed: {exc}",
        )


def handle_doc_compiler(
    request: DocCompilerRequest,
    user_tier: str = "free",
) -> DocCompilerResponse:
    """Run the doc compiler to produce overview artifacts."""
    gate = _check_feature_gate(user_tier, "doc_compiler")
    if gate:
        return DocCompilerResponse(status="error", error=gate["error"])

    try:
        from compile_doc_overview import ALL_MODALITIES, run_doc_compiler

        repo = Path(request.repo_path)
        docs_dir = repo / "docs"
        reports_dir = repo / "reports"
        glossary_path = repo / "glossary.yml"

        if request.modalities.strip().lower() == "all":
            modalities = list(ALL_MODALITIES)
        else:
            modalities = [
                m.strip()
                for m in request.modalities.split(",")
                if m.strip()
            ]

        result = run_doc_compiler(
            docs_dir=docs_dir,
            reports_dir=reports_dir,
            glossary_path=glossary_path,
            modalities=modalities,
            generate_faq_doc=request.generate_faq_doc,
        )

        return DocCompilerResponse(
            status="ok",
            modalities_run=result.get("modalities_run", []),
            report=result,
        )
    except Exception as exc:
        return DocCompilerResponse(
            status="error",
            error=f"Doc compiler failed: {exc}",
        )
