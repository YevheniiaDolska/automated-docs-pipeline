#!/usr/bin/env python3
"""
Legacy wrapper for seo_enhance.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess

print("Note: seo_enhance.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with sitemap generation...\n")

# Pass arguments with --sitemap flag
args = [sys.executable, "scripts/seo_geo_optimizer.py", "docs/", "--sitemap"]
result = subprocess.run(args, capture_output=False)
sys.exit(result.returncode)
