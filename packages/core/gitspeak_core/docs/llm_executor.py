"""LLM executor for Phase 2 doc generation.

GSD-style architecture:
- Claude (Anthropic) as planner/verifier (orchestrator role)
- Groq or DeepSeek as content generators (executor role)
- Fresh context per task (no shared state between tasks)
- Atomic tasks with self-verification

The orchestrator (Claude) creates a detailed plan for each document,
the executor (Groq/DeepSeek) generates the content, and Claude
verifies the result against quality criteria.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider abstraction
# ---------------------------------------------------------------------------

@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str = ""
    model: str = ""
    provider: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_seconds: float = 0.0
    error: str | None = None


class LLMProvider:
    """Unified LLM provider interface for Groq, DeepSeek, and Anthropic."""

    def __init__(
        self,
        groq_api_key: str = "",
        deepseek_api_key: str = "",
        anthropic_api_key: str = "",
        openai_api_key: str = "",
        preference: list[str] | None = None,
    ) -> None:
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.deepseek_api_key = deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        self.preference = preference or ["groq", "deepseek", "anthropic"]

    def get_active_provider(self) -> str:
        """Return the first provider with a valid API key."""
        key_map = {
            "groq": self.groq_api_key,
            "deepseek": self.deepseek_api_key,
            "anthropic": self.anthropic_api_key,
            "openai": self.openai_api_key,
        }
        for provider in self.preference:
            if key_map.get(provider):
                return provider
        return "none"

    def generate(
        self,
        prompt: str,
        system: str = "",
        provider: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> LLMResponse:
        """Generate content using the specified or preferred provider."""
        provider = provider or self.get_active_provider()
        start = time.monotonic()

        try:
            if provider == "groq":
                return self._call_groq(prompt, system, max_tokens, temperature)
            elif provider == "deepseek":
                return self._call_deepseek(prompt, system, max_tokens, temperature)
            elif provider == "anthropic":
                return self._call_anthropic(prompt, system, max_tokens, temperature)
            elif provider == "openai":
                return self._call_openai(prompt, system, max_tokens, temperature)
            else:
                return LLMResponse(error=f"No provider available (tried: {self.preference})")
        except Exception as exc:
            duration = time.monotonic() - start
            logger.error("LLM call failed (%s): %s", provider, exc)
            return LLMResponse(
                provider=provider,
                duration_seconds=duration,
                error=str(exc),
            )

    def _call_groq(self, prompt: str, system: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Call Groq API (OpenAI-compatible)."""
        start = time.monotonic()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", "llama-3.3-70b-versatile"),
            provider="groq",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            duration_seconds=time.monotonic() - start,
        )

    def _call_deepseek(self, prompt: str, system: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Call DeepSeek API (OpenAI-compatible)."""
        start = time.monotonic()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = httpx.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", "deepseek-chat"),
            provider="deepseek",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            duration_seconds=time.monotonic() - start,
        )

    def _call_anthropic(self, prompt: str, system: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Call Anthropic API (Claude)."""
        start = time.monotonic()
        body: dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        usage = data.get("usage", {})

        return LLMResponse(
            content=text,
            model=data.get("model", "claude-sonnet-4-20250514"),
            provider="anthropic",
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            duration_seconds=time.monotonic() - start,
        )

    def _call_openai(self, prompt: str, system: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Call OpenAI API."""
        start = time.monotonic()
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4.1-mini",
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})

        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", "gpt-4.1-mini"),
            provider="openai",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            duration_seconds=time.monotonic() - start,
        )


# ---------------------------------------------------------------------------
# GSD-style doc generation executor
# ---------------------------------------------------------------------------

@dataclass
class GenerationResult:
    """Result of a single document generation task."""

    task_id: str = ""
    status: str = "pending"  # pending/success/failure
    document_path: str = ""
    content: str = ""
    self_check_score: float = 0.0
    plan_provider: str = ""
    gen_provider: str = ""
    verify_provider: str = ""
    total_tokens: int = 0
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    retries: int = 0


class GSDDocExecutor:
    """GSD-style doc generation executor.

    Architecture:
    1. PLAN: Claude analyzes the action item and creates a detailed
       generation plan (what to write, structure, examples needed)
    2. GENERATE: Groq/DeepSeek generates the document content following
       the plan and system prompt
    3. VERIFY: Claude reviews the generated content against quality
       criteria and suggests fixes
    4. FIX (if needed): Groq/DeepSeek applies fixes and regenerates

    Each task gets fresh context (no shared state between tasks).
    """

    def __init__(
        self,
        llm: LLMProvider,
        repo_root: str | Path = ".",
        plan_provider: str = "anthropic",
        gen_provider: str | None = None,  # auto-select fastest
        verify_provider: str = "anthropic",
        max_retries: int = 2,
    ) -> None:
        self.llm = llm
        self.repo_root = Path(repo_root)
        self.plan_provider = plan_provider
        self.gen_provider = gen_provider or llm.get_active_provider()
        self.verify_provider = verify_provider
        self.max_retries = max_retries

        # Load system prompt
        from gitspeak_core.docs.system_prompt import (
            DOC_TYPE_PROMPTS,
            GITSPEAK_SYSTEM_PROMPT,
            build_prompt,
        )

        self._system_prompt = GITSPEAK_SYSTEM_PROMPT
        self._doc_type_prompts = DOC_TYPE_PROMPTS
        self._build_prompt = build_prompt

    def execute_task(self, task: dict[str, Any]) -> GenerationResult:
        """Execute a single doc generation task using GSD pattern.

        Args:
            task: Task dict with task_id, full_context (description,
                  output_format, dependencies, etc.)

        Returns:
            GenerationResult with generated content and metrics.
        """
        start = time.monotonic()
        result = GenerationResult(task_id=task.get("task_id", ""))
        context = task.get("full_context", {})
        output_format = context.get("output_format", {})
        doc_type = output_format.get("content_type", "how-to")
        # Normalize doc_type for prompt lookup
        doc_type_key = doc_type.replace("-", "_")

        total_tokens = 0

        for attempt in range(self.max_retries + 1):
            result.retries = attempt

            # STEP 1: PLAN (Claude)
            plan_response = self._create_plan(context, doc_type_key)
            if plan_response.error:
                result.errors.append(f"Plan failed: {plan_response.error}")
                continue
            total_tokens += plan_response.prompt_tokens + plan_response.completion_tokens
            result.plan_provider = plan_response.provider

            # STEP 2: GENERATE (Groq/DeepSeek)
            gen_response = self._generate_content(
                plan=plan_response.content,
                context=context,
                doc_type_key=doc_type_key,
            )
            if gen_response.error:
                result.errors.append(f"Generation failed: {gen_response.error}")
                continue
            total_tokens += gen_response.prompt_tokens + gen_response.completion_tokens
            result.gen_provider = gen_response.provider

            # STEP 3: VERIFY (Claude)
            verify_response = self._verify_content(
                content=gen_response.content,
                context=context,
                doc_type_key=doc_type_key,
            )
            total_tokens += verify_response.prompt_tokens + verify_response.completion_tokens
            result.verify_provider = verify_response.provider

            # Parse verification result
            score, issues = self._parse_verification(verify_response.content)
            result.self_check_score = score

            if score >= 80.0 or not issues:
                # Content passes quality bar
                result.status = "success"
                result.content = gen_response.content
                break
            else:
                # STEP 4: FIX (Groq/DeepSeek)
                fix_response = self._fix_content(
                    content=gen_response.content,
                    issues=issues,
                    context=context,
                    doc_type_key=doc_type_key,
                )
                total_tokens += fix_response.prompt_tokens + fix_response.completion_tokens

                if fix_response.error:
                    result.errors.append(f"Fix failed: {fix_response.error}")
                    continue

                # Re-verify
                verify2 = self._verify_content(
                    content=fix_response.content,
                    context=context,
                    doc_type_key=doc_type_key,
                )
                total_tokens += verify2.prompt_tokens + verify2.completion_tokens
                score2, _ = self._parse_verification(verify2.content)
                result.self_check_score = score2

                if score2 >= 70.0:
                    result.status = "success"
                    result.content = fix_response.content
                    break
                else:
                    result.errors.append(
                        f"Attempt {attempt + 1}: score {score2:.0f} below threshold"
                    )

        if result.status != "success":
            result.status = "failure"
            # Use best content we have
            if gen_response and not gen_response.error:
                result.content = gen_response.content

        result.total_tokens = total_tokens
        result.duration_seconds = time.monotonic() - start

        logger.info(
            "Task %s: %s (score=%.0f, tokens=%d, %.1fs, retries=%d)",
            result.task_id,
            result.status,
            result.self_check_score,
            result.total_tokens,
            result.duration_seconds,
            result.retries,
        )

        return result

    def _create_plan(self, context: dict, doc_type_key: str) -> LLMResponse:
        """Step 1: Claude creates a detailed generation plan."""
        description = context.get("description", "")
        output_format = context.get("output_format", {})
        dependencies = context.get("dependencies", [])
        patterns = context.get("patterns_to_follow", [])

        prompt = f"""Analyze this documentation task and create a detailed generation plan.

TASK: {description}

DOCUMENT TYPE: {doc_type_key}
TITLE: {output_format.get('title', '')}
DESCRIPTION: {output_format.get('description', '')}

RELATED FILES: {json.dumps(dependencies[:10])}

SUCCESSFUL PATTERNS FROM SIMILAR TASKS:
{chr(10).join(patterns[:3]) if patterns else 'None available.'}

Create a plan with:
1. Document structure (sections and subsections)
2. Key content points for each section
3. Code examples needed (language, what to demonstrate)
4. Tables or diagrams to include
5. Internal links to suggest
6. Variables from _variables.yml to use
7. Specific terminology from glossary.yml

Return the plan as structured markdown."""

        return self.llm.generate(
            prompt=prompt,
            system="You are a senior technical documentation architect. Create precise, actionable plans.",
            provider=self.plan_provider,
            max_tokens=2048,
            temperature=0.2,
        )

    def _generate_content(self, plan: str, context: dict, doc_type_key: str) -> LLMResponse:
        """Step 2: Groq/DeepSeek generates the document content."""
        output_format = context.get("output_format", {})

        # Load template if available
        template_content = ""
        try:
            from gitspeak_core.docs.template_library import TemplateLibrary
            lib = TemplateLibrary()
            tpl = lib.get_template(doc_type_key)
            if tpl:
                template_content = tpl.content
        except (ImportError, OSError) as exc:
            logger.debug("Template library unavailable: %s", exc)

        # Load shared variables from _variables.yml if available
        shared_variables: dict[str, Any] | None = None
        variables_path = self.repo_root / "docs" / "_variables.yml"
        if variables_path.exists():
            try:
                import yaml  # noqa: F811 — heavy module, lazy import justified

                shared_variables = yaml.safe_load(
                    variables_path.read_text(encoding="utf-8")
                )
            except (ImportError, OSError) as exc:
                logger.debug("Could not load _variables.yml: %s", exc)

        # Build the full prompt using VeriOps system
        full_prompt = self._build_prompt(
            doc_type=doc_type_key,
            template_content=template_content or f"# {output_format.get('title', 'Document')}\n\n[Content here]",
            context={
                "plan": plan,
                "description": context.get("description", ""),
                "title": output_format.get("title", ""),
            },
            shared_variables=shared_variables,
        )

        return self.llm.generate(
            prompt=full_prompt,
            system=self._system_prompt,
            provider=self.gen_provider,
            max_tokens=4096,
            temperature=0.1,
        )

    def _verify_content(self, content: str, context: dict, doc_type_key: str) -> LLMResponse:
        """Step 3: Claude verifies the generated content."""
        output_format = context.get("output_format", {})

        prompt = f"""Review this generated documentation against quality criteria.

DOCUMENT TYPE: {doc_type_key}
EXPECTED TITLE: {output_format.get('title', '')}

CONTENT:
```markdown
{content[:6000]}
```

Score the document (0-100) and list issues. Check:
1. FRONTMATTER: title (max 70 chars), description (50-160 chars), content_type, tags
2. STRUCTURE: single H1 matching title, no heading level skips, blank lines
3. STYLE: American English, active voice, no weasel words, no contractions
4. GEO: first paragraph under 60 words with definition verb, descriptive headings
5. CODE: all code blocks have language tags, examples are complete and realistic
6. FACTS: specific numbers, no vague claims
7. VARIABLES: no hardcoded product names/ports/URLs (should use {{{{ variable }}}})

Return JSON:
{{"score": <0-100>, "issues": ["issue1", "issue2", ...], "summary": "brief assessment"}}"""

        return self.llm.generate(
            prompt=prompt,
            system="You are a strict documentation quality reviewer. Be precise and objective.",
            provider=self.verify_provider,
            max_tokens=1024,
            temperature=0.0,
        )

    def _fix_content(self, content: str, issues: list[str], context: dict, doc_type_key: str) -> LLMResponse:
        """Step 4: Groq/DeepSeek fixes identified issues."""
        issues_text = "\n".join(f"- {issue}" for issue in issues)

        prompt = f"""Fix the following issues in this documentation:

ISSUES TO FIX:
{issues_text}

CURRENT CONTENT:
```markdown
{content[:6000]}
```

Return ONLY the corrected Markdown document. Apply all fixes while preserving good content."""

        return self.llm.generate(
            prompt=prompt,
            system=self._system_prompt,
            provider=self.gen_provider,
            max_tokens=4096,
            temperature=0.1,
        )

    def _parse_verification(self, response: str) -> tuple[float, list[str]]:
        """Parse the verification response into score and issues."""
        try:
            # Try to extract JSON from the response
            text = response.strip()
            # Find JSON block
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            data = json.loads(text)
            score = float(data.get("score", 0))
            issues = data.get("issues", [])
            return score, issues
        except (json.JSONDecodeError, ValueError, IndexError):
            # Fallback: try to find score in text
            logger.debug("Could not parse verification JSON, using fallback")
            return 50.0, ["Could not parse verification response"]
