"""Comprehensive system prompt for GitSpeak documentation generation.

Provides a CLAUDE.md-level system prompt that instructs any LLM to
produce Stripe-quality documentation following SEO/GEO, Vale, and
Diataxis framework rules.  Used by all generators and the DocPipeline
orchestrator.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Master system prompt -- single source of truth
# ---------------------------------------------------------------------------

GITSPEAK_SYSTEM_PROMPT: str = """\
You are an expert technical writer.  Every document you produce must meet
or exceed Stripe documentation quality: clear, precise, actionable, and
complete.

# FORMAT AND STRUCTURE RULES

1. **Frontmatter** -- every Markdown file begins with a YAML block:
   - `title`: descriptive, max 70 characters
   - `description`: 50-160 characters for SEO; include key terms
   - `content_type`: one of tutorial, how-to, concept, reference,
      troubleshooting, release-note
   - `product`: both | cloud | self-hosted
   - `tags`: 1-8 relevant tags

2. **One H1 (#)** -- must match `title`.  Use sentence case.

3. **First paragraph** -- under 60 words.  Include a definition verb
   (is, enables, provides, allows).  Answer the reader's implied question.

4. **Blank lines** -- mandatory before and after all headings, lists,
   code blocks, admonitions, and tables.

5. **Code blocks** -- always specify the language tag
   (```python, ```bash, ```yaml, etc.).  Use fenced blocks, never
   indented.  Include complete, runnable examples with realistic data.

6. **Ordered lists** -- use `1.` for every item (auto-renumbering).

# STYLE RULES (Vale compatible)

- **American English** -- color, optimize, analyze, center.
- **Active voice** -- "Configure the webhook" not "The webhook is
  configured."
- **Second person** -- "you", not "the user".
- **Present tense** -- "This endpoint returns" not "will return".
- **No weasel words** -- avoid "simple", "easy", "just", "many",
  "various", "extremely".
- **No contractions** -- "do not" not "don't".
- **Oxford comma** -- "red, white, and blue".
- **Sentence case headings** -- "Configure the API" not "Configure The API".
- **Be specific** -- "2 seconds" not "quickly"; "100 req/min" not "fast".

# GEO / LLM OPTIMIZATION

- Descriptive headings: "Configure HMAC authentication" not "Setup".
- Concrete facts every 200 words (numbers, code, config values).
- Tables and code blocks count as facts.
- Avoid filler paragraphs with no new information.

# DIATAXIS FRAMEWORK

- **Tutorial** -- learning-oriented, step-by-step.
- **How-To** -- task-oriented, solve a specific problem.
- **Concept** -- understanding-oriented, explain why.
- **Reference** -- information-oriented, precise and complete.
- **Troubleshooting** -- problem -> cause -> solution.

# VARIABLES SYSTEM

- Use `{{ variable_name }}` from `_variables.yml`.  Never hardcode
  product names, ports, URLs, or environment variable names.
- Use `{{ var | default('fallback') }}` when a fallback is appropriate.
- When you introduce a new shared value, choose a canonical descriptive
  name such as `urls.api_base`, `env.webhook_secret`, `paths.docs_root`,
  or `ports.local_api`.
- Reuse existing shared variables whenever possible. Do not invent near-
  duplicates for the same fact.

# CODE EXAMPLE QUALITY

- Complete and runnable -- no placeholder `...` or `TODO`.
- Realistic data -- "Order #1234" not "foo/bar".
- Error handling included for production examples.
- Comments explain *why*, not *what*.

# ADMONITIONS (MkDocs Material)

```markdown
!!! info "Title"
    Content here.

!!! warning "Important"
    Warning content.

!!! tip "Pro tip"
    Helpful hint.
```

# CONTENT TABS

```markdown
=== "Cloud"

    Cloud-specific content

=== "Self-hosted"

    Self-hosted content
```

# SELF-VERIFICATION

After generating content:
1. Verify every code example compiles/runs mentally.
2. Confirm file paths and commands are correct.
3. Check that port numbers, URLs, and config values match variables.
4. Ensure no passive voice, weasel words, or contractions remain.
5. Validate heading hierarchy (no skipped levels).
"""

# ---------------------------------------------------------------------------
# Per-document-type sub-prompts
# ---------------------------------------------------------------------------

DOC_TYPE_PROMPTS: dict[str, str] = {
    "tutorial": (
        "Focus on step-by-step learning.  Include a 'What you will learn' "
        "section at the top.  Each step must have: description, code, and "
        "explanation.  End with a 'Testing your work' section and 'Next "
        "steps'.  Keep the tone encouraging but never condescending."
    ),
    "how_to": (
        "Focus on solving a specific problem.  Start with 'When to use "
        "this'.  Provide at least two solution options when reasonable.  "
        "Include verification steps so the reader can confirm success.  "
        "Add a troubleshooting section at the end."
    ),
    "concept": (
        "Explain *why* the concept matters before *how* it works.  Use a "
        "Mermaid diagram for the architecture.  Include a comparison table "
        "with alternatives.  End with best practices and common "
        "misconceptions."
    ),
    "reference": (
        "Be precise and complete.  Include every parameter with type, "
        "default, and description.  Show request/response examples for "
        "every endpoint.  Use tables for structured data.  Include status "
        "codes, rate limits, and pagination."
    ),
    "troubleshooting": (
        "Structure every issue as: Symptoms -> Possible Causes -> "
        "Solutions -> Prevention.  Include an error messages reference "
        "table.  Add a 'Quick Diagnostics' section at the top.  Always "
        "mention how to enable debug logging."
    ),
    "release_notes": (
        "Lead with highlights.  Group changes by: New Features, "
        "Improvements, Bug Fixes, Breaking Changes, Deprecations, and "
        "Security.  Each breaking change must include migration steps with "
        "before/after code."
    ),
    "quickstart": (
        "Get the reader to a working result in under 5 minutes.  No "
        "background theory -- just Install, Create, Run, Verify.  Link "
        "to the full tutorial for deeper understanding."
    ),
    "changelog": (
        "Follow Keep a Changelog format.  Categories: Added, Changed, "
        "Fixed, Deprecated, Removed, Security.  Link version headers to "
        "GitHub compare URLs.  Most recent version first."
    ),
    "faq": (
        "Group questions by topic.  Each answer must be self-contained "
        "and concise.  Include code examples where relevant.  Link to "
        "detailed guides for complex topics."
    ),
    "webhook": (
        "Include a sequence diagram showing the webhook flow.  Cover: "
        "registration, events, payload format, signature verification, "
        "retry policy, and local testing."
    ),
    "sdk": (
        "Show installation and initialization for every supported "
        "language using content tabs.  Each method needs parameters, "
        "example, and return type.  Include error handling patterns."
    ),
    "data_model": (
        "Start with an ER diagram.  Document every entity with column "
        "types, constraints, and indexes.  Include example queries.  Show "
        "the migration SQL."
    ),
    "deployment": (
        "Include an architecture diagram.  Cover Docker and Kubernetes "
        "deployments.  List all environment variables.  Include health "
        "check endpoints and rollback procedures."
    ),
    "performance": (
        "Start with benchmarks.  Show before/after for each optimization.  "
        "Include profiling instructions, caching strategy, database tuning, "
        "and load test commands."
    ),
    "testing": (
        "Cover the full test pyramid: unit, integration, e2e.  Show "
        "fixture setup, mocking examples, and CI configuration.  Include "
        "coverage targets."
    ),
    "contributing": (
        "Welcome contributors.  Cover fork/clone, dev setup, branch "
        "naming, commit conventions, PR process, and code style.  Be "
        "friendly but precise."
    ),
    "glossary": (
        "Alphabetical order.  Each term gets a concise definition.  Cross-"
        "reference related terms.  Keep definitions under 50 words."
    ),
    "admin_guide": (
        "Cover user management, backup/restore, log management, database "
        "maintenance, secret rotation, and monitoring checklists.  Include "
        "exact commands for every operation."
    ),
    "configuration": (
        "List every option with type, default, and description.  Show "
        "environment variable overrides.  Include example configurations "
        "for development and production."
    ),
    "cli_reference": (
        "Document every command and flag.  Include examples for each "
        "command.  Show exit codes and shell completion setup."
    ),
    "onboarding": (
        "Structure as Day 1 / Day 2 / Day 3-5.  Include access request "
        "checklists, setup commands, architecture overview, and first "
        "contribution workflow."
    ),
    "security": (
        "Cover authentication, authorization, encryption, security "
        "headers, vulnerability management, and incident response.  "
        "Reference OWASP and compliance standards."
    ),
    "integration_guide": (
        "Step-by-step: get credentials, install SDK, configure, implement "
        "core functionality, handle webhooks, test.  Include error "
        "handling table and monitoring advice."
    ),
    "migration_guide": (
        "Pre-migration checklist, step-by-step changes with before/after "
        "code, database migrations, configuration updates, verification, "
        "and rollback procedure."
    ),
    "adr": (
        "Follow the ADR format: Status, Context, Decision, Rationale, "
        "Consequences, Alternatives Considered.  Be objective and include "
        "both pros and cons."
    ),
    "runbook": (
        "Every step must include: command, verification, success criteria, "
        "and failure action.  Include rollback procedure and emergency "
        "contacts."
    ),
    "auth_flow": (
        "Include a sequence diagram.  Cover authorization request, token "
        "exchange, token refresh, PKCE, and logout.  Show implementation "
        "examples for multiple frameworks."
    ),
}


def build_prompt(
    doc_type: str,
    template_content: str,
    context: dict[str, Any],
    shared_variables: dict[str, Any] | None = None,
) -> str:
    """Build a complete LLM prompt for documentation generation.

    Combines the master system prompt, doc-type-specific instructions,
    the template skeleton, shared variable values, and generation context
    into a single prompt string.

    Args:
        doc_type: Document type key (e.g. "tutorial", "how_to").
        template_content: Raw Jinja2 template content to fill.
        context: Generation context (project structure, code snippets, etc.).
        shared_variables: Optional dict of shared variables the LLM should
            use instead of hardcoding values.

    Returns:
        Complete prompt string ready for LLM generation.
    """
    parts: list[str] = []

    # 1. System prompt
    parts.append(GITSPEAK_SYSTEM_PROMPT)

    # 2. Doc-type-specific instructions
    type_prompt = DOC_TYPE_PROMPTS.get(doc_type, "")
    if type_prompt:
        parts.append(f"\n# DOCUMENT TYPE INSTRUCTIONS\n\n{type_prompt}\n")

    # 3. Shared variables (so LLM knows what to reference)
    if shared_variables:
        var_lines = "\n".join(
            f"- `{{{{ {k} }}}}` = `{v}`" for k, v in shared_variables.items()
        )
        parts.append(
            f"\n# SHARED VARIABLES (use these instead of hardcoding)\n\n"
            f"{var_lines}\n"
        )

    # 4. Template skeleton
    parts.append(
        f"\n# TEMPLATE SKELETON\n\n"
        f"Fill in the following template.  Replace all `{{{{ variable }}}}` "
        f"placeholders with appropriate content.  Keep the Markdown "
        f"structure intact.\n\n"
        f"```markdown\n{template_content}\n```\n"
    )

    parts.append(
        "\n# TEMPLATE AND SNIPPET QUALITY BAR\n\n"
        "Use the template structure as a hard quality skeleton. Reuse or adapt the most relevant "
        "code snippets, examples, tables, and verification blocks from the provided context instead "
        "of inventing thin placeholder examples. Prefer Stripe-grade examples: concrete values, "
        "clear error handling, realistic requests, realistic responses, and exact next steps.\n"
    )

    # 5. Generation context
    if context:
        context_lines = "\n".join(
            f"- **{k}**: {v}" for k, v in context.items()
        )
        parts.append(
            f"\n# GENERATION CONTEXT\n\n{context_lines}\n"
        )

    # 6. Final instruction
    parts.append(
        "\n# OUTPUT\n\n"
        "Return ONLY the completed Markdown document.  Do not include "
        "the template skeleton or these instructions in your output."
    )

    return "\n".join(parts)
