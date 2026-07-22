"""Tests for the SSOT multi-language SDK snippet renderer."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts import render_sdk_snippets as mod

_VARIABLES = {
    "api_url": "https://api.example.com",
    "env_vars": {"api_key": "PRODUCT_API_KEY"},
}

_SPEC = {
    "id": "create-charge",
    "title": "Create a charge",
    "description": "Create a charge for 20.00 USD.",
    "method": "POST",
    "path": "/v1/charges",
    "auth": "bearer",
    "body": {"amount": 2000, "currency": "usd", "active": True, "note": None},
    "languages": ["curl", "python", "javascript", "go"],
}


def _python_block(rendered: str) -> str:
    """Extract the code inside the Python content tab."""
    lines = rendered.split("\n")
    start = next(i for i, line in enumerate(lines) if line.strip() == "```python")
    end = next(i for i in range(start + 1, len(lines)) if lines[i].strip() == "```")
    return "\n".join(line[4:] for line in lines[start + 1:end])


def test_all_languages_render_and_share_ssot_values() -> None:
    rendered = mod.render_spec(_SPEC, _VARIABLES, "create-charge.req.yml")
    for label in ('=== "cURL"', '=== "Python"', '=== "JavaScript"', '=== "Go"'):
        assert label in rendered
    # Base URL and API-key env var come from variables, not hard-coded per language.
    assert rendered.count("https://api.example.com/v1/charges") == 4
    assert "$PRODUCT_API_KEY" in rendered            # curl
    assert "os.environ['PRODUCT_API_KEY']" in rendered  # python
    assert "process.env.PRODUCT_API_KEY" in rendered    # javascript
    assert 'os.Getenv("PRODUCT_API_KEY")' in rendered   # go
    assert "do not edit" in rendered


def test_generated_python_is_valid_syntax() -> None:
    rendered = mod.render_spec(_SPEC, _VARIABLES, "create-charge.req.yml")
    code = _python_block(rendered)
    # bool/None must render as Python literals, not JSON true/null.
    assert '"active": True' in code
    assert '"note": None' in code
    compile(code, "<snippet>", "exec")  # raises SyntaxError if malformed


def test_auth_none_omits_authorization() -> None:
    spec = dict(_SPEC, auth="none")
    rendered = mod.render_spec(spec, _VARIABLES, "x.req.yml")
    assert "Authorization" not in rendered


def test_check_mode_detects_drift(tmp_path: Path) -> None:
    specs_dir = tmp_path / "specs"
    out_dir = tmp_path / "out"
    specs_dir.mkdir()
    var_file = tmp_path / "_variables.yml"
    var_file.write_text(
        "api_url: https://api.example.com\nenv_vars:\n  api_key: PRODUCT_API_KEY\n",
        encoding="utf-8",
    )
    (specs_dir / "create-charge.req.yml").write_text(
        "id: create-charge\ntitle: Create a charge\nmethod: POST\npath: /v1/charges\n"
        "body:\n  amount: 2000\nlanguages: [curl, python]\n",
        encoding="utf-8",
    )

    def _run(check: bool) -> int:
        argv = [
            "render_sdk_snippets.py",
            "--specs-dir", str(specs_dir),
            "--output-dir", str(out_dir),
            "--variables", str(var_file),
        ]
        if check:
            argv.append("--check")
        old = sys.argv
        sys.argv = argv
        try:
            return mod.main()
        finally:
            sys.argv = old

    # Stale before first render.
    assert _run(check=True) == 1
    # Render, then check passes.
    assert _run(check=False) == 0
    assert (out_dir / "create-charge.md").exists()
    assert _run(check=True) == 0


def test_cli_renders_repo_spec() -> None:
    """The committed spec renders without error via the CLI."""
    result = subprocess.run(
        [sys.executable, "scripts/render_sdk_snippets.py", "--check"],
        capture_output=True,
        text=True,
    )
    # Either current (0) or stale (1) is acceptable here; a crash (2) is not.
    assert result.returncode in (0, 1), result.stdout + result.stderr
