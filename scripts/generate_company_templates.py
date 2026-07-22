#!/usr/bin/env python3
"""Plan company-specific documentation templates with an LLM, from real signals.

Given a company profile plus web research (``company_research.json``) and the
catalog of reusable knowledge modules and SDK snippets, an LLM assesses the
company's documentation needs and emits a set of template specs. Each spec carries
a complete, schema-valid frontmatter for that company and section slots that pull
content from single sources (modules, snippets, variables) -- so documents in the
client repo assemble from blocks instead of duplicating prose.

Generated specs are validated deterministically (frontmatter against
``docs-schema.yml`` + allowed tags; slot refs must point at real modules/snippets),
with a bounded repair loop that feeds errors back to the model. Valid specs are
written to ``templates/specs/`` and rendered into ``docs/`` skeletons.

External LLM use is gated by the egress policy.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml

from scripts import generate_doc_from_spec as gdfs
from scripts import validate_frontmatter as vfm
from scripts.generate_public_docs_audit import _resolve_llm_provider, _run_llm_json_prompt
from scripts.llm_egress import ensure_external_allowed, load_policy, redact_payload

_CONTENT_TYPES = ["tutorial", "how-to", "concept", "reference", "troubleshooting", "release-note"]
_PRODUCTS = ["both", "cloud", "self-hosted"]
_MAX_REPAIR_ATTEMPTS = 3


def load_module_catalog(modules_dir: Path, limit: int = 120) -> list[dict[str, Any]]:
    """Return a compact catalog of available knowledge modules for the prompt."""
    catalog: list[dict[str, Any]] = []
    for path in sorted(modules_dir.glob("*.yml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or str(payload.get("status")) != "active":
            continue
        catalog.append(
            {
                "id": str(payload.get("id", path.stem)),
                "title": str(payload.get("title", "")),
                "summary": str(payload.get("summary", ""))[:180],
                "intents": payload.get("intents", []),
            }
        )
        if len(catalog) >= limit:
            break
    return catalog


def load_snippet_refs(snippets_dir: Path) -> list[str]:
    """Return snippet refs (e.g. 'sdk/create-charge') available for slots."""
    if not snippets_dir.exists():
        return []
    refs: list[str] = []
    for path in sorted(snippets_dir.rglob("*.md")):
        ref = path.relative_to(snippets_dir).with_suffix("").as_posix()
        refs.append(ref)
    return refs


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (ValueError, OSError):
        return {}


def build_context(
    *,
    company: str,
    domain: str,
    research: dict[str, Any],
    assumptions: dict[str, Any],
    modules: list[dict[str, Any]],
    snippet_refs: list[str],
    allowed_tags: list[str],
    api_protocols: list[str],
    style_guide: str,
    glossary_terms: list[str],
) -> dict[str, Any]:
    """Assemble the compact context object sent to the planner."""
    research_digest = {
        "domain_pages": research.get("domain_pages", [])[:8],
        "sources": [
            {"title": s.get("title", ""), "url": s.get("url", ""), "snippet": s.get("snippet", "")[:200]}
            for s in research.get("sources", [])[:20]
        ],
    }
    return {
        "company": company,
        "domain": domain,
        "research": research_digest,
        "company_profile_notes": assumptions.get("provenance", []),
        "api_protocols": api_protocols,
        "style_guide": style_guide,
        "available_modules": modules,
        "available_snippets": snippet_refs,
        "allowed_tags": allowed_tags,
        "content_types": _CONTENT_TYPES,
        "products": _PRODUCTS,
        "glossary_preferred_terms": glossary_terms[:60],
    }


def build_planner_prompt(context: dict[str, Any], repair_errors: list[str] | None = None) -> str:
    parts = [
        "You are a senior documentation architect. Plan Stripe-quality documentation",
        f"templates tailored to the company '{context['company']}' based on the research below.",
        "Assess what documentation this company's developers and operators actually need",
        "(products, APIs/SDKs, protocols), then design the most useful set of templates.",
        "",
        "Return JSON only, shape:",
        '{"templates": [ {',
        '  "doc_type": "<short-kebab>",',
        '  "output_path": "docs/<section>/<slug>.md",',
        '  "frontmatter": {"title": "...", "description": "...", "content_type": "<one of content_types>",',
        '                  "product": "<one of products>", "tags": ["<subset of allowed_tags>"]},',
        '  "intro": "First-paragraph prose, <= 55 words, with a definition (is/provides/enables).",',
        '  "sections": [ {"heading": "Descriptive heading", "slots": [',
        '      {"type": "prose", "text": "..."},',
        '      {"type": "snippet", "ref": "<one of available_snippets>"},',
        '      {"type": "module", "ref": "<one of available_modules[].id>"},',
        '      {"type": "variable", "ref": "product_name"} ] } ] } ] }',
        "",
        "Stripe-quality bar (every template MUST follow):",
        "- intro is a hook: define the subject in the first sentence (is/provides/enables),",
        "  state the primary use case, set expectations. <= 55 words.",
        "- progressive disclosure: simple case first, then variations, then advanced.",
        "- include a runnable code example early via a snippet slot when one fits.",
        "- cover error/edge cases, security/auth, and 'next steps' where relevant.",
        "- descriptive headings (not 'Overview'/'Setup'); concrete facts, not vague claims.",
        "- set geo_contract: {first_paragraph_max_words: 60} on every template.",
        "",
        "Hard rules:",
        "- frontmatter.title: 8-120 chars. frontmatter.description: 20-220 chars.",
        "- content_type MUST be one of content_types; product one of products.",
        "- tags MUST be a subset of allowed_tags (do not invent tags).",
        "- module/snippet slot refs MUST be exact ids/refs from the provided catalogs.",
        "- Prefer module and snippet slots over prose to avoid duplication; use prose only",
        "  for company-specific framing.",
        "- Plan 15-20 templates covering the company's real product surface (APIs/SDKs,",
        "  protocols, onboarding, auth, errors, webhooks, migration), ordered by importance.",
        "",
        f"CONTEXT:\n{json.dumps(context, ensure_ascii=True)}",
    ]
    if repair_errors:
        parts += [
            "",
            "Your previous output failed validation. Fix ALL of these and return corrected JSON only:",
            *[f"- {e}" for e in repair_errors],
        ]
    return "\n".join(parts)


def validate_plan(
    plan: dict[str, Any],
    *,
    module_ids: set[str],
    snippet_refs: set[str],
    schema: dict[str, Any],
    allowed_tags: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate every template in the plan; return (valid_specs, all_errors)."""
    templates = plan.get("templates") if isinstance(plan, dict) else None
    if not isinstance(templates, list) or not templates:
        return [], ["plan.templates must be a non-empty list"]

    valid: list[dict[str, Any]] = []
    errors: list[str] = []
    for i, spec in enumerate(templates):
        prefix = f"templates[{i}]"
        if not isinstance(spec, dict):
            errors.append(f"{prefix}: not an object")
            continue
        fm = spec.get("frontmatter")
        spec_errors: list[str] = []
        if not isinstance(fm, dict):
            spec_errors.append(f"{prefix}.frontmatter: required object missing")
        else:
            for e in gdfs.validate_frontmatter_dict(fm, schema, allowed_tags):
                spec_errors.append(f"{prefix}.{e}")
        if not str(spec.get("output_path", "")).strip():
            spec_errors.append(f"{prefix}.output_path: required")
        for j, section in enumerate(spec.get("sections", []) or []):
            for k, slot in enumerate(section.get("slots", []) or []) if isinstance(section, dict) else []:
                sp = f"{prefix}.sections[{j}].slots[{k}]"
                stype = str(slot.get("type", "")).strip().lower() if isinstance(slot, dict) else ""
                if stype == "module" and str(slot.get("ref", "")) not in module_ids:
                    spec_errors.append(f"{sp}: module ref '{slot.get('ref')}' is not a known module id")
                elif stype == "snippet" and str(slot.get("ref", "")).removesuffix(".md") not in snippet_refs:
                    spec_errors.append(f"{sp}: snippet ref '{slot.get('ref')}' is not a known snippet")
                elif stype not in {"prose", "module", "snippet", "variable"}:
                    spec_errors.append(f"{sp}: invalid slot type '{stype}'")
        if spec_errors:
            errors.extend(spec_errors)
        else:
            valid.append(spec)
    return valid, errors


