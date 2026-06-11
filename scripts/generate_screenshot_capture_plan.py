#!/usr/bin/env python3
"""Generate or update universal screenshot capture plan from docs tree."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

import yaml


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")


def _read_frontmatter_and_body(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except Exception:  # noqa: BLE001
        fm = {}
    body = parts[2]
    return (fm if isinstance(fm, dict) else {}), body


def _first_h2(body: str) -> str:
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def _doc_url_path(rel_doc: str) -> str:
    path = rel_doc.replace('\\', '/')
    if path.endswith('.md'):
        path = path[:-3]
    if path.endswith('/index'):
        path = path[:-len('/index')]
    if path == 'index':
        return '/'
    return '/' + path.strip('/') + '/'


def _load_existing(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate screenshot capture plan from docs')
    parser.add_argument('--docs-root', default='docs')
    parser.add_argument('--output', default='docs/screenshots.capture.yml')
    parser.add_argument('--base-url', default='http://localhost:3000')
    parser.add_argument('--storage-state', default='reports/playwright_storage_state.json')
    parser.add_argument('--max-items', type=int, default=120)
    args = parser.parse_args()

    repo_root = Path.cwd()
    docs_root = (repo_root / args.docs_root).resolve()
    output_path = (repo_root / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_existing(output_path)
    existing_captures = existing.get('captures', []) if isinstance(existing.get('captures'), list) else []
    existing_by_doc: dict[str, dict[str, Any]] = {}
    for item in existing_captures:
        if isinstance(item, dict):
            doc = str(item.get('doc_path', '')).strip()
            if doc:
                existing_by_doc[doc] = item

    candidates: list[dict[str, Any]] = []
    for md in sorted(docs_root.rglob('*.md')):
        if md.name.startswith('_'):
            continue
        rel = md.relative_to(docs_root).as_posix()
        if rel.endswith('/index.md') or rel == 'index.md':
            continue
        text = md.read_text(encoding='utf-8', errors='ignore')
        fm, body = _read_frontmatter_and_body(text)
        title = str(fm.get('title', '')).strip() or md.stem.replace('-', ' ').strip().title()
        section = _first_h2(body) or title
        anchor = _slug(section)
        output = f"docs/assets/screenshots/{_slug(rel[:-3].replace('/', '-'))}.png"
        url = f"{args.base_url.rstrip('/')}{_doc_url_path(rel)}"
        rec = {
            'id': f"doc-{_slug(rel[:-3].replace('/', '-'))}",
            'url': url,
            'output': output,
            'doc_path': rel,
            'section_heading': section,
            'section_anchor': anchor,
            'alt': f"{title} screenshot",
            'wait_for': 'networkidle',
            'full_page': False,
        }
        old = existing_by_doc.get(rel)
        if isinstance(old, dict):
            merged = dict(rec)
            merged.update(old)
            rec = merged
        candidates.append(rec)
        if len(candidates) >= max(1, int(args.max_items)):
            break

    payload = {
        'version': 1,
        'defaults': {
            'storage_state': args.storage_state,
            'viewport': {'width': 1440, 'height': 900},
            'wait_for': 'networkidle',
            'full_page': False,
        },
        'auth': {
            'enabled': False,
            'login_url': '',
            'storage_state_output': args.storage_state,
            'steps': [
                {'type': 'fill', 'selector': "input[name='email']", 'value': '${SCREENSHOT_LOGIN_EMAIL}'},
                {'type': 'fill', 'selector': "input[name='password']", 'value': '${SCREENSHOT_LOGIN_PASSWORD}'},
                {'type': 'click', 'selector': "button[type='submit']"},
                {'type': 'wait_for_selector', 'selector': "[data-testid='dashboard']"},
            ],
        },
        'captures': candidates,
    }

    output_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding='utf-8')
    print(f"[screenshot-plan] generated: {output_path} (captures={len(candidates)})")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
