#!/usr/bin/env python3
"""
Legacy wrapper for algolia_config.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess
from pathlib import Path

print("Note: algolia_config.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with Algolia mode...\n")

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
optimizer_script = script_dir / "seo_geo_optimizer.py"
docs_dir = project_root / "docs"

if "--help" in sys.argv or "-h" in sys.argv:
    print("Usage: python scripts/algolia_config.py [--output OUTPUT_PATH]")
    print("Runs: python scripts/seo_geo_optimizer.py <project>/docs --algolia")
    sys.exit(0)

# Pass arguments with --algolia flag
args = [sys.executable, str(optimizer_script), str(docs_dir), "--algolia"]
if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    if idx + 1 < len(sys.argv):
        args.extend(['--output', sys.argv[idx + 1]])

result = subprocess.run(args, capture_output=False)
sys.exit(result.returncode)
