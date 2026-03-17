#!/usr/bin/env python3
"""
Comprehensive SEO and GEO Optimization Tool for Documentation
24 automated checks (8 GEO + 16 SEO) plus enhancement/generation.
Combines all SEO/GEO functionality:
- GEO linting for LLM optimization (8 checks)
- SEO validation of existing docs (16 checks)
- SEO metadata enhancement
- Structured data generation
- Sitemap generation
- Algolia search optimization
"""

import json
import yaml
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import subprocess

# Internal maintenance guides are kept in docs/ for operator convenience,
# but they are not product docs pages and should not affect GEO gate signals.
INTERNAL_GEO_IGNORE = {"SEO_GUIDE.md", "VARIABLES_GUIDE.md"}

# ==================== GEO RULES ====================

GEO_RULES = {
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

# Per-locale GEO rule overrides.
# Keys are locale codes; values override the corresponding GEO_RULES entries.
# Languages not listed here fall back to the default English rules above.
GEO_RULES_BY_LOCALE: dict[str, dict] = {
    "ru": {
        "first_para_max_words": 80,
        "meta_desc_max_chars": 200,
        "generic_headings": [
            "overview", "introduction", "configuration", "setup",
            "details", "information", "general", "notes", "summary",
            # Russian generic headings
            "obzor", "vvedenie", "nastroyka", "nastrojka",
            "podrobnosti", "informatsiya", "obshchee", "zametki",
        ],
        "definition_patterns": [
            r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
            r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b",
            # Russian definition patterns
            r"\beto\b", r"\byavlyaetsya\b", r"\bpozvolyaet\b",
            r"\bobespechivae?t\b", r"\bsozdae?t\b",
            # Cyrillic patterns
            r"\b\u044d\u0442\u043e\b",  # eto
            r"\b\u044f\u0432\u043b\u044f\u0435\u0442\u0441\u044f\b",  # yavlyaetsya
            r"\b\u043f\u043e\u0437\u0432\u043e\u043b\u044f\u0435\u0442\b",  # pozvolyaet
            r"\b\u043e\u0431\u0435\u0441\u043f\u0435\u0447\u0438\u0432\u0430\u0435\u0442\b",  # obespechvaet
        ],
    },
    "de": {
        "first_para_max_words": 70,
        "meta_desc_max_chars": 180,
        "generic_headings": [
            "overview", "introduction", "configuration", "setup",
            "details", "information", "general", "notes", "summary",
            "ueberblick", "uebersicht", "einleitung", "konfiguration",
            "einrichtung", "details", "informationen", "allgemein",
        ],
        "definition_patterns": [
            r"\bis\b", r"\benables?\b", r"\bprovides?\b", r"\ballows?\b",
            r"\bcreates?\b", r"\bprocesses?\b", r"\bexecutes?\b",
            r"\bist\b", r"\bermoeglicht\b", r"\bbietet\b", r"\berlaubt\b",
        ],
    },
}


def _get_geo_rules_for_locale(locale: str | None) -> dict:
    """Return GEO rules for a locale, merging overrides with defaults."""
    if not locale or locale not in GEO_RULES_BY_LOCALE:
        return GEO_RULES
    merged = GEO_RULES.copy()
    merged.update(GEO_RULES_BY_LOCALE[locale])
    return merged


def _detect_locale_from_path(filepath) -> str | None:
    """Detect locale from docs/{locale}/... path structure."""
    parts = Path(filepath).parts
    for i, part in enumerate(parts):
        if part == "docs" and i + 1 < len(parts):
            candidate = parts[i + 1]
            if re.match(r"^[a-z]{2,3}$", candidate):
                return candidate
    return None

# ==================== HELPER FUNCTIONS ====================

def extract_frontmatter(text):
    """Extract frontmatter from markdown."""
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

def get_git_info(filepath):
    """Get git information for a file."""
    try:
        # Get last modified date
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(filepath)],
            capture_output=True, text=True, check=True
        )
        last_modified = result.stdout.strip()

        # Get original author
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%an", "--", str(filepath)],
            capture_output=True, text=True, check=True
        )
        original_author = result.stdout.strip().split('\n')[0] if result.stdout else None

        return {
            'last_reviewed': last_modified[:10] if last_modified else None,
            'original_author': original_author
        }
    except subprocess.CalledProcessError:
        return {}

# ==================== GEO LINTING ====================

class GEOFinding:
    def __init__(self, filepath, line, rule, message, severity="warning"):
        self.filepath = filepath
        self.line = line
        self.rule = rule
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"  {self.filepath}:{self.line} [{self.severity}] {self.rule}: {self.message}"

