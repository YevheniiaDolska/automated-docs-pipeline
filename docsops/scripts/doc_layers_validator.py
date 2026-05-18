#!/usr/bin/env python3
"""
Documentation Layers Validator
Ensures documentation follows proper abstraction layers (inspired by BDR methodology).
"""

import argparse
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List
import re
from datetime import datetime
from yaml import YAMLError


IGNORED_LAYER_PATH_MARKERS = ("docs/reference/intent-experiences/",)


def _should_skip_layer_validation(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    return any(marker in normalized for marker in IGNORED_LAYER_PATH_MARKERS)


class DocLayersValidator:
    """
    Validates that documentation maintains proper abstraction layers:
    1. Domain/Concepts - High-level understanding
    2. Tasks/How-to - Business workflows
    3. Reference - Technical implementation details
    """

    def __init__(self, docs_dir: str = "docs", policy_pack_path: str | None = None):
        self.docs_dir = Path(docs_dir)
        self.layer_violations = []
        self.required_layers = self._load_required_layers(policy_pack_path)
        self.feature_key_fields = (
            "feature_id",
            "feature",
            "component",
            "capability",
            "topic",
            "api_group",
        )

    def _load_required_layers(self, policy_pack_path: str | None) -> tuple[str, ...]:
        """Load required doc layers from policy pack, fallback to disabled coverage check."""
        default_layers: tuple[str, ...] = ()
        if not policy_pack_path:
            return default_layers

        path = Path(policy_pack_path)
        if not path.exists():
            return default_layers

        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except YAMLError:
            return default_layers

        if not isinstance(payload, dict):
            return default_layers

        section = payload.get("doc_layers", {})
        if not isinstance(section, dict):
            return default_layers

        raw_layers = section.get("required_layers") or section.get("required_content_layers")
        if not isinstance(raw_layers, list):
            return default_layers

        layers = tuple(
            str(item).strip().lower()
            for item in raw_layers
            if isinstance(item, str) and str(item).strip()
        )
        return layers if layers else default_layers

    def extract_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract frontmatter as mapping."""
        if not content.startswith("---"):
            return {}
        try:
            parts = content.split("---", 2)
            if len(parts) >= 2:
                fm = yaml.safe_load(parts[1])
                if isinstance(fm, dict):
                    return fm
        except (YAMLError, AttributeError, TypeError):
            return {}
        return {}

    def detect_layer_violations(self) -> List[Dict]:
        """Find documents that mix abstraction layers inappropriately."""
        violations = []
        feature_layers: dict[str, set[str]] = {}

        for md_file in self.docs_dir.rglob("*.md"):
            if _should_skip_layer_validation(md_file):
                continue
            content = md_file.read_text(encoding='utf-8')
            frontmatter = self.extract_frontmatter(content)

            # Extract frontmatter to determine intended layer
            content_type = self.extract_content_type(content)

            if content_type:
                issues = self.check_layer_consistency(content, content_type, md_file)
                violations.extend(issues)
                feature_key = self.extract_feature_key(md_file, frontmatter, content_type)
                feature_layers.setdefault(feature_key, set()).add(content_type)

        if feature_layers and self.required_layers:
            missing = self.detect_missing_required_layers(feature_layers)
            violations.extend(missing)

        return violations

    def extract_content_type(self, content: str) -> str:
        """Extract content_type from frontmatter."""
        if content.startswith("---"):
            try:
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    fm = yaml.safe_load(parts[1])
                    return fm.get("content_type", "")
            except (YAMLError, AttributeError, TypeError):
                return ""
        return ""

    def extract_feature_key(self, file_path: Path, frontmatter: dict[str, Any], content_type: str) -> str:
        """Infer feature key to group docs into concept/how-to/reference sets."""
        for key in self.feature_key_fields:
            value = frontmatter.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()

        title = frontmatter.get("title")
        if isinstance(title, str) and title.strip():
            normalized = re.sub(r"\s+", "-", title.strip().lower())
            normalized = re.sub(r"[^a-z0-9\-_/]", "", normalized)
            if normalized:
                return normalized

        stem = file_path.stem.lower()
        suffix_patterns = (
            "-concept",
            "-how-to",
            "-reference",
            "_concept",
            "_how_to",
            "_reference",
            "-tutorial",
            "_tutorial",
            "-troubleshooting",
            "_troubleshooting",
        )
        for suffix in suffix_patterns:
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        return stem or content_type

    def detect_missing_required_layers(self, feature_layers: dict[str, set[str]]) -> List[Dict]:
        """Report features missing required layers from active policy pack."""
        missing: List[Dict] = []
        required = set(self.required_layers)
        for feature, seen_layers in sorted(feature_layers.items()):
            absent = sorted(required - seen_layers)
            if not absent:
                continue
            missing.append(
                {
                    "file": feature,
                    "content_type": "feature",
                    "violation": f"Missing required layers: {', '.join(absent)}",
                    "recommendation": (
                        "Add missing layer docs for this feature "
                        f"(required by policy pack: {', '.join(self.required_layers)})."
                    ),
                    "missing_layers": absent,
                    "present_layers": sorted(seen_layers),
                }
            )
        return missing

    def check_layer_consistency(self, content: str, content_type: str, file_path: Path) -> List[Dict]:
        """Check if content matches its declared type."""
        violations = []

        # Define what shouldn't appear in each layer
        layer_rules = {
            "concept": {
                "should_not_have": [
                    r'```[a-z]+\n.*?\n```',  # Code blocks in concepts should be minimal
                    r'Step \d+:',  # Step-by-step instructions don't belong in concepts
                    r'Click on',  # UI instructions don't belong in concepts
                    r'Run the following command',  # Commands don't belong in concepts
                ],
                "warning": "Concept documentation should explain 'what' and 'why', not 'how'"
            },
            "tutorial": {
                "should_not_have": [
                    r'interface\s+\w+\s*{',  # API interfaces too technical for tutorials
                    r'class\s+\w+\s*{',  # Class definitions too technical
                ],
                "warning": "Tutorials should focus on learning journey, not technical specs"
            },
            "how-to": {
                "should_not_have": [
                    r'In this tutorial',  # How-to is task-focused, not learning-focused
                    r'theory behind',  # Theory belongs in concepts
                ],
                "warning": "How-to guides should be task-oriented, not educational"
            },
            "reference": {
                "should_not_have": [
                    r'In this tutorial',  # Reference is not tutorial
                    r'Let\'s explore',  # Reference should be direct, not exploratory
                    r'why you might',  # Reference documents 'what is', not 'why'
                ],
                "warning": "Reference documentation should be factual and precise"
            }
        }

        if content_type in layer_rules:
            rules = layer_rules[content_type]

            for pattern in rules["should_not_have"]:
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    violations.append({
                        "file": str(file_path.relative_to(self.docs_dir)),
                        "content_type": content_type,
                        "violation": f"Contains pattern inappropriate for {content_type}",
                        "pattern": pattern[:50],  # First 50 chars of pattern
                        "occurrences": len(matches),
                        "recommendation": rules["warning"]
                    })

        # Check for mixing business and technical layers
        has_business_terms = bool(re.search(r'(workflow|process|business|user journey)', content, re.I))
        has_technical_details = bool(re.search(r'(implementation|algorithm|data structure|complexity)', content, re.I))

        if content_type in ["tutorial", "how-to"] and has_technical_details and not has_business_terms:
            violations.append({
                "file": str(file_path.relative_to(self.docs_dir)),
                "content_type": content_type,
                "violation": "Too technical, lacks business context",
                "recommendation": "Add business context or move technical details to reference docs"
            })

        return violations

    def generate_report(self) -> str:
        """Generate HTML report of layer violations."""
        violations = self.detect_layer_violations()

        # Group by content type
        by_type = {}
        for v in violations:
            ct = v["content_type"]
            if ct not in by_type:
                by_type[ct] = []
            by_type[ct].append(v)

        if violations:
            violation_blocks = []
            for content_type, items in by_type.items():
                item_blocks = []
                for item in items:
                    item_blocks.append(
                        f"""
        <div class="violation-item">
            <div class="file-name">{item['file']}</div>
            <div>{item['violation']}</div>
            <div class="recommendation">Tip: {item['recommendation']}</div>
        </div>
                        """.strip()
                    )
                violation_blocks.append(
                    f"""
    <div class="violations">
        <h2>{content_type.title()} Documents - {len(items)} violations</h2>
        {''.join(item_blocks)}
    </div>
                    """.strip()
                )
            violations_html = ''.join(violation_blocks)
        else:
            violations_html = (
                '<div class="violations"><h2>No layer violations found!</h2>'
                '<p>All documents maintain proper abstraction levels.</p></div>'
            )

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Documentation Layers Validation Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .layer-diagram {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .layer {{
            display: inline-block;
            padding: 15px 30px;
            margin: 10px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .layer.concept {{ background: #3498db; color: white; }}
        .layer.tutorial {{ background: #2ecc71; color: white; }}
        .layer.how-to {{ background: #f39c12; color: white; }}
        .layer.reference {{ background: #e74c3c; color: white; }}
        .violations {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .violation-item {{
            padding: 15px;
            border-left: 4px solid #e74c3c;
            background: #fff5f5;
            margin-bottom: 10px;
            border-radius: 5px;
        }}
        .file-name {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .recommendation {{
            color: #7f8c8d;
            font-style: italic;
            margin-top: 5px;
        }}
        h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Documentation Layers Validation</h1>
        <p>Ensuring proper abstraction and separation of concerns</p>
        <p>{datetime.now().strftime("%B %d, %Y")}</p>
    </div>

    <div class="layer-diagram">
        <h2>Proper Documentation Layers</h2>
        <div>
            <div class="layer concept">Concepts (What/Why)</div>
            →
            <div class="layer tutorial">Tutorials (Learning)</div>
            →
            <div class="layer how-to">How-to (Tasks)</div>
            →
            <div class="layer reference">Reference (Specs)</div>
        </div>
        <p style="color: #7f8c8d; margin-top: 20px;">
            Each layer should maintain its abstraction level without bleeding into others
        </p>
    </div>

    <div class="summary">
        <div class="metric">
            <h3>Total Violations</h3>
            <div style="font-size: 2em; font-weight: bold; color: #e74c3c;">{len(violations)}</div>
        </div>
        <div class="metric">
            <h3>Files Affected</h3>
            <div style="font-size: 2em; font-weight: bold; color: #f39c12;">{len(set(v['file'] for v in violations))}</div>
        </div>
    </div>

    {violations_html}

    <div class="violations">
        <h2>Recommendations</h2>
        <ul>
            <li><strong>Concepts:</strong> Focus on explaining what something is and why it exists</li>
            <li><strong>Tutorials:</strong> Guide learners through their first experience</li>
            <li><strong>How-to:</strong> Provide step-by-step instructions for specific tasks</li>
            <li><strong>Reference:</strong> Document technical specifications and APIs</li>
        </ul>
        <p>Each document type should stay within its layer to maintain clarity and purpose.</p>
    </div>
</body>
</html>"""
        return html

    def save_report(self, output_path: str = "doc_layers_report.html"):
        """Save the layers validation report."""
        report = self.generate_report()
        Path(output_path).write_text(report)
        print(f"Documentation layers report saved to: {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Validate documentation abstraction layers")
    parser.add_argument("--docs-dir", default="docs", help="Docs directory to scan")
    parser.add_argument(
        "--policy-pack",
        default=None,
        help="Optional policy pack path. If omitted, defaults are used.",
    )
    parser.add_argument(
        "--output",
        default="doc_layers_report.html",
        help="HTML report path",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional JSON output path for violations",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if any violation is found",
    )
    args = parser.parse_args()

    validator = DocLayersValidator(docs_dir=args.docs_dir, policy_pack_path=args.policy_pack)
    violations = validator.detect_layer_violations()
    validator.save_report(args.output)

    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "required_layers": list(validator.required_layers),
                    "violations_count": len(violations),
                    "violations": violations,
                },
                ensure_ascii=True,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    if args.strict and violations:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
