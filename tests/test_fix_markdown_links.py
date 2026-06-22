from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_fix_markdown_links_repairs_missing_md_target(tmp_path: Path) -> None:
    from scripts.fix_markdown_links import fix_markdown_links

    docs = tmp_path / "docs"
    guide = docs / "guide"
    guide.mkdir(parents=True)
    (guide / "setup.md").write_text("# Setup\n", encoding="utf-8")
    page = docs / "index.md"
    page.write_text("[Setup](guide/setup)\n", encoding="utf-8")

    report = fix_markdown_links(docs, write=True)

    assert report["fixed_links"] == 1
    assert "[Setup](guide/setup.md)" in page.read_text(encoding="utf-8")


def test_fix_markdown_links_repairs_root_relative_index_and_anchor(tmp_path: Path) -> None:
    from scripts.fix_markdown_links import fix_markdown_links

    docs = tmp_path / "docs"
    guide = docs / "guide"
    guide.mkdir(parents=True)
    (guide / "index.md").write_text("# Hello World\n", encoding="utf-8")
    page = docs / "index.md"
    page.write_text("[Guide](/guide/#Hello_World)\n", encoding="utf-8")

    report = fix_markdown_links(docs, write=True)

    assert report["fixed_links"] == 1
    assert "[Guide](guide/index.md#hello-world)" in page.read_text(encoding="utf-8")


def test_fix_markdown_links_reports_ambiguous_target_without_rewrite(tmp_path: Path) -> None:
    from scripts.fix_markdown_links import fix_markdown_links

    docs = tmp_path / "docs"
    (docs / "a").mkdir(parents=True)
    (docs / "b").mkdir(parents=True)
    (docs / "a" / "install.md").write_text("# Install A\n", encoding="utf-8")
    (docs / "b" / "install.md").write_text("# Install B\n", encoding="utf-8")
    page = docs / "index.md"
    page.write_text("[Install](missing/install)\n", encoding="utf-8")

    report = fix_markdown_links(docs, write=True)

    assert report["fixed_links"] == 0
    assert report["unresolved_links"] == 1
    assert page.read_text(encoding="utf-8") == "[Install](missing/install)\n"
    assert report["unresolved"][0]["reason"] == "ambiguous-target"


def test_fix_markdown_links_main_writes_report(tmp_path: Path, monkeypatch) -> None:
    from scripts import fix_markdown_links as mod

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n", encoding="utf-8")
    report_path = tmp_path / "reports" / "link_fix_report.json"
    monkeypatch.setattr(sys, "argv", ["x", str(docs), "--report", str(report_path)])

    rc = mod.main()

    assert rc == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["scanned_files"] == 1


def test_fix_markdown_links_repairs_external_same_host_redirect(tmp_path: Path, monkeypatch) -> None:
    from scripts import fix_markdown_links as mod

    docs = tmp_path / "docs"
    docs.mkdir()
    page = docs / "index.md"
    page.write_text("[API](https://docs.example.com/old-path)\n", encoding="utf-8")

    monkeypatch.setattr(
        mod,
        "_probe_external_link",
        lambda raw_target, timeout_seconds: (mod.ExternalCandidate("https://docs.example.com/new-path"), ""),
    )

    report = mod.fix_markdown_links(docs, write=True, check_external=True)

    assert report["external_links_checked"] == 1
    assert report["fixed_links"] == 1
    assert "[API](https://docs.example.com/new-path)" in page.read_text(encoding="utf-8")


def test_fix_markdown_links_writes_needs_review_reports(tmp_path: Path) -> None:
    from scripts import fix_markdown_links as mod

    report = {
        "docs_root": "/tmp/docs",
        "unresolved_links": 1,
        "unresolved": [
            {
                "source_file": "index.md",
                "link_text": "API",
                "target": "https://docs.example.com/old-path",
                "reason": "network-error",
            }
        ],
    }
    review_json = tmp_path / "reports" / "needs_review.json"
    review_md = tmp_path / "reports" / "needs_review.md"

    mod._write_review_reports(report, review_json, review_md)

    json_payload = json.loads(review_json.read_text(encoding="utf-8"))
    assert json_payload["unresolved_links"] == 1
    md_text = review_md.read_text(encoding="utf-8")
    assert "Link Fix Needs Review" in md_text
    assert "`network-error`" in md_text