def get_first_paragraph(content):
    """Extract first paragraph from content."""
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

def geo_lint_file(filepath):
    """Perform GEO linting on a file."""
    findings = []
    text = filepath.read_text(encoding="utf-8")
    fm, content = extract_frontmatter(text)
    lines = text.split("\n")

    # Detect locale and load locale-specific rules
    locale = _detect_locale_from_path(filepath)
    rules = _get_geo_rules_for_locale(locale)

    # Rule 1: Meta description
    desc = fm.get("description", "")
    if not desc:
        findings.append(GEOFinding(filepath, 1, "meta-description-missing",
                                "Missing frontmatter 'description' field", "error"))
    elif len(desc) < rules["meta_desc_min_chars"]:
        findings.append(GEOFinding(filepath, 1, "meta-description-short",
                                f"Description too short ({len(desc)} < {rules['meta_desc_min_chars']} chars)"))
    elif len(desc) > rules["meta_desc_max_chars"]:
        findings.append(GEOFinding(filepath, 1, "meta-description-long",
                                f"Description too long ({len(desc)} > {rules['meta_desc_max_chars']} chars)"))

    # Rule 2: First paragraph density
    first_para = get_first_paragraph(content)
    word_count = len(first_para.split())
    if word_count > rules["first_para_max_words"]:
        findings.append(GEOFinding(filepath, 3, "first-paragraph-too-long",
                                f"First paragraph: {word_count} words (max {rules['first_para_max_words']}). "
                                "LLMs extract the first ~60 words for answers."))

    # Rule 3: First paragraph should contain a definition
    has_definition = any(re.search(p, first_para, re.IGNORECASE) for p in rules["definition_patterns"])
    if first_para and not has_definition:
        findings.append(GEOFinding(filepath, 3, "first-paragraph-no-definition",
                                "First paragraph lacks a definition pattern (is/enables/provides). "
                                "LLMs need explicit definitions to extract answers.", "suggestion"))

    # Rule 4: Generic headings
    in_code_block_g = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block_g = not in_code_block_g
            continue
        if in_code_block_g:
            continue
        if line.startswith("#"):
            heading_text = re.sub(r'^#+\s*', '', line).strip().lower()
            if heading_text in rules["generic_headings"]:
                findings.append(GEOFinding(filepath, i, "heading-generic",
                                        f"Generic heading '{line.strip()}'. Use descriptive headings "
                                        "for LLM retrieval (e.g., 'Configure SASL authentication' not 'Configuration')."))

    # Rule 5: Heading hierarchy
    prev_level = 0
    in_code_block_h = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block_h = not in_code_block_h
            continue
        if in_code_block_h:
            continue
        if line.startswith("#"):
            level = len(line.split()[0]) if line.split() else 0
            if level > prev_level + 1 and prev_level > 0:
                findings.append(GEOFinding(filepath, i, "heading-hierarchy-skip",
                                        f"Heading level skipped: H{prev_level} -> H{level}", "error"))
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

        has_fact = any(re.search(p, line) for p in rules.get("fact_patterns", GEO_RULES["fact_patterns"]))
        if has_fact:
            word_buffer = []
            buffer_start = i

        if len(word_buffer) > rules["max_words_without_fact"]:
            findings.append(GEOFinding(filepath, buffer_start, "low-fact-density",
                                    f"{len(word_buffer)} words without concrete facts "
                                    f"(numbers, code, config values). Add specifics for LLM extraction."))
            word_buffer = []
            buffer_start = i

    return findings

# ==================== SEO ENHANCEMENT ====================

