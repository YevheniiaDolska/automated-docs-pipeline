#!/usr/bin/env python3
"""Compile Tier A modules to .so/.pyd using Cython.

Reads protected_modules.yml for the manifest, compiles each Tier A
module with Cython + GCC/MSVC, strips debug symbols, and generates
a signed module hash manifest.

Usage:
  python3 build/compile_protected.py --platform linux-x86_64 --python 3.12
  python3 build/compile_protected.py --platform macos-arm64 --python 3.12 --output dist/
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

BUILD_DIR = Path(__file__).resolve().parent
REPO_ROOT = BUILD_DIR.parent
MANIFEST_PATH = BUILD_DIR / "protected_modules.yml"

SUPPORTED_PLATFORMS = ["linux-x86_64", "macos-arm64", "macos-x86_64", "windows-x64"]
SUPPORTED_PYTHONS = ["3.11", "3.12", "3.13"]


def _read_manifest() -> dict[str, Any]:
    raw = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Invalid protected_modules.yml")
    return raw


def _compile_module(source: Path, output_dir: Path, platform: str) -> Path | None:
    """Compile a single Python module to .so/.pyd via Cython."""
    if not source.exists():
        print(f"  [skip] Source not found: {source}")
        return None

    module_name = source.stem
    pyx_path = output_dir / f"{module_name}.pyx"

    # Copy source as .pyx
    shutil.copy2(source, pyx_path)

    # Write minimal setup.py for this module
    setup_content = f"""
from setuptools import setup
from Cython.Build import cythonize
from Cython.Compiler import Options

Options.docstrings = False

setup(
    ext_modules=cythonize(
        "{pyx_path.name}",
        compiler_directives={{
            "embedsignature": False,
            "binding": False,
            "language_level": "3",
        }},
    ),
)
"""
    setup_path = output_dir / f"setup_{module_name}.py"
    setup_path.write_text(setup_content, encoding="utf-8")

    # Run compilation
    cmd = [
        sys.executable,
        setup_path.name,
        "build_ext",
        "--inplace",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(output_dir),
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"  [error] Compilation failed for {module_name}")
        if result.stderr:
            for line in result.stderr.strip().splitlines()[-5:]:
                print(f"    {line}")
        return None

    # Find the compiled output
    ext = ".pyd" if "windows" in platform else ".so"
    compiled = list(output_dir.glob(f"{module_name}*{ext}"))
    if not compiled:
        # Sometimes extension includes cpython version tag
        compiled = list(output_dir.glob(f"{module_name}*.so")) + list(output_dir.glob(f"{module_name}*.pyd"))

    if compiled:
        return compiled[0]

    print(f"  [error] No compiled output found for {module_name}")
    return None


def _strip_debug(path: Path, platform: str) -> None:
    """Strip debug symbols from compiled module."""
    if "windows" in platform:
        return
    strip_cmd = "strip"
    if shutil.which(strip_cmd):
        subprocess.run([strip_cmd, "-S", str(path)], check=False)


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _generate_hash_manifest(
    compiled_modules: dict[str, Path],
    output_dir: Path,
) -> Path:
    """Generate a hash manifest for all compiled modules."""
    manifest = {
        "version": 1,
        "modules": {},
    }
    for name, path in sorted(compiled_modules.items()):
        manifest["modules"][name] = {
            "file": path.name,
            "sha256": _hash_file(path),
            "size": path.stat().st_size,
        }

    manifest_path = output_dir / ".module_hashes.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Tier A modules with Cython")
    parser.add_argument(
        "--platform",
        choices=SUPPORTED_PLATFORMS,
        required=True,
        help="Target platform",
    )
    parser.add_argument(
        "--python",
        choices=SUPPORTED_PYTHONS,
        default="3.12",
        help="Target Python version",
    )
    parser.add_argument(
        "--output",
        default="dist/compiled",
        help="Output directory for compiled modules",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List modules that would be compiled without compiling",
    )
    args = parser.parse_args()

    manifest = _read_manifest()
    tier_a = manifest.get("tier_a", [])

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[compile] Platform: {args.platform}")
    print(f"[compile] Python: {args.python}")
    print(f"[compile] Tier A modules: {len(tier_a)}")
    print(f"[compile] Output: {output_dir}")

    if args.dry_run:
        print("\n[dry-run] Modules that would be compiled:")
        for entry in tier_a:
            source = REPO_ROOT / entry["source"]
            exists = source.exists()
            status = "OK" if exists else "MISSING"
            print(f"  {entry['module']} ({source}) [{status}]")
        return 0

    # Check for Cython
    try:
        import Cython  # noqa: F401
    except ImportError:
        print("[error] Cython is not installed. Run: pip install cython")
        return 1

    compiled: dict[str, Path] = {}
    failed: list[str] = []

    for entry in tier_a:
        module_name = entry["module"]
        source = REPO_ROOT / entry["source"]
        print(f"\n[compile] {module_name} <- {source}")

        result = _compile_module(source, output_dir, args.platform)
        if result:
            _strip_debug(result, args.platform)
            compiled[module_name] = result
            print(f"  [ok] {result.name} ({result.stat().st_size} bytes)")
        else:
            failed.append(module_name)

    # Generate hash manifest
    if compiled:
        manifest_path = _generate_hash_manifest(compiled, output_dir)
        print(f"\n[compile] Hash manifest: {manifest_path}")

    # Cleanup build artifacts
    for pattern in ["*.pyx", "setup_*.py", "*.c", "build/"]:
        for item in output_dir.glob(pattern):
            if item.is_dir():
                shutil.rmtree(item)
            elif item.suffix in {".pyx", ".py", ".c"}:
                item.unlink()

    print(f"\n[compile] Results: {len(compiled)} compiled, {len(failed)} failed")
    if failed:
        print(f"[compile] Failed modules: {', '.join(failed)}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
