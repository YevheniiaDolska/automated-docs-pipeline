from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_sync_glossary_adds_new_term(tmp_path: Path) -> None:
    from scripts.sync_project_glossary import sync_glossary

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    md = docs_dir / "guide.md"
    md.write_text(
        (
            "# Guide\n\n"
            "Use SmartQueue to sequence retries.\n\n"
            "<!-- glossary:add: SmartQueue | Queue manager for retry orchestration | retry queue -->\n"
        ),
        encoding="utf-8",
    )

    glossary_path = tmp_path / "glossary.yml"
    glossary_path.write_text("terms: {}\nforbidden: []\n", encoding="utf-8")
    report_path = tmp_path / "reports" / "glossary_sync_report.json"

    report = sync_glossary(
        paths=[str(docs_dir)],
        glossary_path=glossary_path,
        write=True,
        report_path=report_path,
    )

    assert report["added_count"] == 1
    glossary = yaml.safe_load(glossary_path.read_text(encoding="utf-8"))
    assert "SmartQueue" in glossary["terms"]
    assert glossary["terms"]["SmartQueue"]["aliases"] == ["retry queue"]
    assert report_path.exists()


def test_sync_glossary_updates_existing_term(tmp_path: Path) -> None:
    from scripts.sync_project_glossary import sync_glossary

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text(
        "<!-- glossary:add: Event Mesh | Messaging layer for event routing | router -->\n",
        encoding="utf-8",
    )

    glossary_path = tmp_path / "glossary.yml"
    glossary_path.write_text(
        yaml.safe_dump(
            {
                "terms": {
                    "Event Mesh": {
                        "description": "Messaging layer for distributed events",
                        "aliases": [],
                    }
                },
                "forbidden": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    report = sync_glossary(
        paths=[str(docs_dir)],
        glossary_path=glossary_path,
        write=True,
        report_path=None,
    )
    assert report["updated_count"] == 1
    glossary = yaml.safe_load(glossary_path.read_text(encoding="utf-8"))
    assert glossary["terms"]["Event Mesh"]["aliases"] == ["router"]


def test_noop_sync_does_not_rewrite_the_glossary(tmp_path: Path) -> None:
    """A YAML re-dump strips comments and reflows the file.

    Doing that on a run that changed nothing silently destroys the
    hand-written per-locale terminology rules and their documentation.
    """
    from scripts.sync_project_glossary import sync_glossary

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text("# Guide\n\nNo markers here.\n", encoding="utf-8")

    glossary_path = tmp_path / "glossary.yml"
    original = (
        "# Project glossary - hand-written header that must survive\n"
        "terms:\n"
        "  retry:\n"
        "    description: Automatic re-execution after failure\n"
        "    aliases: []\n"
        "    # Only enforce terms where a mistranslation changes the meaning\n"
        "    locales:\n"
        "      ru:\n"
        "        preferred: повторная попытка\n"
        "forbidden: []\n"
    )
    glossary_path.write_text(original, encoding="utf-8")

    report = sync_glossary(
        paths=[str(docs_dir)],
        glossary_path=glossary_path,
        write=True,
        report_path=None,
    )

    assert report["added_count"] == 0
    assert report["updated_count"] == 0
    assert glossary_path.read_text(encoding="utf-8") == original


def test_sync_keeps_non_english_terms_readable(tmp_path: Path) -> None:
    r"""Escaping Cyrillic to \uXXXX makes locale rules unmaintainable.

    The reviewers who curate these rules are the ones who must read them.
    """
    from scripts.sync_project_glossary import sync_glossary

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text(
        "# Guide\n\n"
        "<!-- glossary:add: SmartQueue | Queue manager | queue -->\n",
        encoding="utf-8",
    )

    glossary_path = tmp_path / "glossary.yml"
    glossary_path.write_text(
        yaml.safe_dump(
            {
                "terms": {
                    "retry": {
                        "description": "Automatic re-execution after failure",
                        "aliases": [],
                        "locales": {"ru": {"preferred": "повторная попытка"}},
                    }
                },
                "forbidden": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    # This run adds a term, so the file is legitimately rewritten.
    report = sync_glossary(
        paths=[str(docs_dir)],
        glossary_path=glossary_path,
        write=True,
        report_path=None,
    )
    assert report["added_count"] == 1

    raw = glossary_path.read_text(encoding="utf-8")
    assert "повторная попытка" in raw
    # The literal escape sequence must not appear, as opposed to the
    # character it denotes.
    # A literal backslash-u escape sequence must not appear in the file,
    # as opposed to the character it denotes. chr(92) is a backslash.
    assert (chr(92) + "u04") not in raw

    glossary = yaml.safe_load(raw)
    assert glossary["terms"]["retry"]["locales"]["ru"]["preferred"] == "повторная попытка"