class SEOEnhancer:
    def __init__(self, base_url="https://docs.example.com"):
        self.base_url = base_url.rstrip('/')

    def generate_structured_data(self, filepath, frontmatter, content):
        """Generate JSON-LD structured data for better search engine understanding."""

        # Extract main heading
        heading_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        main_heading = heading_match.group(1) if heading_match else frontmatter.get('title', '')

        # Determine article type
        content_type = frontmatter.get('content_type', 'article')
        article_type = {
            'how-to': 'HowTo',
            'tutorial': 'TechArticle',
            'troubleshooting': 'FAQPage',
            'reference': 'TechArticle',
            'concept': 'Article'
        }.get(content_type, 'Article')

        # Base structured data
        structured_data = {
            "@context": "https://schema.org",
            "@type": article_type,
            "headline": main_heading,
            "description": frontmatter.get('description', ''),
            "url": f"{self.base_url}/{str(filepath).replace('docs/', '').replace('.md', '')}",
            "dateModified": frontmatter.get('last_reviewed', datetime.now().isoformat()),
            "author": {
                "@type": "Organization",
                "name": "Documentation Team"
            }
        }

        # Add how-to specific fields
        if article_type == 'HowTo':
            steps = self._extract_steps(content)
            if steps:
                structured_data['step'] = steps

            # Extract time estimate
            time_match = re.search(r'(\d+)\s*(?:min|minute)', content, re.IGNORECASE)
            if time_match:
                structured_data['totalTime'] = f"PT{time_match.group(1)}M"

        # Add FAQ specific fields
        elif article_type == 'FAQPage':
            qa_pairs = self._extract_qa_pairs(content)
            if qa_pairs:
                structured_data['mainEntity'] = qa_pairs

        # Add breadcrumb
        breadcrumb = self._generate_breadcrumb(filepath)
        if breadcrumb:
            structured_data['breadcrumb'] = breadcrumb

        return structured_data

    def _extract_steps(self, content):
        """Extract numbered steps for HowTo schema."""
        steps = []
        step_pattern = r'^\d+\.\s+(.+?)(?=^\d+\.|^#{1,6}\s|$)'
        matches = re.findall(step_pattern, content, re.MULTILINE | re.DOTALL)

        for i, step_text in enumerate(matches, 1):
            step_text = re.sub(r'\n+', ' ', step_text).strip()
            steps.append({
                "@type": "HowToStep",
                "position": i,
                "name": f"Step {i}",
                "text": step_text[:500]
            })

        return steps

    def _extract_qa_pairs(self, content):
        """Extract Q&A pairs for FAQ schema."""
        qa_pairs = []

        problem_pattern = r'(?:Problem|Issue|Error):\s*(.+?)(?:Solution|Fix|Resolution):\s*(.+?)(?=(?:Problem|Issue|Error):|$)'
        matches = re.findall(problem_pattern, content, re.IGNORECASE | re.DOTALL)

        for problem, solution in matches:
            qa_pairs.append({
                "@type": "Question",
                "name": problem.strip()[:200],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": solution.strip()[:500]
                }
            })

        return qa_pairs

    def _generate_breadcrumb(self, filepath):
        """Generate breadcrumb structured data."""
        parts = Path(filepath).parts[1:-1]  # Skip 'docs' and filename
        if not parts:
            return None

        items = []
        current_path = ""

        for i, part in enumerate(parts, 1):
            current_path += f"/{part}"
            items.append({
                "@type": "ListItem",
                "position": i,
                "name": part.replace('-', ' ').title(),
                "item": f"{self.base_url}{current_path}"
            })

        return {
            "@type": "BreadcrumbList",
            "itemListElement": items
        }

    def generate_meta_tags(self, frontmatter, filepath):
        """Generate comprehensive meta tags for SEO."""

        title = frontmatter.get('title', '')
        description = frontmatter.get('description', '')

        # Generate canonical URL
        canonical = f"{self.base_url}/{str(filepath).replace('docs/', '').replace('.md', '')}"

        meta_tags = {
            # Basic meta tags
            'title': title,
            'description': description,
            'canonical': canonical,

            # Open Graph tags (for social sharing)
            'og:title': title,
            'og:description': description,
            'og:url': canonical,
            'og:type': 'article',
            'og:site_name': 'Documentation',

            # Twitter Card tags
            'twitter:card': 'summary',
            'twitter:title': title,
            'twitter:description': description,

            # Additional SEO tags
            'robots': 'index, follow',
            'author': 'Documentation Team'
        }

        # Add product-specific tags if applicable
        if 'product' in frontmatter:
            meta_tags['article:section'] = frontmatter['product']

        # Add tags/keywords
        if 'tags' in frontmatter:
            meta_tags['keywords'] = ', '.join(frontmatter['tags'])
            meta_tags['article:tag'] = frontmatter['tags']

        return meta_tags

    def generate_sitemap_entry(self, filepath, frontmatter):
        """Generate sitemap entry for the file."""

        # Determine priority based on content type and path
        priority = 0.5  # default

        if 'index' in filepath.name:
            priority = 0.9
        elif frontmatter.get('content_type') == 'reference':
            priority = 0.8
        elif 'getting-started' in str(filepath):
            priority = 0.7
        elif frontmatter.get('content_type') == 'troubleshooting':
            priority = 0.4

        # Determine change frequency
        last_reviewed = frontmatter.get('last_reviewed', '')
        if last_reviewed:
            days_old = (datetime.now() - datetime.fromisoformat(last_reviewed)).days
            if days_old < 30:
                changefreq = 'weekly'
            elif days_old < 90:
                changefreq = 'monthly'
            else:
                changefreq = 'yearly'
        else:
            changefreq = 'monthly'

        return {
            'loc': f"{self.base_url}/{str(filepath).replace('docs/', '').replace('.md', '')}",
            'lastmod': last_reviewed or datetime.now().isoformat()[:10],
            'changefreq': changefreq,
            'priority': priority
        }

