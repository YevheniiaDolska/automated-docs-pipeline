#!/usr/bin/env python3
"""
Legacy wrapper for auto_metadata.py
Redirects to the new consolidated seo_geo_optimizer.py
"""

import sys
import subprocess
from pathlib import Path

print("Note: auto_metadata.py has been consolidated into seo_geo_optimizer.py")
print("Running seo_geo_optimizer.py with --fix flag...\n")

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
optimizer_script = script_dir / "seo_geo_optimizer.py"
docs_dir = project_root / "docs"

if "--help" in sys.argv or "-h" in sys.argv:
    print("Usage: python scripts/auto_metadata.py")
    print("Runs: python scripts/seo_geo_optimizer.py <project>/docs --fix")
    sys.exit(0)

# Pass arguments with --fix flag for metadata enhancement
args = [sys.executable, str(optimizer_script), str(docs_dir), "--fix"]
result = subprocess.run(args, capture_output=False)
sys.exit(result.returncode)
