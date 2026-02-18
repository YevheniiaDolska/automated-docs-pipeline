#!/usr/bin/env python3
"""
Documentation Layers Validator
Ensures documentation follows proper abstraction layers (inspired by BDR methodology).
"""

import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import re
from datetime import datetime
from yaml import YAMLError

class DocLayersValidator:
    """
    Validates that documentation maintains proper abstraction layers:
    1. Domain/Concepts - High-level understanding
    2. Tasks/How-to - Business workflows
    3. Reference - Technical implementation details
    """

    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.layer_violations = []

    def detect_layer_violations(self) -> List[Dict]:
        """Find documents that mix abstraction layers inappropriately."""
        violations = []

        for md_file in self.docs_dir.rglob("*.md"):
            content = md_file.read_text(encoding='utf-8')

            # Extract frontmatter to determine intended layer
            content_type = self.extract_content_type(content)

            if content_type:
                issues = self.check_layer_consistency(content, content_type, md_file)
                violations.extend(issues)

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
    validator = DocLayersValidator()
    validator.save_report()

if __name__ == "__main__":
    main()