def plan_templates(
    context: dict[str, Any],
    *,
    provider: dict[str, str],
    api_key: str,
    model: str,
    timeout: int,
    module_ids: set[str],
    snippet_refs: set[str],
    schema: dict[str, Any],
    allowed_tags: set[str],
    max_attempts: int = _MAX_REPAIR_ATTEMPTS,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Call the LLM and validate/repair until specs are valid or attempts run out."""
    repair_errors: list[str] | None = None
    last_errors: list[str] = []
    for _ in range(max_attempts):
        prompt = build_planner_prompt(context, repair_errors)
        plan = _run_llm_json_prompt(
            provider=provider, api_key=api_key, model=model, timeout=timeout, prompt=prompt, max_tokens=4000
        )
        valid, errors = validate_plan(
            plan, module_ids=module_ids, snippet_refs=snippet_refs, schema=schema, allowed_tags=allowed_tags
        )
        if not errors:
            return valid, []
        last_errors = errors
        # Keep the valid ones; ask the model to fix only what failed.
        repair_errors = errors
        if valid and not any(e.startswith("plan.templates") for e in errors):
            # Partial success: return what validated rather than risk losing it.
            return valid, errors
    return [], last_errors


def write_and_render(
    specs: list[dict[str, Any]],
    *,
    specs_dir: Path,
    docs_root: Path,
    modules_dir: Path,
    schema: dict[str, Any],
    allowed_tags: set[str],
) -> list[dict[str, str]]:
    """Write spec files and render skeletons; return a manifest of outputs."""
    manifest: list[dict[str, str]] = []
    specs_dir.mkdir(parents=True, exist_ok=True)
    for i, spec in enumerate(specs):
        slug = str(spec.get("doc_type", "")).strip() or Path(str(spec.get("output_path", f"template-{i}"))).stem
        spec_path = specs_dir / f"{slug}.spec.yml"
        spec_path.write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=False), encoding="utf-8")

        rendered, errors = gdfs.build_document(
            spec, modules_dir=modules_dir, schema=schema, allowed_tags=allowed_tags
        )
        entry = {"spec": str(spec_path), "doc_type": slug}
        geo_warnings = gdfs.check_geo_contract(spec, rendered)
        if geo_warnings:
            entry["geo_warnings"] = "; ".join(geo_warnings)
        if errors:
            entry["status"] = "spec_written_render_failed"
            entry["errors"] = "; ".join(errors)
        else:
            out_rel = str(spec.get("output_path", "")).strip() or f"reference/{slug}.md"
            out_path = docs_root / out_rel if not Path(out_rel).is_absolute() else Path(out_rel)
            # output_path is docs-relative when it starts with 'docs/'
            if out_rel.startswith("docs/"):
                out_path = docs_root.parent / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")
            entry["doc"] = str(out_path)
            entry["status"] = "ok"
        manifest.append(entry)
    return manifest


def _load_glossary_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    terms = data.get("terms", {}) if isinstance(data, dict) else {}
    return list(terms.keys()) if isinstance(terms, dict) else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--company", required=True)
    parser.add_argument("--domain", default="")
    parser.add_argument("--research", default="reports/company_research.json")
    parser.add_argument("--assumptions", default="")
    parser.add_argument("--api-protocols", default="", help="Comma-separated: rest,graphql,grpc,...")
    parser.add_argument("--style-guide", default="google")
    parser.add_argument("--modules-dir", default="knowledge_modules")
    parser.add_argument("--snippets-dir", default="_snippets")
    parser.add_argument("--specs-dir", default="templates/specs")
    parser.add_argument("--docs-root", default="docs")
    parser.add_argument("--schema", default="docs-schema.yml")
    parser.add_argument("--mkdocs", default="mkdocs.yml")
    parser.add_argument("--glossary", default="glossary.yml")
    parser.add_argument("--manifest", default="reports/company_templates_manifest.json")
    parser.add_argument("--llm-provider", default="auto")
    parser.add_argument("--llm-model", default="deepseek-chat")
    parser.add_argument("--llm-api-key-env-name", default="")
    parser.add_argument("--llm-timeout", type=int, default=120)
    parser.add_argument("--runtime-config", default="docsops/config/client_runtime.yml")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--external-approve-once", action="store_true")
    parser.add_argument("--external-approve-for-run", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    provider = _resolve_llm_provider(args.llm_provider, args.llm_model, api_key_env_override=args.llm_api_key_env_name)
    api_key = os.environ.get(provider["api_key_env"], "").strip()
    if not api_key:
        print(f"[skipped] missing {provider['api_key_env']} for provider {provider['name']}")
        return 2

    policy = load_policy(Path(args.runtime_config))
    approved = ensure_external_allowed(
        policy=policy,
        step="company_template_planning",
        reports_dir=Path(args.reports_dir),
        approve_once=bool(args.external_approve_once),
        approve_for_run=bool(args.external_approve_for_run),
        non_interactive=not bool(args.interactive),
    )
    if not approved:
        print("[blocked] company_template_planning blocked by egress policy/approval gate.")
        return 3

    modules = load_module_catalog(Path(args.modules_dir))
    module_ids = {m["id"] for m in modules}
    snippet_refs = load_snippet_refs(Path(args.snippets_dir))
    allowed_tags = gdfs.load_allowed_tags(Path(args.mkdocs))
    schema = vfm.load_schema(args.schema)
    protocols = [p.strip() for p in str(args.api_protocols).split(",") if p.strip()]
    research = _read_json(Path(args.research))
    assumptions = _read_json(Path(args.assumptions)) if args.assumptions else {}
    glossary_terms = _load_glossary_terms(Path(args.glossary))

    context = build_context(
        company=args.company, domain=args.domain, research=research, assumptions=assumptions,
        modules=modules, snippet_refs=snippet_refs, allowed_tags=sorted(allowed_tags),
        api_protocols=protocols, style_guide=args.style_guide, glossary_terms=glossary_terms,
    )
    context = redact_payload(context) if policy.redact_before_external else context

    specs, errors = plan_templates(
        context, provider=provider, api_key=api_key, model=args.llm_model, timeout=int(args.llm_timeout),
        module_ids=module_ids, snippet_refs=set(snippet_refs), schema=schema, allowed_tags=allowed_tags,
    )
    if not specs:
        print("[failed] no valid templates produced. Errors:")
        for e in errors[:20]:
            print(f"  - {e}")
        return 1

    manifest = write_and_render(
        specs, specs_dir=Path(args.specs_dir), docs_root=Path(args.docs_root),
        modules_dir=Path(args.modules_dir), schema=schema, allowed_tags=allowed_tags,
    )
    Path(args.manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest).write_text(json.dumps({"company": args.company, "templates": manifest}, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for m in manifest if m.get("status") == "ok")
    print(f"[ok] planned {len(specs)} template(s), {ok} rendered -> {args.specs_dir}, manifest: {args.manifest}")
    if errors:
        print(f"[warn] {len(errors)} validation issue(s) on discarded templates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
