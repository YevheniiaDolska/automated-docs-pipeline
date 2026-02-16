#!/usr/bin/env python3
"""Upload SEO-optimized records to Algolia."""

import json
import os
import sys
from pathlib import Path


def main():
    """Upload records to Algolia if available."""
    # Check for required environment variables
    app_id = os.environ.get('ALGOLIA_APP_ID')
    api_key = os.environ.get('ALGOLIA_API_KEY')
    index_name = os.environ.get('ALGOLIA_INDEX_NAME', 'docs')

    if not app_id or not api_key:
        print("Algolia credentials not found, skipping upload")
        return 0

    # Check for records file
    records_file = Path('seo-report-algolia.json')
    if not records_file.exists():
        print("No Algolia records file found")
        return 0

    # Import Algolia client (may not be installed)
    try:
        from algoliasearch.search_client import SearchClient
    except ImportError:
        print("Algolia client not installed, skipping upload")
        return 0

    # Load records
    with open(records_file, 'r') as f:
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