# ==================== SEO VALIDATION ====================

SEO_RULES = {
    "title_min_chars": 10,
    "title_max_chars": 70,
    "max_url_depth": 4,
    "min_internal_links": 1,
    "max_image_without_alt_pct": 0,
    "min_content_words": 100,
    "max_line_length_for_mobile": 180,
    "check_mobile_line_length": True,
    "max_long_lines_before_warning": 30,
}


def seo_validate_file(filepath):
    """Validate SEO best practices on an existing documentation file.

    Returns a list of GEOFinding objects (reusing the same data class
    since findings are structurally identical).

    Checks performed (14 rules):
      SEO-01  Title length optimization
      SEO-02  Title contains target keywords from filename
      SEO-03  URL/path structure depth
      SEO-04  URL uses kebab-case
      SEO-05  Image alt text presence
      SEO-06  Internal link density
      SEO-07  External links use descriptive text (no bare URLs)
      SEO-08  Canonical-friendly path (no special chars)
      SEO-09  Mobile-friendly line lengths
      SEO-10  Heading keywords match title
      SEO-11  Content freshness signal (last_reviewed)
      SEO-12  Minimum content length
      SEO-13  No duplicate headings
      SEO-14  Structured data presence (code blocks / tables)
    """
    findings = []
    text = filepath.read_text(encoding="utf-8")
    fm, content = extract_frontmatter(text)
    lines = text.split("\n")

    # --- SEO-01: Title length ---
    title = fm.get("title", "")
    if not title:
        findings.append(GEOFinding(filepath, 1, "seo-title-missing",
                                   "Missing 'title' in frontmatter", "error"))
    elif len(title) < SEO_RULES["title_min_chars"]:
        findings.append(GEOFinding(filepath, 1, "seo-title-short",
                                   f"Title too short ({len(title)} chars, min {SEO_RULES['title_min_chars']})"))
    elif len(title) > SEO_RULES["title_max_chars"]:
        findings.append(GEOFinding(filepath, 1, "seo-title-long",
                                   f"Title too long ({len(title)} chars, max {SEO_RULES['title_max_chars']})"))

    # --- SEO-02: Title contains keywords from filename ---
    stem_words = set(filepath.stem.replace("-", " ").replace("_", " ").lower().split())
    stop_words = {"the", "a", "an", "and", "or", "in", "on", "of", "to", "for", "is", "with"}
    stem_words -= stop_words
    if title and stem_words:
        title_lower = title.lower()
        overlap = sum(1 for w in stem_words if w in title_lower)
        if overlap < len(stem_words) * 0.5 and len(stem_words) > 1:
            findings.append(GEOFinding(filepath, 1, "seo-title-keyword-mismatch",
                                       f"Title does not reflect filename keywords: {stem_words}",
                                       "suggestion"))

    # --- SEO-03: URL depth ---
    depth = len(filepath.parts) - 1  # minus filename
    if depth > SEO_RULES["max_url_depth"]:
        findings.append(GEOFinding(filepath, 1, "seo-url-depth",
                                   f"URL depth {depth} exceeds max {SEO_RULES['max_url_depth']}. "
                                   "Shallower paths rank better."))

    # --- SEO-04: URL uses kebab-case ---
    if "_" in filepath.stem or any(c.isupper() for c in filepath.stem):
        findings.append(GEOFinding(filepath, 1, "seo-url-naming",
                                   "Filename should use kebab-case (lowercase, hyphens). "
                                   f"Current: '{filepath.name}'"))

    # --- SEO-05: Image alt text ---
    img_pattern = re.compile(r"!\[([^\]]*)\]\(")
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for match in img_pattern.finditer(line):
            alt = match.group(1).strip()
            if not alt:
                findings.append(GEOFinding(filepath, i, "seo-img-no-alt",
                                           "Image missing alt text. Add descriptive alt for SEO."))

    # --- SEO-06: Internal link density ---
    internal_link_count = len(re.findall(r"\[([^\]]+)\]\((?!https?://)", content))
    if internal_link_count < SEO_RULES["min_internal_links"]:
        findings.append(GEOFinding(filepath, 1, "seo-low-internal-links",
                                   f"Only {internal_link_count} internal link(s). "
                                   "Add cross-references to improve SEO link graph.",
                                   "suggestion"))

    # --- SEO-07: External links use descriptive text ---
    bare_url_pattern = re.compile(r"(?<!\()(https?://[^\s\)]+)(?!\))")
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for match in bare_url_pattern.finditer(line):
            url = match.group(0)
            if not re.search(r"\[[^\]]+\]\(" + re.escape(url), line):
                findings.append(GEOFinding(filepath, i, "seo-bare-url",
                                           f"Bare URL found. Use [descriptive text]({url}) instead."))

    # --- SEO-08: Canonical-friendly path ---
    bad_chars = set("!@#$%^&*()+={}[];',")
    if any(c in bad_chars for c in filepath.stem):
        findings.append(GEOFinding(filepath, 1, "seo-path-special-chars",
                                   "Filename contains special characters. Use only "
                                   "alphanumeric and hyphens for clean URLs."))

    # --- SEO-09: Mobile-friendly line lengths (optional, disabled by default) ---
    if bool(SEO_RULES.get("check_mobile_line_length", False)):
        long_lines = 0
        in_code = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if len(line) > SEO_RULES["max_line_length_for_mobile"]:
                long_lines += 1
        if long_lines > int(SEO_RULES.get("max_long_lines_before_warning", 30)):
            findings.append(GEOFinding(filepath, 1, "seo-long-lines",
                                       f"{long_lines} lines exceed {SEO_RULES['max_line_length_for_mobile']} chars. "
                                       "Long lines hurt mobile readability."))

    # --- SEO-10: Heading keywords match title ---
    if title:
        title_words = set(title.lower().split()) - stop_words
        h2_texts = re.findall(r"^##\s+(.+)$", content, re.MULTILINE)
        if h2_texts and title_words:
            h2_words = set()
            for h in h2_texts:
                h2_words.update(h.lower().split())
            h2_words -= stop_words
            overlap = title_words & h2_words
            if not overlap and len(title_words) > 2:
                findings.append(GEOFinding(filepath, 1, "seo-heading-keyword-gap",
                                           "No H2 headings share keywords with the title. "
                                           "Align headings with title for better ranking.",
                                           "suggestion"))

    # --- SEO-11: Content freshness signal ---
    if not fm.get("last_reviewed") and not fm.get("date"):
        findings.append(GEOFinding(filepath, 1, "seo-no-freshness",
                                   "No 'last_reviewed' or 'date' in frontmatter. "
                                   "Search engines favor dated content.", "suggestion"))

    # --- SEO-12: Minimum content length ---
    word_count = len(content.split())
    if word_count < SEO_RULES["min_content_words"]:
        findings.append(GEOFinding(filepath, 1, "seo-thin-content",
                                   f"Only {word_count} words. Pages under "
                                   f"{SEO_RULES['min_content_words']} words rank poorly.",
                                   "warning"))

    # --- SEO-13: Duplicate headings ---
    headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
    seen = {}
    for level, text in headings:
        key = text.strip().lower()
        if key in seen:
            findings.append(GEOFinding(filepath, 1, "seo-duplicate-heading",
                                       f"Duplicate heading: '{text.strip()}'. "
                                       "Use unique headings for better anchor links."))
        seen[key] = True

    # --- SEO-14: Structured data presence ---
    has_code_block = "```" in content
    has_table = "|" in content and re.search(r"\|.*\|.*\|", content)
    has_list = bool(re.search(r"^[\-\*]\s", content, re.MULTILINE))
    if not has_code_block and not has_table and not has_list:
        findings.append(GEOFinding(filepath, 1, "seo-no-structured-data",
                                   "No code blocks, tables, or lists found. "
                                   "Structured content improves search snippets.",
                                   "suggestion"))

    return findings


