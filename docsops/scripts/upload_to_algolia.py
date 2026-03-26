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

    # Update index settings
    if config:
        result = _algolia_request(app_id, api_key, "PUT", f"{base}/settings", config)
        print(f"Index settings updated (taskID={result.get('taskID')})")

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
