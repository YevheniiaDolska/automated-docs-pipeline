#!/usr/bin/env python3
"""Upload SEO-optimized records to Algolia."""

import argparse
import json
import os
import sys
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


def main():
    """Upload records to Algolia if available."""
    args = parse_args()

    # Check for required environment variables
    app_id = os.environ.get(args.app_id_env)
    api_key = os.environ.get(args.api_key_env)
    index_name = os.environ.get(args.index_name_env, args.index_name_default)

    if not app_id or not api_key:
        print("Algolia credentials not found, skipping upload")
        return 0

    # Check for records file
    records_file = Path(args.records_file)
    if not records_file.exists():
        print(f"No Algolia records file found: {records_file}")
        return 0

    # Import Algolia client (may not be installed)
    try:
        from algoliasearch.search_client import SearchClient
    except ImportError:
        print("Algolia client not installed, skipping upload")
        return 0

    # Load records
    with records_file.open('r', encoding='utf-8') as f:
        data = json.load(f)
        records = data.get('records', [])
        config = data.get('config', {})

    if not records:
        print("No records to upload")
        return 0

    # Initialize client and upload
    client = SearchClient.create(app_id, api_key)
    index = client.init_index(index_name)

    # Update settings
    if config:
        index.set_settings(config)

    # Clear and upload records
    index.clear_objects()
    response = index.save_objects(records)

    print(f"Uploaded {len(records)} records to Algolia index '{index_name}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
