#!/usr/bin/env python3
"""GEO (Generative Engine Optimization) linter for documentation.

Checks structural signals that affect how LLMs extract and cite content:
- First paragraph answer density
- Heading descriptiveness
- Fact density
- Meta description quality
- Heading hierarchy
"""

import re
import sys
import yaml
from pathlib import Path

RULES = {
    "first_para_max_words": 60,
    "max_words_without_fact": 200,
    "meta_desc_min_chars": 50,
    "meta_desc_max_chars": 160,
    "min_heading_words": 3,
    "generic_headings": [
        "overview", "introduction", "configuration", "setup",
        "details", "information", "general", "notes", "summary"
    ],
    "definition_patterns": [
        r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
        r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b"
    ],
    "fact_patterns": [
        r"\d+", r"`[^`]+`", r"\bdefault\b", r"\bport\b",
        r"\bversion\b", r"\bMB\b", r"\bGB\b", r"\bms\b",
        r"```", r"\bhttp[s]?://\b"
    ]
}

class Finding:
    def __init__(self, filepath, line, rule, message, severity="warning"):
        self.filepath = filepath
        self.line = line
        self.rule = rule
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"  {self.filepath}:{self.line} [{self.severity}] {self.rule}: {self.message}"

def extract_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
        return fm, parts[2]
    except yaml.YAMLError:
        return {}, text

def get_first_paragraph(content):
    lines = content.strip().split("\n")
    para = []
    started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if started:
                break
            continue
        if stripped.startswith("#"):
            started = True
            continue
        if started or not stripped.startswith("#"):
            para.append(stripped)
            started = True
    return " ".join(para)

def lint_file(filepath):
    findings = []
    text = filepath.read_text(encoding="utf-8")
    fm, content = extract_frontmatter(text)
    lines = text.split("\n")

    # Rule 1: Meta description
    desc = fm.get("description", "")
    if not desc:
        findings.append(Finding(filepath, 1, "meta-description-missing",
                                "Missing frontmatter 'description' field", "error"))
    elif len(desc) < RULES["meta_desc_min_chars"]:
        findings.append(Finding(filepath, 1, "meta-description-short",
                                f"Description too short ({len(desc)} < {RULES['meta_desc_min_chars']} chars)"))
    elif len(desc) > RULES["meta_desc_max_chars"]:
        findings.append(Finding(filepath, 1, "meta-description-long",
                                f"Description too long ({len(desc)} > {RULES['meta_desc_max_chars']} chars)"))

    # Rule 2: First paragraph density
    first_para = get_first_paragraph(content)
    word_count = len(first_para.split())
    if word_count > RULES["first_para_max_words"]:
        findings.append(Finding(filepath, 3, "first-paragraph-too-long",
                                f"First paragraph: {word_count} words (max {RULES['first_para_max_words']}). "
                                "LLMs extract the first ~60 words for answers."))

    # Rule 3: First paragraph should contain a definition
    has_definition = any(re.search(p, first_para, re.IGNORECASE) for p in RULES["definition_patterns"])
    if first_para and not has_definition:
        findings.append(Finding(filepath, 3, "first-paragraph-no-definition",
                                "First paragraph lacks a definition pattern (is/enables/provides). "
                                "LLMs need explicit definitions to extract answers.", "suggestion"))

    # Rule 4: Generic headings
    for i, line in enumerate(lines, 1):
        if line.startswith("#"):
            heading_text = re.sub(r'^#+\s*', '', line).strip().lower()
            if heading_text in RULES["generic_headings"]:
                findings.append(Finding(filepath, i, "heading-generic",
                                        f"Generic heading '{line.strip()}'. Use descriptive headings "
                                        "for LLM retrieval (e.g., 'Configure SASL authentication' not 'Configuration')."))

    # Rule 5: Heading hierarchy
    prev_level = 0
    for i, line in enumerate(lines, 1):
        if line.startswith("#") and not line.startswith("```"):
            level = len(line.split()[0]) if line.split() else 0
            if level > prev_level + 1 and prev_level > 0:
                findings.append(Finding(filepath, i, "heading-hierarchy-skip",
                                        f"Heading level skipped: H{prev_level} → H{level}", "error"))
            prev_level = level

    # Rule 6: Fact density
    in_code_block = False
    word_buffer = []
    buffer_start = 0
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            word_buffer = []
            continue
        if in_code_block or line.startswith("#") or line.startswith("|"):
            word_buffer = []
            buffer_start = i
            continue

        word_buffer.extend(line.split())
        if not buffer_start:
            buffer_start = i

        has_fact = any(re.search(p, line) for p in RULES["fact_patterns"])
        if has_fact:
            word_buffer = []
            buffer_start = i

        if len(word_buffer) > RULES["max_words_without_fact"]:
            findings.append(Finding(filepath, buffer_start, "low-fact-density",
                                    f"{len(word_buffer)} words without concrete facts "
                                    f"(numbers, code, config values). Add specifics for LLM extraction."))
            word_buffer = []
            buffer_start = i

    return findings

def main():
    if len(sys.argv) < 2:
        print("Usage: python geo_lint.py <path>", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1])
    files = sorted(target.rglob("*.md")) if target.is_dir() else [target]
    files = [f for f in files if not f.name.startswith("_")]

    all_findings = []
    for f in files:
        all_findings.extend(lint_file(f))

    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warning"]
    suggestions = [f for f in all_findings if f.severity == "suggestion"]

    if all_findings:
        print(f"\n🔍 GEO Lint: {len(errors)} error(s), {len(warnings)} warning(s), {len(suggestions)} suggestion(s)\n")
        for f in all_findings:
            print(f)
        print()

    if errors:
        sys.exit(1)
    else:
        print("✅ GEO Lint: no blocking errors")

if __name__ == "__main__":
    main()
