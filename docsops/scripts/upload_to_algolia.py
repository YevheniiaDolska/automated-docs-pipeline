#!/usr/bin/env python3
"""Upload SEO-optimized records to Algolia.

Uses the Algolia REST API directly (no SDK dependency) so the script
works with any Python 3.8+ installation.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload records to Algolia")
    parser.add_argument(
        "--records-file",
        default="seo-report-algolia.json",
        help="Path to Algolia records payload JSON",
    )
    parser.add_argument(
        "--app-id-env",
        default="ALGOLIA_APP_ID",
        help="Environment variable name for Algolia app id",
    )
    parser.add_argument(
        "--api-key-env",
        default="ALGOLIA_API_KEY",
        help="Environment variable name for Algolia admin API key",
    )
    parser.add_argument(
        "--index-name-env",
        default="ALGOLIA_INDEX_NAME",
        help="Environment variable name for Algolia index name",
    )
    parser.add_argument(
        "--index-name-default",
        default="docs",
        help="Fallback index name if env variable is not set",
    )
    parser.add_argument(
        "--advanced-config",
        default="",
        help="Optional path to advanced Algolia config YAML/JSON",
    )
    parser.add_argument(
        "--apply-advanced",
        action="store_true",
        help="Apply synonyms/query rules/replicas from --advanced-config",
    )
    return parser.parse_args()


def _algolia_request(app_id: str, api_key: str, method: str, path: str, body=None):
    """Send a request to the Algolia REST API."""
    url = f"https://{app_id}-dsn.algolia.net{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-Algolia-Application-Id", app_id)
    req.add_header("X-Algolia-API-Key", api_key)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _load_advanced_config(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(raw) or {}
    else:
        data = json.loads(raw or "{}")
    return data if isinstance(data, dict) else {}


def _upsert_synonyms(app_id: str, api_key: str, base: str, synonyms: list[dict]) -> None:
    for syn in synonyms:
        if not isinstance(syn, dict):
            continue
        object_id = str(syn.get("objectID", "")).strip()
        if not object_id:
            continue
        result = _algolia_request(app_id, api_key, "PUT", f"{base}/synonyms/{object_id}", syn)
        print(f"Synonym upserted: {object_id} (taskID={result.get('taskID')})")


def _upsert_rules(app_id: str, api_key: str, base: str, rules: list[dict]) -> None:
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        object_id = str(rule.get("objectID", "")).strip()
        if not object_id:
            continue
        result = _algolia_request(app_id, api_key, "PUT", f"{base}/rules/{object_id}", rule)
        print(f"Rule upserted: {object_id} (taskID={result.get('taskID')})")


def main():
    """Upload records to Algolia."""
    args = parse_args()

    app_id = os.environ.get(args.app_id_env)
    api_key = os.environ.get(args.api_key_env)
    index_name = os.environ.get(args.index_name_env, args.index_name_default)

    if not app_id or not api_key:
        print("Algolia credentials not found, skipping upload")
        return 0

    records_file = Path(args.records_file)
    if not records_file.exists():
        print(f"No Algolia records file found: {records_file}")
        return 0

    with records_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        records = data.get("records", [])
        config = data.get("config", {})
    elif isinstance(data, list):
        records = data
        config = {}
    else:
        print(f"Unsupported payload format in {records_file}")
        return 1

    if not records:
        print("No records to upload")
        return 0

    base = f"/1/indexes/{index_name}"
    advanced_cfg = {}
    if args.apply_advanced and args.advanced_config.strip():
        advanced_cfg = _load_advanced_config(Path(args.advanced_config))

    # Update index settings
    settings = {}
    if isinstance(config, dict):
        settings.update(config)
    adv_settings = advanced_cfg.get("settings", {})
    if isinstance(adv_settings, dict):
        settings.update(adv_settings)
    if settings:
        result = _algolia_request(app_id, api_key, "PUT", f"{base}/settings", settings)
        print(f"Index settings updated (taskID={result.get('taskID')})")

    if advanced_cfg:
        synonyms = advanced_cfg.get("synonyms", [])
        if isinstance(synonyms, list):
            _upsert_synonyms(app_id, api_key, base, synonyms)

        rules = advanced_cfg.get("rules", [])
        if isinstance(rules, list):
            _upsert_rules(app_id, api_key, base, rules)

        replicas = advanced_cfg.get("replicas", [])
        if isinstance(replicas, list):
            names = [str(v).strip() for v in replicas if str(v).strip()]
            if names:
                result = _algolia_request(app_id, api_key, "PUT", f"{base}/settings", {"replicas": names})
                print(f"Replicas configured: {', '.join(names)} (taskID={result.get('taskID')})")
                replica_settings = advanced_cfg.get("replica_settings", {})
                if isinstance(replica_settings, dict):
                    for replica_name in names:
                        rs = replica_settings.get(replica_name, {})
                        if not isinstance(rs, dict) or not rs:
                            continue
                        replica_base = f"/1/indexes/{replica_name}"
                        result = _algolia_request(app_id, api_key, "PUT", f"{replica_base}/settings", rs)
                        print(f"Replica settings applied: {replica_name} (taskID={result.get('taskID')})")

        per_index = advanced_cfg.get("per_index", {})
        if isinstance(per_index, dict):
            for idx_name, idx_cfg in per_index.items():
                idx = str(idx_name).strip()
                if not idx or not isinstance(idx_cfg, dict):
                    continue
                idx_base = f"/1/indexes/{idx}"
                idx_settings = idx_cfg.get("settings", {})
                if isinstance(idx_settings, dict) and idx_settings:
                    result = _algolia_request(app_id, api_key, "PUT", f"{idx_base}/settings", idx_settings)
                    print(f"Per-index settings applied: {idx} (taskID={result.get('taskID')})")
                idx_synonyms = idx_cfg.get("synonyms", [])
                if isinstance(idx_synonyms, list):
                    _upsert_synonyms(app_id, api_key, idx_base, idx_synonyms)
                idx_rules = idx_cfg.get("rules", [])
                if isinstance(idx_rules, list):
                    _upsert_rules(app_id, api_key, idx_base, idx_rules)

        query_suggestions = advanced_cfg.get("query_suggestions", {})
        if isinstance(query_suggestions, dict):
            source_index = str(query_suggestions.get("source_index", index_name)).strip() or index_name
            model = query_suggestions.get("model", {})
            if isinstance(model, dict) and model:
                path = f"/1/indexes/{source_index}/querySuggestions"
                result = _algolia_request(app_id, api_key, "POST", path, model)
                print(f"Query suggestions configured for {source_index} (taskID={result.get('taskID')})")

    # Clear existing records
    result = _algolia_request(app_id, api_key, "POST", f"{base}/clear", {})
    print(f"Index cleared (taskID={result.get('taskID')})")

    # Upload records in batches
    batch_size = 1000
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        body = {"requests": [{"action": "addObject", "body": r} for r in batch]}
        result = _algolia_request(app_id, api_key, "POST", f"{base}/batch", body)
        total += len(batch)
        print(
            f"Batch {i // batch_size + 1}: "
            f"{len(batch)} records (taskID={result.get('taskID')})"
        )

    print(f"Uploaded {total} records to Algolia index '{index_name}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
