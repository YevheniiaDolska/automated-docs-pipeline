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