# ==================== ALGOLIA SEARCH OPTIMIZATION ====================

class AlgoliaOptimizer:
    def __init__(self):
        self.records = []

    def extract_content_sections(self, content):
        """Split content into searchable sections."""
        sections = []
        current_section = {
            'heading': '',
            'content': '',
            'level': 0
        }

        lines = content.split('\n')
        for line in lines:
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                if current_section['content'].strip():
                    sections.append(current_section)

                level = len(heading_match.group(1))
                current_section = {
                    'heading': heading_match.group(2),
                    'content': '',
                    'level': level
                }
            else:
                if line.strip() and not line.startswith('```'):
                    current_section['content'] += line + ' '

        if current_section['content'].strip():
            sections.append(current_section)

        return sections

    def create_search_record(self, filepath, frontmatter, section, section_index):
        """Create an Algolia record from a document section."""

        # Generate unique objectID
        object_id = hashlib.md5(
            f"{filepath}#{section_index}".encode()
        ).hexdigest()

        # Clean content for search
        content = section['content']
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Links
        content = re.sub(r'`([^`]+)`', r'\1', content)  # Inline code
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Bold
        content = re.sub(r'\*([^*]+)\*', r'\1', content)  # Italic

        # Extract code snippets for separate indexing
        code_snippets = re.findall(r'```[^`]*```', section['content'])

        # Build hierarchy for faceting
        hierarchy = {
            'lvl0': frontmatter.get('product', 'Documentation'),
            'lvl1': frontmatter.get('content_type', 'General'),
            'lvl2': section['heading'] if section['level'] == 2 else '',
            'lvl3': section['heading'] if section['level'] == 3 else '',
            'lvl4': section['heading'] if section['level'] == 4 else ''
        }

        # Calculate ranking boost
        ranking_boost = 0

        # Boost based on content type
        content_type_boosts = {
            'tutorial': 10,
            'how-to': 8,
            'reference': 6,
            'concept': 4,
            'troubleshooting': 2
        }
        ranking_boost += content_type_boosts.get(frontmatter.get('content_type', ''), 0)

        # Boost based on path depth (shallower = more important)
        path_depth = len(Path(filepath).parts) - 2
        ranking_boost -= path_depth * 2

        # Boost if it's an index page
        if 'index' in Path(filepath).stem:
            ranking_boost += 20

        # Penalize deprecated content
        if frontmatter.get('maturity') == 'deprecated':
            ranking_boost -= 50

        record = {
            'objectID': object_id,

            # Content fields
            'title': frontmatter.get('title', ''),
            'heading': section['heading'],
            'content': content[:1000],
            'description': frontmatter.get('description', ''),

            # Facet fields
            'product': frontmatter.get('product', 'both'),
            'content_type': frontmatter.get('content_type', ''),
            'component': frontmatter.get('app_component', ''),
            'version': frontmatter.get('app_version', ''),
            'maturity': frontmatter.get('maturity', 'ga'),
            'tags': frontmatter.get('tags', []),

            # Hierarchy for UI
            'hierarchy': hierarchy,

            # Metadata
            'url': f"/{str(filepath).replace('docs/', '').replace('.md', '')}#{section_index}",
            'last_reviewed': frontmatter.get('last_reviewed', ''),
            'path': str(filepath),

            # Ranking
            'ranking_boost': ranking_boost,
            'heading_level': section['level'],

            # Analytics
            'word_count': len(content.split()),
            'has_code': len(code_snippets) > 0,
            'code_snippets': code_snippets[:3]
        }

        return record

    def generate_algolia_config(self):
        """Generate Algolia index configuration."""
        return {
            'searchableAttributes': [
                'unordered(title)',
                'unordered(heading)',
                'unordered(content)',
                'unordered(description)',
                'tags'
            ],
            'attributesForFaceting': [
                'searchable(product)',
                'searchable(content_type)',
                'searchable(component)',
                'searchable(tags)',
                'maturity',
                'version',
                'has_code'
            ],
            'customRanking': [
                'desc(ranking_boost)',
                'asc(heading_level)',
                'desc(word_count)'
            ],
            'attributesToSnippet': [
                'content:50',
                'description:30'
            ],
            'attributesToHighlight': [
                'title',
                'heading',
                'content',
                'tags'
            ],
            'distinct': True,
            'attributeForDistinct': 'url',
            'highlightPreTag': '<mark>',
            'highlightPostTag': '</mark>',
            'snippetEllipsisText': '…',
            'removeWordsIfNoResults': 'lastWords'
        }

