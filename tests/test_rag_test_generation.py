"""Tests for RAG-based test generation (scripts/generate_tests_from_rag.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_tests_from_rag import (
    GeneratedTest,
    GenerationRequest,
    CodeIndex,
    CodeRecord,
    batch_generate,
    build_generation_prompt,
    generate_test_from_description,
    load_index,
    retrieve_similar,
    save_index,
    scan_directory,
    scan_python_file,
    validate_generated_test,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_test_file(tmp_path: Path) -> Path:
    code = '''\
import pytest
from myapp.api import create_user


class TestUserAPI:
    """Tests for user API endpoints."""

    def test_create_user_success(self):
        """Test that creating a user returns 201."""
        result = create_user("alice", "alice@example.com")
        assert result.status_code == 201

    def test_create_user_duplicate_email(self):
        """Test that duplicate email returns 409 conflict."""
        create_user("bob", "bob@example.com")
        with pytest.raises(Exception):
            create_user("carol", "bob@example.com")


def test_health_check():
    """Test the health check endpoint returns 200."""
    assert True


@pytest.fixture
def db_session():
    """Create a test database session."""
    return None
'''
    f = tmp_path / "test_users.py"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture()
def sample_step_file(tmp_path: Path) -> Path:
    code = '''\
def step_login(username, password):
    """Step: log in with credentials."""
    pass


def _step_navigate_to_dashboard():
    """Step: navigate to main dashboard."""
    pass
'''
    f = tmp_path / "steps.py"
    f.write_text(code, encoding="utf-8")
    return f


@pytest.fixture()
def sample_index(sample_test_file: Path, sample_step_file: Path) -> CodeIndex:
    base = sample_test_file.parent
    return scan_directory(base)


# ---------------------------------------------------------------------------
# Scanning tests
# ---------------------------------------------------------------------------


class TestScanPythonFile:
    def test_extracts_test_functions(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        names = [r.function_name for r in records]
        assert "test_create_user_success" in names
        assert "test_create_user_duplicate_email" in names
        assert "test_health_check" in names

    def test_extracts_fixtures(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        fixtures = [r for r in records if r.category == "fixture"]
        assert len(fixtures) == 1
        assert fixtures[0].function_name == "db_session"

    def test_detects_framework(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        test_recs = [r for r in records if r.category == "test"]
        assert all(r.framework == "pytest" for r in test_recs)

    def test_extracts_class_context(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        class_test = next(r for r in records if r.function_name == "test_create_user_success")
        assert class_test.class_name == "TestUserAPI"

    def test_standalone_test_has_empty_class(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        standalone = next(r for r in records if r.function_name == "test_health_check")
        assert standalone.class_name == ""

    def test_extracts_docstrings(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        rec = next(r for r in records if r.function_name == "test_create_user_success")
        assert "201" in rec.docstring

    def test_extracts_imports(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        assert any("pytest" in r.imports for r in records)
        assert any("myapp.api.create_user" in r.imports for r in records)

    def test_generates_description_from_docstring(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        rec = next(r for r in records if r.function_name == "test_create_user_success")
        assert "201" in rec.description

    def test_generates_description_from_name(self, tmp_path: Path) -> None:
        code = "def test_webhook_retry_backoff():\n    pass\n"
        f = tmp_path / "test_basic.py"
        f.write_text(code, encoding="utf-8")
        records = scan_python_file(f, tmp_path)
        assert len(records) == 1
        assert "webhook retry backoff" in records[0].description.lower()

    def test_handles_syntax_error(self, tmp_path: Path) -> None:
        f = tmp_path / "broken.py"
        f.write_text("def test_oops(:\n    pass\n", encoding="utf-8")
        records = scan_python_file(f, tmp_path)
        assert records == []

    def test_handles_encoding_error(self, tmp_path: Path) -> None:
        f = tmp_path / "binary.py"
        f.write_bytes(b"\xff\xfe\x00\x00")
        records = scan_python_file(f, tmp_path)
        assert records == []

    def test_computes_signature(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        sigs = [r.signature for r in records]
        assert all(len(s) == 16 for s in sigs)
        # Different functions should have different signatures
        assert len(set(sigs)) == len(sigs)

    def test_record_id_format(self, sample_test_file: Path) -> None:
        records = scan_python_file(sample_test_file, sample_test_file.parent)
        class_rec = next(r for r in records if r.class_name == "TestUserAPI")
        assert "::" in class_rec.id
        assert "TestUserAPI" in class_rec.id


class TestScanDirectory:
    def test_scans_all_files(self, sample_index: CodeIndex) -> None:
        assert sample_index.total_files_scanned == 2
        assert sample_index.total_functions_indexed >= 4

    def test_framework_stats(self, sample_index: CodeIndex) -> None:
        assert "pytest" in sample_index.framework_stats

    def test_skips_pycache(self, tmp_path: Path) -> None:
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "test_cached.py").write_text("def test_x(): pass\n", encoding="utf-8")
        (tmp_path / "test_real.py").write_text("def test_y(): pass\n", encoding="utf-8")
        index = scan_directory(tmp_path)
        names = [r.function_name for r in index.records]
        assert "test_y" in names
        assert "test_x" not in names

    def test_skips_venv(self, tmp_path: Path) -> None:
        venv = tmp_path / "venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "test_venv.py").write_text("def test_v(): pass\n", encoding="utf-8")
        index = scan_directory(tmp_path)
        names = [r.function_name for r in index.records]
        assert "test_v" not in names


# ---------------------------------------------------------------------------
# Retrieval tests
# ---------------------------------------------------------------------------


class TestRetrieveSimilar:
    def test_finds_relevant_tests(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("create user endpoint", sample_index, top_k=3)
        assert len(results) > 0
        names = [r.function_name for r, _ in results]
        assert any("create_user" in n for n in names)

    def test_respects_top_k(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("test", sample_index, top_k=2)
        assert len(results) <= 2

    def test_category_filter(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("database session", sample_index, category_filter="fixture")
        for rec, _ in results:
            assert rec.category == "fixture"

    def test_empty_query_returns_empty(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("", sample_index)
        assert results == []

    def test_no_match_returns_empty(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("xyzzy quantum entanglement", sample_index)
        assert results == []

    def test_scores_are_sorted(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("user email duplicate", sample_index, top_k=5)
        if len(results) >= 2:
            scores = [s for _, s in results]
            assert scores == sorted(scores, reverse=True)

    def test_tests_boosted_over_helpers(self, sample_index: CodeIndex) -> None:
        results = retrieve_similar("health check", sample_index, top_k=5)
        if results:
            top_rec, _ = results[0]
            assert top_rec.category in {"test", "step"}


# ---------------------------------------------------------------------------
# Prompt construction tests
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_includes_description(self) -> None:
        req = GenerationRequest(description="Test webhook retry with exponential backoff")
        prompt = build_generation_prompt(req, [])
        assert "webhook retry" in prompt.lower()
        assert "exponential backoff" in prompt.lower()

    def test_includes_examples(self, sample_index: CodeIndex) -> None:
        req = GenerationRequest(description="Test user creation")
        similar = retrieve_similar("user creation", sample_index, top_k=2)
        prompt = build_generation_prompt(req, similar)
        assert "Example 1" in prompt
        assert "similarity:" in prompt

    def test_includes_framework(self) -> None:
        req = GenerationRequest(description="Test something", framework="unittest")
        prompt = build_generation_prompt(req, [])
        assert "unittest" in prompt

    def test_includes_import_context(self, sample_index: CodeIndex) -> None:
        req = GenerationRequest(description="Test user creation")
        similar = retrieve_similar("user creation", sample_index, top_k=2)
        prompt = build_generation_prompt(req, similar)
        assert "Import Context" in prompt

    def test_includes_requirements(self) -> None:
        req = GenerationRequest(description="Test API")
        prompt = build_generation_prompt(req, [])
        assert "docstring" in prompt.lower()
        assert "test_" in prompt


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidateGenerated:
    def test_valid_test_passes(self) -> None:
        code = (
            "import pytest\n\n"
            "def test_addition():\n"
            "    assert 2 + 2 == 4\n"
        )
        ok, errors = validate_generated_test(code)
        assert ok is True
        assert errors == []

    def test_syntax_error_fails(self) -> None:
        code = "def test_broken(:\n    pass\n"
        ok, errors = validate_generated_test(code)
        assert ok is False
        assert any("Syntax" in e for e in errors)

    def test_no_test_function_fails(self) -> None:
        code = "import pytest\n\ndef helper():\n    pass\n"
        ok, errors = validate_generated_test(code)
        assert ok is False
        assert any("test_" in e for e in errors)

    def test_no_imports_warns(self) -> None:
        code = "def test_something():\n    assert True\n"
        ok, errors = validate_generated_test(code)
        assert ok is False
        assert any("import" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Index serialization tests
# ---------------------------------------------------------------------------


class TestCodeIndexSerialization:
    def test_save_and_load_roundtrip(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        out = tmp_path / "index.json"
        save_index(sample_index, out)
        loaded = load_index(out)
        assert loaded.total_files_scanned == sample_index.total_files_scanned
        assert loaded.total_functions_indexed == sample_index.total_functions_indexed
        assert len(loaded.records) == len(sample_index.records)

    def test_saved_json_structure(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        out = tmp_path / "index.json"
        save_index(sample_index, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "records" in data
        assert "source_dirs" in data
        assert "framework_stats" in data
        # Embeddings should be stripped
        for rec in data["records"]:
            assert "embedding" not in rec

    def test_creates_parent_dirs(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        out = tmp_path / "deep" / "nested" / "index.json"
        save_index(sample_index, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# Generation orchestrator tests
# ---------------------------------------------------------------------------


class TestGenerateFromDescription:
    def test_returns_generated_test(self, sample_index: CodeIndex) -> None:
        result = generate_test_from_description(
            "Test that user creation returns 201",
            sample_index,
        )
        assert isinstance(result, GeneratedTest)
        assert result.description == "Test that user creation returns 201"
        assert result.file_name.startswith("test_")
        assert result.file_name.endswith(".py")

    def test_includes_similar_tests(self, sample_index: CodeIndex) -> None:
        result = generate_test_from_description(
            "Test user email validation",
            sample_index,
        )
        assert len(result.similar_tests) > 0

    def test_file_name_from_description(self, sample_index: CodeIndex) -> None:
        result = generate_test_from_description(
            "Test webhook retry logic backs off exponentially",
            sample_index,
        )
        assert "webhook" in result.file_name
        assert result.file_name.endswith(".py")

    def test_no_similar_tests_still_generates(self, tmp_path: Path) -> None:
        empty_index = CodeIndex(records=[], source_dirs=[])
        result = generate_test_from_description("Test something", empty_index)
        assert result.source_code  # Should still produce a prompt
        assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Batch generation tests
# ---------------------------------------------------------------------------


class TestBatchGenerate:
    def test_generates_from_yaml_list(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        import yaml

        desc_file = tmp_path / "descs.yml"
        desc_file.write_text(
            yaml.safe_dump(
                [
                    "Test user login with valid credentials",
                    "Test user login with invalid password",
                ]
            ),
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        results = batch_generate(desc_file, sample_index, out_dir)
        assert len(results) == 2
        assert (out_dir).is_dir()
        generated_files = list(out_dir.glob("test_*.py"))
        assert len(generated_files) == 2

    def test_generates_from_yaml_dict(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        import yaml

        desc_file = tmp_path / "descs.yml"
        desc_file.write_text(
            yaml.safe_dump(
                {
                    "tests": [
                        {
                            "description": "Test API health endpoint",
                            "target_module": "myapp.api",
                            "test_type": "integration",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        results = batch_generate(desc_file, sample_index, out_dir)
        assert len(results) == 1

    def test_skips_empty_descriptions(self, sample_index: CodeIndex, tmp_path: Path) -> None:
        import yaml

        desc_file = tmp_path / "descs.yml"
        desc_file.write_text(
            yaml.safe_dump(["Test something", "", "Test another"]),
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        results = batch_generate(desc_file, sample_index, out_dir)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_async_test_detected(self, tmp_path: Path) -> None:
        code = "import pytest\n\nasync def test_async_op():\n    assert True\n"
        f = tmp_path / "test_async.py"
        f.write_text(code, encoding="utf-8")
        records = scan_python_file(f, tmp_path)
        assert len(records) == 1
        assert records[0].category == "test"

    def test_parametrized_test(self, tmp_path: Path) -> None:
        code = (
            "import pytest\n\n"
            "@pytest.mark.parametrize('x', [1, 2, 3])\n"
            "def test_param(x):\n"
            "    assert x > 0\n"
        )
        f = tmp_path / "test_param.py"
        f.write_text(code, encoding="utf-8")
        records = scan_python_file(f, tmp_path)
        assert len(records) == 1
        assert records[0].framework == "pytest"

    def test_empty_directory(self, tmp_path: Path) -> None:
        index = scan_directory(tmp_path)
        assert index.total_files_scanned == 0
        assert index.total_functions_indexed == 0
        assert index.records == []

    def test_non_test_file_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / "utils.py"
        f.write_text("def helper():\n    return 42\n", encoding="utf-8")
        index = scan_directory(tmp_path)
        assert index.total_functions_indexed == 0
