#!/usr/bin/env python3
"""
Legacy wrapper for algolia_config.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess

print("Note: algolia_config.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with Algolia mode...\n")

# Pass arguments with --algolia flag
args = [sys.executable, "scripts/seo_geo_optimizer.py", "docs/", "--algolia"]
if '--output' in sys.argv:
    idx = sys.argv.index('--output')
    if idx + 1 < len(sys.argv):
        args.extend(['--output', sys.argv[idx + 1]])

result = subprocess.run(args, capture_output=False)
sys.exit(result.returncode)
