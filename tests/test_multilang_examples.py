from __future__ import annotations

from pathlib import Path


def test_validate_multilang_examples_pass(tmp_path: Path) -> None:
    from scripts.validate_multilang_examples import validate_docs

    docs = tmp_path / "docs"
    docs.mkdir()
    file_path = docs / "api-guide.md"
    file_path.write_text(
        """# API guide

=== "cURL"

    ```bash
    curl -X GET "https://api.example.com/v1/users"
    ```

=== "JavaScript"

    ```javascript
    const response = await fetch("https://api.example.com/v1/users");
    console.log(await response.json());
    ```

=== "Python"

    ```python
    import requests
    print(requests.get("https://api.example.com/v1/users").json())
    ```
""",
        encoding="utf-8",
    )

    issues = validate_docs(docs, "all", ["curl", "javascript", "python"])
    assert issues == []


def test_generate_multilang_tabs_transforms_curl(tmp_path: Path) -> None:
    from scripts.generate_multilang_tabs import transform_markdown

    source = """# API

```bash
curl -X GET "https://api.example.com/v1/users"
```
"""
    updated, changed = transform_markdown(source, scope="all", file_path=Path("docs/api-guide.md"))
    assert changed == 1
    assert '=== "cURL"' in updated
    assert '=== "JavaScript"' in updated
    assert '=== "Python"' in updated
