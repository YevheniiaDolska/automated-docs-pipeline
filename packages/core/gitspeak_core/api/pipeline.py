"""VeriDoc pipeline API endpoints.

Exposes REST endpoints for:
- Running the 3-phase documentation pipeline (Discovery, Generation, Quality)
- Automation schedule management (CRUD)
- RAG-based test generation
- Algolia search widget generation
- Doc compiler
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

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

    model_config = ConfigDict(extra="forbid")

    repo_path: str = Field(description="Path to the repository root")
    doc_scope: str = Field(default="standard", description="Documentation scope")
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
    modules: dict[str, bool] | None = Field(
        default=None,
        description="Module toggles (override saved settings)",
    )
    flow_mode: str | None = Field(
        default=None,
        description="api-first, code-first, or hybrid",
    )


class PhaseResult(BaseModel):
    """Result of a single pipeline phase."""

    model_config = ConfigDict(extra="forbid")

    name: str
    status: str  # "ok", "error", "skipped"
    duration_seconds: float = 0.0
    error: str | None = None


class RunPipelineResponse(BaseModel):
    """Response from pipeline execution."""

    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    artifacts: list[str] = Field(default_factory=list)
    report: dict[str, Any] | None = None
    phases: list[PhaseResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class RagTestRequest(BaseModel):
    """Request body for RAG test generation."""

    model_config = ConfigDict(extra="forbid")

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
    """Response from RAG test generation."""

    model_config = ConfigDict(extra="forbid")

    status: str
    generated_test: dict[str, Any] | None = None
    index_stats: dict[str, Any] | None = None
    error: str | None = None


class RagTestIndexRequest(BaseModel):
    """Request body for RAG test index building."""

    model_config = ConfigDict(extra="forbid")

    repo_path: str
    test_dir: str = "tests"


class RagTestIndexResponse(BaseModel):
    """Response from RAG test index building."""

    model_config = ConfigDict(extra="forbid")

    status: str
    stats: dict[str, Any] | None = None
    error: str | None = None


class AlgoliaWidgetRequest(BaseModel):
    """Request body for Algolia widget generation."""

    model_config = ConfigDict(extra="forbid")

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
    """Response from Algolia widget generation."""

    model_config = ConfigDict(extra="forbid")

    status: str
    files_generated: list[str] = Field(default_factory=list)
    error: str | None = None


class DocCompilerRequest(BaseModel):
    """Request body for the doc compiler endpoint."""

    model_config = ConfigDict(extra="forbid")

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
    """Response from doc compiler."""

    model_config = ConfigDict(extra="forbid")

    status: str
    modalities_run: list[str] = Field(default_factory=list)
    report: dict[str, Any] | None = None
    error: str | None = None


# --- Automation models ---


class AutomationSchedule(BaseModel):
    """Cron-like automation schedule."""

    model_config = ConfigDict(extra="forbid")

    id: str = ""
    name: str = Field(description="Human-readable schedule name")
    cron: str = Field(
        default="0 3 * * 1",
        description="Cron expression (default: Monday 3 AM)",
    )
    enabled: bool = True
    flow_mode: str | None = None
    modules: dict[str, bool] | None = None


class AutomationListResponse(BaseModel):
    """List of automation schedules."""

    model_config = ConfigDict(extra="forbid")

    schedules: list[AutomationSchedule] = Field(default_factory=list)


class AutomationTriggerResponse(BaseModel):
    """Response from triggering an automation schedule."""

    model_config = ConfigDict(extra="forbid")

    status: str
    message: str


# ---------------------------------------------------------------------------
# Tier ordering for feature gating
# ---------------------------------------------------------------------------

TIER_ORDER = ["free", "starter", "pro", "business", "enterprise"]

# Module -> minimum tier mapping
MODULE_MIN_TIER: dict[str, str] = {
    "gap_detection": "starter",
    "drift_detection": "pro",
    "docs_contract": "pro",
    "normalization": "starter",
    "snippet_lint": "starter",
    "fact_checks": "starter",
    "multilang_examples": "pro",
    "self_checks": "starter",
    "lifecycle_management": "starter",
    "knowledge_validation": "business",
    "rag_optimization": "business",
    "ontology_graph": "business",
    "retrieval_evals": "business",
    "i18n_sync": "enterprise",
    "release_pack": "pro",
    "terminology_management": "starter",
    "kpi_sla": "pro",
    "doc_compiler": "enterprise",
    "diagram_validation": "pro",
    "test_assets_generation": "pro",
    "rag_test_generation": "pro",
    "finalize_gate": "pro",
}


def _tier_index(tier: str) -> int:
    """Return numeric index for tier comparison."""
    try:
        return TIER_ORDER.index(tier.lower())
    except ValueError:
        return 0


def _has_feature(user_tier: str, module_key: str) -> bool:
    """Check if user tier meets the minimum tier for a module."""
    min_tier = MODULE_MIN_TIER.get(module_key, "starter")
    return _tier_index(user_tier) >= _tier_index(min_tier)


# ---------------------------------------------------------------------------
# Feature gate helper (pricing-based, for non-module features)
# ---------------------------------------------------------------------------


def _check_feature_gate(tier: str, feature: str) -> dict[str, Any] | None:
    """Return an error dict if the feature is not available, else None."""
    try:
        from gitspeak_core.config.pricing import has_feature
    except ImportError:
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
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_scripts_dir(repo_path: str) -> Path:
    """Resolve the scripts directory for a repo."""
    repo = Path(repo_path)
    scripts = repo / "scripts"
    if scripts.is_dir():
        return scripts
    return REPO_ROOT / "scripts"


def _is_enabled(
    module_key: str,
    user_tier: str,
    module_overrides: dict[str, bool] | None,
) -> bool:
    """Check if a module is enabled: tier allows it AND not disabled."""
    if not _has_feature(user_tier, module_key):
        return False
    if module_overrides and module_key in module_overrides:
        return module_overrides[module_key]
    return True


def _run_script(
    script_name: str,
    args: list[str],
    repo_path: str,
    timeout: int = 300,
) -> tuple[bool, str]:
    """Run a pipeline script via subprocess. Returns (success, output)."""
    scripts_dir = _resolve_scripts_dir(repo_path)
    script_path = scripts_dir / script_name

    if not script_path.exists():
        return False, f"Script not found: {script_path}"

    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=repo_path,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Script timed out after {timeout}s: {script_name}"
    except Exception as exc:
        return False, f"Script execution failed: {exc}"


def _run_allow_fail(
    script_name: str,
    args: list[str],
    repo_path: str,
    phase_name: str,
    timeout: int = 300,
) -> PhaseResult:
    """Run a script, returning PhaseResult. Never raises."""
    start = time.monotonic()
    ok, output = _run_script(script_name, args, repo_path, timeout)
    elapsed = time.monotonic() - start
    if ok:
        return PhaseResult(
            name=phase_name, status="ok", duration_seconds=round(elapsed, 2)
        )
    return PhaseResult(
        name=phase_name,
        status="error",
        duration_seconds=round(elapsed, 2),
        error=output[:500] if output else "Unknown error",
    )


# ---------------------------------------------------------------------------
# Phase 1: Discovery
# ---------------------------------------------------------------------------


def _run_discovery(
    repo_path: str,
    user_tier: str,
    protocols: list[str],
    modules: dict[str, bool] | None,
    flow_mode: str | None,
) -> tuple[list[PhaseResult], list[str], list[str]]:
    """Run discovery phase. Returns (phases, artifacts, errors)."""
    phases: list[PhaseResult] = []
    artifacts: list[str] = []
    errors: list[str] = []
    repo = Path(repo_path)
    reports_dir = repo / "reports"

    # 1. Multi-protocol contracts (Enterprise-only, non-REST protocols)
    non_rest = [p for p in protocols if p != "rest"]
    if non_rest and _is_enabled("i18n_sync", user_tier, modules):
        # i18n_sync gate is enterprise; multi_protocol is also enterprise
        runtime_cfg = repo / "docsops" / "config" / "client_runtime.yml"
        args = [
            "--runtime-config", str(runtime_cfg),
            "--reports-dir", str(reports_dir),
        ]
        phase = _run_allow_fail(
            "run_multi_protocol_contract_flow.py",
            args, repo_path, "multi_protocol_contracts",
        )
        phases.append(phase)
        if phase.status == "error":
            errors.append(f"Multi-protocol: {phase.error}")

    # 2. Gap detection
    if _is_enabled("gap_detection", user_tier, modules):
        phase = _run_allow_fail(
            "gap_detector.py",
            ["--docs-dir", str(repo / "docs"), "--report", str(reports_dir / "doc_gaps_report.json")],
            repo_path, "gap_detection",
        )
        phases.append(phase)
        if phase.status == "ok":
            artifacts.append(str(reports_dir / "doc_gaps_report.json"))

    # 3. Docs contract check
    if _is_enabled("docs_contract", user_tier, modules):
        phase = _run_allow_fail(
            "check_docs_contract.py", [], repo_path, "docs_contract",
        )
        phases.append(phase)

    # 4. API/SDK drift detection
    if _is_enabled("drift_detection", user_tier, modules):
        phase = _run_allow_fail(
            "check_api_sdk_drift.py",
            ["--report", str(reports_dir / "api_sdk_drift_report.json")],
            repo_path, "drift_detection",
        )
        phases.append(phase)
        if phase.status == "ok":
            artifacts.append(str(reports_dir / "api_sdk_drift_report.json"))

    # 5. KPI wall
    if _is_enabled("kpi_sla", user_tier, modules):
        phase = _run_allow_fail(
            "generate_kpi_wall.py",
            ["--docs-dir", str(repo / "docs"), "--output", str(reports_dir / "kpi-wall.json")],
            repo_path, "kpi_wall",
        )
        phases.append(phase)
        if phase.status == "ok":
            artifacts.append(str(reports_dir / "kpi-wall.json"))

        # 6. SLA evaluation
        phase = _run_allow_fail(
            "evaluate_kpi_sla.py",
            ["--kpi-wall", str(reports_dir / "kpi-wall.json"),
             "--output", str(reports_dir / "kpi-sla-report.json")],
            repo_path, "sla_evaluation",
        )
        phases.append(phase)

    # 7. i18n sync (Enterprise-only)
    if _is_enabled("i18n_sync", user_tier, modules):
        phase = _run_allow_fail(
            "i18n_sync.py",
            ["--report", str(reports_dir / "i18n_sync_report.json")],
            repo_path, "i18n_sync",
        )
        phases.append(phase)

    # 8. Consolidate reports (unconditional if any discovery ran)
    phase = _run_allow_fail(
        "consolidate_reports.py",
        ["--reports-dir", str(reports_dir), "--output", str(reports_dir / "consolidated_report.json")],
        repo_path, "consolidate_reports",
    )
    phases.append(phase)
    if phase.status == "ok":
        artifacts.append(str(reports_dir / "consolidated_report.json"))
    else:
        errors.append(f"Consolidation: {phase.error}")

    return phases, artifacts, errors


# ---------------------------------------------------------------------------
# Phase 3: Quality
# ---------------------------------------------------------------------------


def _run_quality(
    repo_path: str,
    user_tier: str,
    protocols: list[str],
    modules: dict[str, bool] | None,
    algolia_enabled: bool,
) -> tuple[list[PhaseResult], list[str], list[str]]:
    """Run quality phase. Returns (phases, artifacts, errors)."""
    phases: list[PhaseResult] = []
    artifacts: list[str] = []
    errors: list[str] = []
    repo = Path(repo_path)
    reports_dir = repo / "reports"
    docs_dir = repo / "docs"

    # 9. Normalize docs
    if _is_enabled("normalization", user_tier, modules):
        phases.append(_run_allow_fail(
            "normalize_docs.py", [str(docs_dir)], repo_path, "normalize_docs",
        ))

    # 10. Code snippet lint
    if _is_enabled("snippet_lint", user_tier, modules):
        phases.append(_run_allow_fail(
            "lint_code_snippets.py", [str(docs_dir)], repo_path, "snippet_lint",
        ))

    # 11. Frontmatter validation
    if _is_enabled("fact_checks", user_tier, modules):
        phases.append(_run_allow_fail(
            "validate_frontmatter.py", [], repo_path, "frontmatter_validation",
        ))

    # 12a/12b. Multilang examples
    if _is_enabled("multilang_examples", user_tier, modules):
        phases.append(_run_allow_fail(
            "generate_multilang_tabs.py", [str(docs_dir)],
            repo_path, "multilang_tabs_generate",
        ))
        phases.append(_run_allow_fail(
            "validate_multilang_examples.py", [str(docs_dir)],
            repo_path, "multilang_tabs_validate",
        ))

    # 13. Code examples smoke test
    if _is_enabled("self_checks", user_tier, modules):
        phases.append(_run_allow_fail(
            "check_code_examples_smoke.py", [str(docs_dir)],
            repo_path, "code_examples_smoke",
        ))

    # 14. SEO/GEO optimization
    if _is_enabled("fact_checks", user_tier, modules):
        seo_args = [str(docs_dir)]
        phases.append(_run_allow_fail(
            "seo_geo_optimizer.py", seo_args, repo_path, "seo_geo_optimization",
        ))

    # 14b. Algolia SEO + upload
    if algolia_enabled and _is_enabled("fact_checks", user_tier, modules):
        phases.append(_run_allow_fail(
            "seo_geo_optimizer.py", [str(docs_dir), "--algolia"],
            repo_path, "algolia_seo",
        ))
        phases.append(_run_allow_fail(
            "upload_to_algolia.py", [], repo_path, "algolia_upload",
        ))

    # 15. Doc layers validation
    if _is_enabled("fact_checks", user_tier, modules):
        phases.append(_run_allow_fail(
            "doc_layers_validator.py", [str(docs_dir)],
            repo_path, "doc_layers_validation",
        ))

    # 16. Lifecycle management
    if _is_enabled("lifecycle_management", user_tier, modules):
        phases.append(_run_allow_fail(
            "lifecycle_manager.py", [str(docs_dir)],
            repo_path, "lifecycle_management",
        ))

    # 17. Glossary sync
    if _is_enabled("terminology_management", user_tier, modules):
        phases.append(_run_allow_fail(
            "sync_project_glossary.py",
            ["--paths", str(docs_dir), "--glossary", str(repo / "glossary.yml"),
             "--report", str(reports_dir / "glossary_sync_report.json"), "--write"],
            repo_path, "glossary_sync",
        ))

    # --- Knowledge pipeline ---

    # 18. Extract knowledge modules
    if _is_enabled("knowledge_validation", user_tier, modules):
        phases.append(_run_allow_fail(
            "extract_knowledge_modules_from_docs.py",
            ["--docs-dir", str(docs_dir), "--modules-dir", str(repo / "knowledge_modules"),
             "--report", str(reports_dir / "knowledge_auto_extract_report.json")],
            repo_path, "knowledge_extract",
        ))

    # 19. Validate knowledge modules
    if _is_enabled("knowledge_validation", user_tier, modules):
        phases.append(_run_allow_fail(
            "validate_knowledge_modules.py", [],
            repo_path, "knowledge_validate",
        ))

    # 20. Knowledge retrieval index
    if _is_enabled("rag_optimization", user_tier, modules):
        phase = _run_allow_fail(
            "generate_knowledge_retrieval_index.py", [],
            repo_path, "knowledge_retrieval_index",
        )
        phases.append(phase)
        if phase.status == "ok":
            artifacts.append(str(docs_dir / "assets" / "knowledge-retrieval-index.json"))

    # 21. Knowledge graph JSON-LD
    if _is_enabled("ontology_graph", user_tier, modules):
        phases.append(_run_allow_fail(
            "generate_knowledge_graph_jsonld.py",
            ["--modules-dir", str(repo / "knowledge_modules"),
             "--output", str(docs_dir / "assets" / "knowledge-graph.jsonld"),
             "--report", str(reports_dir / "knowledge_graph_report.json")],
            repo_path, "knowledge_graph",
        ))

    # 22. Retrieval evals
    if _is_enabled("retrieval_evals", user_tier, modules):
        phases.append(_run_allow_fail(
            "run_retrieval_evals.py",
            ["--index", str(docs_dir / "assets" / "knowledge-retrieval-index.json"),
             "--report", str(reports_dir / "retrieval_evals_report.json")],
            repo_path, "retrieval_evals",
        ))

    # --- Test generation ---

    # 23. Test assets (smart merge)
    if _is_enabled("test_assets_generation", user_tier, modules) and protocols:
        proto_str = ",".join(protocols)
        phases.append(_run_allow_fail(
            "generate_protocol_test_assets.py",
            ["--protocols", proto_str,
             "--output-dir", str(reports_dir / "api-test-assets")],
            repo_path, "test_assets_generation",
        ))

    # 24. RAG-based test generation
    if _is_enabled("rag_test_generation", user_tier, modules):
        phases.append(_run_allow_fail(
            "generate_tests_from_rag.py",
            ["--repo", repo_path],
            repo_path, "rag_test_generation",
        ))

    # --- Final reporting and gate ---

    # 25. Release docs pack
    if _is_enabled("release_pack", user_tier, modules):
        phases.append(_run_allow_fail(
            "generate_release_docs_pack.py",
            ["--docs-dir", str(docs_dir), "--output-dir", str(reports_dir)],
            repo_path, "release_docs_pack",
        ))

    # 26. Audit scorecard
    phases.append(_run_allow_fail(
        "generate_audit_scorecard.py",
        ["--reports-dir", str(reports_dir)],
        repo_path, "audit_scorecard",
    ))

    # 27. Doc compiler (Enterprise-only)
    if _is_enabled("doc_compiler", user_tier, modules):
        phase = _run_allow_fail(
            "compile_doc_overview.py",
            ["--docs-dir", str(docs_dir), "--reports-dir", str(reports_dir),
             "--glossary", str(repo / "glossary.yml")],
            repo_path, "doc_compiler",
        )
        phases.append(phase)
        if phase.status == "ok":
            artifacts.append(str(reports_dir / "doc_compiler_report.json"))

    # 28. Finalize docs gate
    if _is_enabled("finalize_gate", user_tier, modules):
        phase = _run_allow_fail(
            "finalize_docs_gate.py",
            ["--reports-dir", str(reports_dir)],
            repo_path, "finalize_gate",
        )
        phases.append(phase)
        if phase.status == "error":
            errors.append(f"Finalize gate failed: {phase.error}")

    return phases, artifacts, errors


# ---------------------------------------------------------------------------
# Endpoint handlers
# ---------------------------------------------------------------------------


def handle_run_pipeline(
    request: RunPipelineRequest,
    user_tier: str = "free",
) -> RunPipelineResponse:
    """Run the 3-phase documentation pipeline.

    Phase 1 (Discovery): gap detection, drift, KPI, consolidation.
    Phase 2 (Generation): returns consolidated report for LLM/human.
    Phase 3 (Quality): linting, knowledge pipeline, test generation, gate.
    """
    protocols = request.protocols or request.api_protocols or []
    modules = request.modules
    algolia_enabled = request.algolia_enabled or False

    all_phases: list[PhaseResult] = []
    all_artifacts: list[str] = []
    all_errors: list[str] = []

    # --- Phase 1: Discovery ---
    discovery_phases, discovery_artifacts, discovery_errors = _run_discovery(
        repo_path=request.repo_path,
        user_tier=user_tier,
        protocols=protocols,
        modules=modules,
        flow_mode=request.flow_mode,
    )
    all_phases.extend(discovery_phases)
    all_artifacts.extend(discovery_artifacts)
    all_errors.extend(discovery_errors)

    # --- Phase 2: Generation (pause point) ---
    # The consolidated report is produced. The caller (LLM or human)
    # reads it and creates/updates docs. When done, they call the
    # quality endpoint or re-run with a quality-only flag.
    # For now, we include consolidated_report in artifacts and continue
    # to Phase 3 in the same call for backward compatibility.
    all_phases.append(PhaseResult(
        name="generation_pause",
        status="ok",
        duration_seconds=0.0,
    ))

    # --- Phase 3: Quality ---
    quality_phases, quality_artifacts, quality_errors = _run_quality(
        repo_path=request.repo_path,
        user_tier=user_tier,
        protocols=protocols,
        modules=modules,
        algolia_enabled=algolia_enabled,
    )
    all_phases.extend(quality_phases)
    all_artifacts.extend(quality_artifacts)
    all_errors.extend(quality_errors)

    # Build summary
    ok_count = sum(1 for p in all_phases if p.status == "ok")
    err_count = sum(1 for p in all_phases if p.status == "error")
    skip_count = sum(1 for p in all_phases if p.status == "skipped")

    parts: list[str] = []
    if protocols:
        parts.append(f"Protocols: {', '.join(protocols)}")
    if algolia_enabled:
        parts.append("Algolia search enabled")
    if request.sandbox_backend:
        parts.append(f"Sandbox: {request.sandbox_backend}")
    parts.append(f"Phases: {ok_count} ok, {err_count} error, {skip_count} skipped")

    # Load consolidated report if available
    report: dict[str, Any] | None = None
    consolidated_path = Path(request.repo_path) / "reports" / "consolidated_report.json"
    if consolidated_path.exists():
        try:
            report = json.loads(consolidated_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to read consolidated report %s: %s",
                consolidated_path,
                exc,
            )

    return RunPipelineResponse(
        status="error" if all_errors else "ok",
        message="; ".join(parts) if parts else "Pipeline completed",
        artifacts=all_artifacts,
        report=report,
        phases=all_phases,
        errors=all_errors,
    )


# ---------------------------------------------------------------------------
# Automation endpoints
# ---------------------------------------------------------------------------

# In-memory schedule store (production uses persistent storage)
_schedules: dict[str, AutomationSchedule] = {}
_next_schedule_id = 1


def handle_list_schedules(user_tier: str = "free") -> AutomationListResponse:
    """List all automation schedules."""
    if _tier_index(user_tier) < _tier_index("pro"):
        return AutomationListResponse(schedules=[])
    return AutomationListResponse(schedules=list(_schedules.values()))


def handle_create_schedule(
    schedule: AutomationSchedule,
    user_tier: str = "free",
) -> AutomationSchedule | dict[str, Any]:
    """Create a new automation schedule. Requires Pro+."""
    global _next_schedule_id

    if _tier_index(user_tier) < _tier_index("pro"):
        return {
            "status": "error",
            "error": "Automation requires Pro plan or higher.",
            "status_code": 402,
        }

    schedule.id = f"sched_{_next_schedule_id}"
    _next_schedule_id += 1
    _schedules[schedule.id] = schedule
    return schedule


def handle_update_schedule(
    schedule_id: str,
    updates: dict[str, Any],
    user_tier: str = "free",
) -> AutomationSchedule | dict[str, Any]:
    """Update an existing automation schedule."""
    if _tier_index(user_tier) < _tier_index("pro"):
        return {
            "status": "error",
            "error": "Automation requires Pro plan or higher.",
            "status_code": 402,
        }

    if schedule_id not in _schedules:
        return {"status": "error", "error": "Schedule not found.", "status_code": 404}

    sched = _schedules[schedule_id]
    for key, val in updates.items():
        if hasattr(sched, key) and key != "id":
            setattr(sched, key, val)
    return sched


def handle_delete_schedule(
    schedule_id: str,
    user_tier: str = "free",
) -> dict[str, Any]:
    """Delete an automation schedule."""
    if _tier_index(user_tier) < _tier_index("pro"):
        return {
            "status": "error",
            "error": "Automation requires Pro plan or higher.",
            "status_code": 402,
        }

    if schedule_id not in _schedules:
        return {"status": "error", "error": "Schedule not found.", "status_code": 404}

    del _schedules[schedule_id]
    return {"status": "ok", "message": f"Schedule {schedule_id} deleted."}


def handle_trigger_schedule(
    schedule_id: str,
    user_tier: str = "free",
) -> AutomationTriggerResponse:
    """Manually trigger an automation schedule."""
    if _tier_index(user_tier) < _tier_index("pro"):
        return AutomationTriggerResponse(
            status="error", message="Automation requires Pro plan or higher."
        )

    if schedule_id not in _schedules:
        return AutomationTriggerResponse(
            status="error", message="Schedule not found."
        )

    sched = _schedules[schedule_id]
    if not sched.enabled:
        return AutomationTriggerResponse(
            status="error", message="Schedule is disabled."
        )

    return AutomationTriggerResponse(
        status="ok",
        message=f"Schedule '{sched.name}' triggered.",
    )


# ---------------------------------------------------------------------------
# Existing endpoint handlers (preserved)
# ---------------------------------------------------------------------------


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
