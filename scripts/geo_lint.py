#!/usr/bin/env python3
"""
Legacy wrapper for geo_lint.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess

print("Note: geo_lint.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with GEO-only mode...\n")

# Pass all arguments to the new script
result = subprocess.run(
    [sys.executable, "scripts/seo_geo_optimizer.py"] + sys.argv[1:],
    capture_output=False
)

sys.exit(result.returncode)
