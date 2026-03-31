#!/usr/bin/env python3
"""RAG-based test generation from existing client test codebase.

Inspired by Sberbank's RAG+LLM approach for test automation.
Scans a project for existing tests and step functions, builds a semantic
index, then uses retrieval-augmented generation to create new tests
matching the project's conventions.

Supported test frameworks: pytest, unittest, Allure steps.

Usage:
  # Index existing tests
  python3 scripts/generate_tests_from_rag.py index \
    --source-dir tests/ \
    --index-file reports/test-rag-index.json

  # Generate new tests from descriptions
  python3 scripts/generate_tests_from_rag.py generate \
    --index-file reports/test-rag-index.json \
    --descriptions reports/test-descriptions.yml \
    --output-dir generated/tests

  # One-shot: describe what to test, get a test file
  python3 scripts/generate_tests_from_rag.py generate \
    --index-file reports/test-rag-index.json \
    --query "Test that webhook retry logic backs off exponentially" \
    --output-dir generated/tests
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import textwrap
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class CodeRecord:
    """A single indexed test or step function."""

    id: str
    file_path: str
    function_name: str
    class_name: str
    source_code: str
    docstring: str
    decorators: list[str]
    imports: list[str]
    description: str  # LLM-generated or extracted summary
    category: str  # "test" | "step" | "fixture" | "helper"
    framework: str  # "pytest" | "unittest" | "allure"
    signature: str  # SHA-256 of source_code
    line_number: int = 0
    tags: list[str] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)


@dataclass
class CodeIndex:
    """Collection of indexed test records."""

    records: list[CodeRecord]
    source_dirs: list[str]
    total_files_scanned: int = 0
    total_functions_indexed: int = 0
    framework_stats: dict[str, int] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """A request to generate a test."""

    description: str
    target_module: str = ""
    test_type: str = "unit"  # unit | integration | api | e2e
    framework: str = "pytest"
    tags: list[str] = field(default_factory=list)


@dataclass
class GeneratedTest:
    """A generated test result."""

    description: str
    source_code: str
    file_name: str
    similar_tests: list[str]
    confidence: float = 0.0
    validation_status: str = "pending"
    validation_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# AST-based test code scanner
# ---------------------------------------------------------------------------


def _extract_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    decorators: list[str] = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(ast.dump(dec))
        elif isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name):
                decorators.append(func.id)
            elif isinstance(func, ast.Attribute):
                parts = []
                node_inner = func
                while isinstance(node_inner, ast.Attribute):
                    parts.append(node_inner.attr)
                    node_inner = node_inner.value
                if isinstance(node_inner, ast.Name):
                    parts.append(node_inner.id)
                decorators.append(".".join(reversed(parts)))
    return decorators


def _extract_imports(tree: ast.Module) -> list[str]:
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}" if module else alias.name)
    return imports


def _classify_function(
    name: str,
    decorators: list[str],
    class_name: str,
) -> tuple[str, str]:
    """Classify function as test/step/fixture/helper and detect framework."""
    dec_str = " ".join(decorators).lower()

    # Allure steps
    if "allure.step" in dec_str or "step" in dec_str:
        return "step", "allure"

    # pytest fixtures
    if "fixture" in dec_str or "pytest.fixture" in dec_str:
        return "fixture", "pytest"

    # pytest parametrize or marks
    if "pytest.mark" in dec_str or "parametrize" in dec_str:
        return "test", "pytest"

    # Test methods
    if name.startswith("test_") or name.startswith("test"):
        if class_name and class_name.startswith("Test"):
            # Could be pytest class or unittest
            if any("unittest" in d for d in decorators):
                return "test", "unittest"
            return "test", "pytest"
        return "test", "pytest"

    # unittest setUp/tearDown
    if name in {"setUp", "tearDown", "setUpClass", "tearDownClass"}:
        return "fixture", "unittest"

    return "helper", "unknown"


def _generate_description(
    name: str,
    docstring: str,
    category: str,
    source_code: str,
) -> str:
    """Generate a human-readable description from function metadata."""
    if docstring:
        # Use first line of docstring
        first_line = docstring.strip().split("\n")[0].strip()
        if len(first_line) > 20:
            return first_line

    # Generate from function name
    words = name.replace("test_", "").replace("_", " ").strip()
    if category == "test":
        return f"Test that {words}"
    if category == "step":
        return f"Step: {words}"
    if category == "fixture":
        return f"Fixture: {words}"
    return f"Helper: {words}"


def scan_python_file(file_path: Path, base_dir: Path) -> list[CodeRecord]:
    """Extract test records from a single Python file."""
    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    imports = _extract_imports(tree)
    rel_path = str(file_path.relative_to(base_dir))
    records: list[CodeRecord] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        # Determine class context
        class_name = ""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                for child in ast.iter_child_nodes(parent):
                    if child is node:
                        class_name = parent.name
                        break

        decorators = _extract_decorators(node)
        category, framework = _classify_function(node.name, decorators, class_name)

        # Skip non-interesting functions
        if category == "helper" and not node.name.startswith("_step"):
            continue

        # Extract source code for this function
        try:
            func_source = ast.get_source_segment(source, node) or ""
        except (RuntimeError, ValueError, TypeError, OSError):
            func_source = ""

        if not func_source:
            # Fallback: extract by line numbers
            lines = source.splitlines()
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
            func_source = "\n".join(lines[start:end])

        docstring = ast.get_docstring(node) or ""
        description = _generate_description(node.name, docstring, category, func_source)
        sig = hashlib.sha256(func_source.encode("utf-8")).hexdigest()[:16]

        record_id = f"{rel_path}::{class_name}::{node.name}" if class_name else f"{rel_path}::{node.name}"

        records.append(
            CodeRecord(
                id=record_id,
                file_path=rel_path,
                function_name=node.name,
                class_name=class_name,
                source_code=func_source,
                docstring=docstring,
                decorators=decorators,
                imports=imports,
                description=description,
                category=category,
                framework=framework,
                signature=sig,
                line_number=node.lineno,
                tags=[],
            )
        )

    return records


def scan_directory(source_dir: Path) -> CodeIndex:
    """Scan a directory tree for Python test files and index them."""
    records: list[CodeRecord] = []
    files_scanned = 0
    framework_stats: dict[str, int] = {}

    for py_file in sorted(source_dir.rglob("*.py")):
        # Skip obvious non-test directories
        rel = py_file.relative_to(source_dir)
        parts = rel.parts
        if any(p.startswith(".") or p in {"__pycache__", "node_modules", ".git", "venv", "env"} for p in parts):
            continue

        files_scanned += 1
        file_records = scan_python_file(py_file, source_dir)
        for rec in file_records:
            framework_stats[rec.framework] = framework_stats.get(rec.framework, 0) + 1
        records.extend(file_records)

    return CodeIndex(
        records=records,
        source_dirs=[str(source_dir)],
        total_files_scanned=files_scanned,
        total_functions_indexed=len(records),
        framework_stats=framework_stats,
    )


# ---------------------------------------------------------------------------
# Token-overlap retrieval (no embeddings needed)
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    """Simple word tokenization for overlap scoring."""
    return set(re.findall(r"[a-z_][a-z0-9_]*", text.lower()))


def retrieve_similar(
    query: str,
    index: CodeIndex,
    top_k: int = 5,
    category_filter: str | None = None,
) -> list[tuple[CodeRecord, float]]:
    """Find the most similar test records using token overlap."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored: list[tuple[CodeRecord, float]] = []
    for rec in index.records:
        if category_filter and rec.category != category_filter:
            continue

        # Build searchable text from record
        rec_text = f"{rec.description} {rec.function_name} {rec.docstring} {rec.class_name}"
        rec_tokens = _tokenize(rec_text)

        if not rec_tokens:
            continue

        # Jaccard-like overlap score
        overlap = len(query_tokens & rec_tokens)
        union = len(query_tokens | rec_tokens)
        score = overlap / union if union > 0 else 0.0

        # Boost tests over helpers
        if rec.category == "test":
            score *= 1.2
        elif rec.category == "step":
            score *= 1.1

        if score > 0:
            scored.append((rec, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_generation_prompt(
    request: GenerationRequest,
    similar_records: list[tuple[CodeRecord, float]],
) -> str:
    """Build a prompt for test generation using retrieved examples."""
    examples_block = ""
    if similar_records:
        example_parts: list[str] = []
        for i, (rec, score) in enumerate(similar_records[:3], 1):
            example_parts.append(
                f"--- Example {i} (similarity: {score:.2f}) ---\n"
                f"# Description: {rec.description}\n"
                f"# File: {rec.file_path}\n"
                f"# Framework: {rec.framework}\n"
                f"{rec.source_code}\n"
            )
        examples_block = "\n".join(example_parts)

    # Collect unique imports from similar records
    all_imports: list[str] = []
    for rec, _ in similar_records[:3]:
        for imp in rec.imports:
            if imp not in all_imports:
                all_imports.append(imp)
    imports_hint = "\n".join(f"# - {imp}" for imp in all_imports[:10]) if all_imports else "# (no imports context)"

    prompt = f"""\
You are a test automation engineer. Generate a Python test function based on the
description below. Follow the project's existing test conventions shown in the
examples.

## Test Description
{request.description}

## Target Module
{request.target_module or '(not specified)'}

## Test Type
{request.test_type}

## Framework
{request.framework}

## Project Import Context
{imports_hint}

## Similar Existing Tests (use as style reference)
{examples_block if examples_block else '(no similar tests found)'}

## Requirements
1. Use the same framework and patterns as the examples above.
2. Include realistic test data (not "foo", "bar", "test123").
3. Include docstring explaining what the test verifies.
4. Handle both success and error cases where applicable.
5. Use descriptive function names starting with test_.
6. Include necessary imports at the top.
7. Use pytest fixtures if the examples use them.
8. Do NOT use emoji or special Unicode characters.

## Output
Return ONLY valid Python code. No markdown fences, no explanations.
"""
    return prompt


# ---------------------------------------------------------------------------
# Test validation
# ---------------------------------------------------------------------------


def validate_generated_test(source_code: str) -> tuple[bool, list[str]]:
    """Validate generated test code for syntax and basic correctness."""
    errors: list[str] = []

    # Check syntax
    try:
        tree = ast.parse(source_code)
    except SyntaxError as exc:
        errors.append(f"Syntax error: {exc}")
        return False, errors

    # Check that at least one test function exists
    test_funcs = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not test_funcs:
        errors.append("No test function (test_*) found in generated code")

    # Check for import statements
    has_imports = any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        for node in ast.walk(tree)
    )
    if not has_imports:
        errors.append("No import statements found")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# Index serialization
# ---------------------------------------------------------------------------


def save_index(index: CodeIndex, output_path: Path) -> None:
    """Save index to JSON file."""
    data = {
        "source_dirs": index.source_dirs,
        "total_files_scanned": index.total_files_scanned,
        "total_functions_indexed": index.total_functions_indexed,
        "framework_stats": index.framework_stats,
        "records": [asdict(r) for r in index.records],
    }
    # Strip embeddings to keep file small
    for rec in data["records"]:
        rec.pop("embedding", None)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_index(index_path: Path) -> CodeIndex:
    """Load index from JSON file."""
    data = json.loads(index_path.read_text(encoding="utf-8"))
    records = [CodeRecord(**r) for r in data.get("records", [])]
    return CodeIndex(
        records=records,
        source_dirs=data.get("source_dirs", []),
        total_files_scanned=data.get("total_files_scanned", 0),
        total_functions_indexed=data.get("total_functions_indexed", 0),
        framework_stats=data.get("framework_stats", {}),
    )


# ---------------------------------------------------------------------------
# Generation orchestrator
# ---------------------------------------------------------------------------


def generate_test_from_description(
    description: str,
    index: CodeIndex,
    target_module: str = "",
    test_type: str = "unit",
    framework: str = "pytest",
    top_k: int = 3,
) -> GeneratedTest:
    """Generate a test using RAG: retrieve similar tests, build prompt, return result.

    Note: actual LLM call is not made here -- the prompt is returned as source_code
    so the caller (or LLM agent) can execute it. When an LLM API key is available,
    this function can be extended to call the model directly.
    """
    request = GenerationRequest(
        description=description,
        target_module=target_module,
        test_type=test_type,
        framework=framework,
    )

    similar = retrieve_similar(description, index, top_k=top_k, category_filter="test")
    if not similar:
        similar = retrieve_similar(description, index, top_k=top_k)

    prompt = build_generation_prompt(request, similar)
    similar_ids = [rec.id for rec, _ in similar]

    # File name from description
    slug = re.sub(r"[^a-z0-9]+", "_", description.lower().strip())[:60].strip("_")
    file_name = f"test_{slug}.py"

    return GeneratedTest(
        description=description,
        source_code=prompt,  # The prompt serves as the generation instruction
        file_name=file_name,
        similar_tests=similar_ids,
        confidence=similar[0][1] if similar else 0.0,
        validation_status="prompt_ready",
    )


def batch_generate(
    descriptions_path: Path,
    index: CodeIndex,
    output_dir: Path,
) -> list[GeneratedTest]:
    """Generate tests from a YAML file of descriptions."""
    try:
        import yaml
    except ImportError:
        print("pyyaml is required for batch generation")
        return []

    data = yaml.safe_load(descriptions_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        data = data.get("tests", []) if isinstance(data, dict) else []

    results: list[GeneratedTest] = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for item in data:
        if isinstance(item, str):
            desc = item
            target = ""
            test_type = "unit"
        elif isinstance(item, dict):
            desc = str(item.get("description", ""))
            target = str(item.get("target_module", ""))
            test_type = str(item.get("test_type", "unit"))
        else:
            continue

        if not desc:
            continue

        result = generate_test_from_description(
            desc, index, target_module=target, test_type=test_type
        )
        # Write prompt to output file
        out_file = output_dir / result.file_name
        out_file.write_text(
            f"# Generated test prompt for: {desc}\n"
            f"# Similar tests: {', '.join(result.similar_tests[:3])}\n"
            f"# Confidence: {result.confidence:.2f}\n\n"
            f"{result.source_code}\n",
            encoding="utf-8",
        )
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_index(args: argparse.Namespace) -> int:
    source_dir = Path(args.source_dir).resolve()
    if not source_dir.is_dir():
        print(f"Source directory not found: {source_dir}")
        return 1

    print(f"Scanning {source_dir} for test code...")
    index = scan_directory(source_dir)
    output = Path(args.index_file)
    save_index(index, output)

    print(f"Indexed {index.total_functions_indexed} functions from {index.total_files_scanned} files")
    print(f"Framework breakdown: {index.framework_stats}")
    categories = {}
    for rec in index.records:
        categories[rec.category] = categories.get(rec.category, 0) + 1
    print(f"Categories: {categories}")
    print(f"Index saved: {output}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    index_path = Path(args.index_file)
    if not index_path.exists():
        print(f"Index file not found: {index_path}")
        print("Run 'index' command first to build the test index.")
        return 1

    index = load_index(index_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.query:
        result = generate_test_from_description(
            args.query,
            index,
            target_module=args.target_module or "",
            test_type=args.test_type or "unit",
        )
        out_file = output_dir / result.file_name
        out_file.write_text(
            f"# Generated test prompt for: {args.query}\n"
            f"# Similar tests: {', '.join(result.similar_tests[:3])}\n"
            f"# Confidence: {result.confidence:.2f}\n\n"
            f"{result.source_code}\n",
            encoding="utf-8",
        )
        print(f"Generated: {out_file}")
        print(f"Similar tests found: {len(result.similar_tests)}")
        print(f"Confidence: {result.confidence:.2f}")
        return 0

    if args.descriptions:
        desc_path = Path(args.descriptions)
        if not desc_path.exists():
            print(f"Descriptions file not found: {desc_path}")
            return 1
        results = batch_generate(desc_path, index, output_dir)
        print(f"Generated {len(results)} test prompts in {output_dir}")
        return 0

    print("Provide --query or --descriptions")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RAG-based test generation from existing test codebase"
    )
    subparsers = parser.add_subparsers(dest="command")

    # Index command
    idx = subparsers.add_parser("index", help="Index existing test code")
    idx.add_argument("--source-dir", required=True, help="Directory to scan for tests")
    idx.add_argument(
        "--index-file",
        default="reports/test-rag-index.json",
        help="Output index file",
    )

    # Generate command
    gen = subparsers.add_parser("generate", help="Generate tests from descriptions")
    gen.add_argument("--index-file", required=True, help="Path to test index JSON")
    gen.add_argument("--query", help="Single test description to generate")
    gen.add_argument("--descriptions", help="YAML file with test descriptions")
    gen.add_argument("--output-dir", default="generated/tests", help="Output directory")
    gen.add_argument("--target-module", help="Target module under test")
    gen.add_argument("--test-type", default="unit", help="Test type: unit|integration|api|e2e")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    if args.command == "index":
        return cmd_index(args)
    if args.command == "generate":
        return cmd_generate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