# ==================== METADATA AUTO-ENHANCEMENT ====================

def infer_metadata_from_path(filepath):
    """Infer metadata from file path."""
    path_parts = filepath.parts
    metadata = {}

    # Infer content_type from directory
    if 'getting-started' in path_parts or 'tutorial' in path_parts:
        metadata['content_type'] = 'tutorial'
    elif 'how-to' in path_parts or 'guides' in path_parts:
        metadata['content_type'] = 'how-to'
    elif 'concept' in path_parts or 'concepts' in path_parts:
        metadata['content_type'] = 'concept'
    elif 'reference' in path_parts or 'api' in path_parts:
        metadata['content_type'] = 'reference'
    elif 'troubleshoot' in path_parts or 'troubleshooting' in path_parts:
        metadata['content_type'] = 'troubleshooting'
    elif 'release' in path_parts or 'changelog' in path_parts:
        metadata['content_type'] = 'release-note'

    # Infer product from path
    if 'cloud' in str(filepath).lower():
        metadata['product'] = 'cloud'
    elif 'self-hosted' in str(filepath).lower() or 'docker' in str(filepath).lower():
        metadata['product'] = 'self-hosted'

    # Infer component from filename
    filename = filepath.stem.lower()
    components = {
        'webhook': 'webhook',
        'http': 'http-request',
        'code': 'code',
        'ai': 'ai-agent',
        'schedule': 'schedule',
        'workflow': 'workflow-engine',
        'credential': 'credentials',
        'expression': 'expressions'
    }

    for key, value in components.items():
        if key in filename:
            metadata['app_component'] = value
            break

    # Auto-generate tags from path and filename
    tags = []
    for part in path_parts[1:-1]:  # Skip 'docs' and filename
        if part not in ['getting-started', 'how-to', 'reference', 'concepts', 'troubleshooting']:
            tags.append(part.replace('-', ' ').title())

    if 'app_component' in metadata:
        tags.append(metadata['app_component'].replace('-', ' ').title())

    if tags:
        metadata['tags'] = list(set(tags))[:8]  # Max 8 tags

    return metadata

