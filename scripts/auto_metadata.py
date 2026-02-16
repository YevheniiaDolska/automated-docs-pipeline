#!/usr/bin/env python3
"""
Legacy wrapper for auto_metadata.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess

print("Note: auto_metadata.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with --fix flag...\n")

# Pass arguments with --fix flag for metadata enhancement
args = [sys.executable, "scripts/seo_geo_optimizer.py", "docs/", "--fix"]
result = subprocess.run(args, capture_output=False)
sys.exit(result.returncode)