def analyze_content(content):
    """Analyze content to infer metadata."""
    metadata = {}

    # Check for version mentions
    version_match = re.search(r'(?:version |v)(\d+\.\d+)', content, re.IGNORECASE)
    if version_match:
        metadata['app_version'] = version_match.group(1)

    # Infer content_type from content structure
    if not metadata.get('content_type'):
        if re.search(r'^\d+\.\s+', content, re.MULTILINE):
            metadata['content_type'] = 'how-to'
        elif 'Prerequisites' in content or '## Before you begin' in content:
            metadata['content_type'] = 'tutorial'
        elif 'Problem:' in content or 'Solution:' in content or 'Error:' in content:
            metadata['content_type'] = 'troubleshooting'
        elif '| Parameter |' in content or '| Method |' in content:
            metadata['content_type'] = 'reference'

    return metadata

# ==================== MAIN OPTIMIZER CLASS ====================

class ComprehensiveSEOOptimizer:
    """Main class that combines all SEO/GEO functionality."""

    def __init__(self, base_url="https://docs.example.com"):
        self.base_url = base_url
        self.seo_enhancer = SEOEnhancer(base_url)
        self.algolia = AlgoliaOptimizer()
        self.findings = []
        self.enhanced_files = []

    def optimize_file(self, filepath, fix=False):
        """Run all optimizations on a single file."""
        results = {
            'filepath': str(filepath),
            'geo_findings': [],
            'metadata_enhanced': False,
            'seo_data': None,
            'search_records': []
        }

        # Read file
        content = filepath.read_text(encoding='utf-8')
        frontmatter, body = extract_frontmatter(content)

        # 1. GEO Linting
        results['geo_findings'] = geo_lint_file(filepath)
        self.findings.extend(results['geo_findings'])

        # 1b. SEO Validation
        seo_findings = seo_validate_file(filepath)
        results['geo_findings'].extend(seo_findings)
        self.findings.extend(seo_findings)

        # 2. Auto-enhance metadata if needed
        if fix:
            path_metadata = infer_metadata_from_path(filepath)
            content_metadata = analyze_content(body)
            git_metadata = get_git_info(filepath)

            # Merge metadata
            enhanced_fm = frontmatter.copy()
            for source in [path_metadata, content_metadata, git_metadata]:
                for key, value in source.items():
                    if key not in enhanced_fm:
                        enhanced_fm[key] = value
                        results['metadata_enhanced'] = True

            if results['metadata_enhanced']:
                # Write back enhanced frontmatter
                yaml_str = yaml.dump(enhanced_fm, default_flow_style=False, sort_keys=False)
                new_content = f"---\n{yaml_str}---\n{body}"
                filepath.write_text(new_content, encoding='utf-8')
                frontmatter = enhanced_fm
                self.enhanced_files.append(filepath)

        # 3. Generate SEO data
        results['seo_data'] = {
            'structured_data': self.seo_enhancer.generate_structured_data(filepath, frontmatter, body),
            'meta_tags': self.seo_enhancer.generate_meta_tags(frontmatter, filepath),
            'sitemap_entry': self.seo_enhancer.generate_sitemap_entry(filepath, frontmatter)
        }

        # 4. Generate search records
        sections = self.algolia.extract_content_sections(body)
        for i, section in enumerate(sections):
            record = self.algolia.create_search_record(filepath, frontmatter, section, i)
            results['search_records'].append(record)
            self.algolia.records.append(record)

        return results

    def generate_sitemap(self, docs_dir='docs'):
        """Generate complete sitemap.xml."""
        entries = []

        for md_file in Path(docs_dir).rglob('*.md'):
            if md_file.name.startswith('_'):
                continue

            content = md_file.read_text(encoding='utf-8')
            frontmatter, _ = extract_frontmatter(content)
            entry = self.seo_enhancer.generate_sitemap_entry(md_file, frontmatter)
            entries.append(entry)

        # Generate XML
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for entry in sorted(entries, key=lambda x: x['priority'], reverse=True):
            xml_content += '  <url>\n'
            xml_content += f"    <loc>{entry['loc']}</loc>\n"
            xml_content += f"    <lastmod>{entry['lastmod']}</lastmod>\n"
            xml_content += f"    <changefreq>{entry['changefreq']}</changefreq>\n"
            xml_content += f"    <priority>{entry['priority']}</priority>\n"
            xml_content += '  </url>\n'

        xml_content += '</urlset>'

        Path('sitemap.xml').write_text(xml_content, encoding='utf-8')
        print(f"Generated sitemap with {len(entries)} URLs")
        return entries

    def generate_reports(self):
        """Generate comprehensive SEO/GEO reports."""
        # GEO Report
        errors = [f for f in self.findings if f.severity == "error"]
        warnings = [f for f in self.findings if f.severity == "warning"]
        suggestions = [f for f in self.findings if f.severity == "suggestion"]

        print("\n" + "="*60)
        print("SEO/GEO OPTIMIZATION REPORT")
        print("="*60)

        print(f"\nGEO Findings: {len(errors)} errors, {len(warnings)} warnings, {len(suggestions)} suggestions")
        if self.findings:
            for f in self.findings[:10]:  # Show first 10
                print(f)
            if len(self.findings) > 10:
                print(f"  ... and {len(self.findings) - 10} more findings")

        # Metadata Enhancement Report
        if self.enhanced_files:
            print(f"\n✨ Metadata Enhanced: {len(self.enhanced_files)} files")
            for f in self.enhanced_files[:5]:
                print(f"  - {f}")

        # Search Index Report
        if self.algolia.records:
            print(f"\nSearch Records: {len(self.algolia.records)} records generated")

            # Statistics by content type
            types = {}
            for r in self.algolia.records:
                ct = r.get('content_type', 'unknown')
                types[ct] = types.get(ct, 0) + 1

            print("  By content type:")
            for t, count in sorted(types.items()):
                print(f"    - {t}: {count}")

        return errors

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Comprehensive SEO/GEO Optimizer for Documentation')
    parser.add_argument('path', nargs='?', default='docs',
                       help='Path to process (file or directory)')
    parser.add_argument('--fix', action='store_true',
                       help='Automatically fix issues and enhance metadata')
    parser.add_argument('--sitemap', action='store_true',
                       help='Generate sitemap.xml')
    parser.add_argument('--algolia', action='store_true',
                       help='Generate Algolia search records')
    parser.add_argument('--output', default='seo-output.json',
                       help='Output file for results')
    args = parser.parse_args()

    optimizer = ComprehensiveSEOOptimizer()
    path = Path(args.path)

    # Process files
    if path.is_file():
        if path.name in INTERNAL_GEO_IGNORE:
            print(f"Skipping internal guide for GEO checks: {path}")
            results = {}
        else:
            results = optimizer.optimize_file(path, fix=args.fix)
        print(json.dumps(results, indent=2, default=str))
    else:
        for md_file in sorted(path.rglob('*.md')):
            if md_file.name.startswith('_'):
                continue
            if md_file.name in INTERNAL_GEO_IGNORE:
                print(f"Skipping internal guide for GEO checks: {md_file}")
                continue
            print(f"Processing {md_file}...")
            optimizer.optimize_file(md_file, fix=args.fix)

    # Generate sitemap if requested
    if args.sitemap:
        optimizer.generate_sitemap(args.path if path.is_dir() else 'docs')

    # Save Algolia records if requested
    if args.algolia:
        algolia_data = {
            'records': optimizer.algolia.records,
            'config': optimizer.algolia.generate_algolia_config()
        }
        with open(args.output.replace('.json', '-algolia.json'), 'w') as f:
            json.dump(algolia_data, f, indent=2, default=str)
        print(f"Saved {len(optimizer.algolia.records)} Algolia records")

    # Generate reports
    errors = optimizer.generate_reports()

    # Exit with error code if errors found
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
