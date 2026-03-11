#!/usr/bin/env python3
"""
Auto-Detecting Site Generator Wrapper

Detects which site generator the project uses (MkDocs, Docusaurus, Sphinx, Hugo, or Jekyll) and
runs the appropriate build, serve, or detect command.

Usage:
    python3 scripts/run_generator.py detect   # prints generator name
    python3 scripts/run_generator.py build    # runs correct build command
    python3 scripts/run_generator.py serve    # runs correct serve command
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from site_generator import SiteGenerator


def detect(project_dir: Path, generator_name: str | None = None) -> SiteGenerator:
    """Detect or instantiate the site generator."""
    if generator_name:
        return SiteGenerator.from_name(generator_name)
    return SiteGenerator.detect(project_dir)


def cmd_detect(args: argparse.Namespace) -> int:
    """Print the detected generator name."""
    gen = detect(Path(args.project_dir), args.generator)
    print(gen.name)
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Run the build command for the detected generator."""
    gen = detect(Path(args.project_dir), args.generator)
    cmd = gen.get_build_command()
    print(f"[run_generator] Building with {gen.name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=args.project_dir)
    return result.returncode


def cmd_serve(args: argparse.Namespace) -> int:
    """Run the serve command for the detected generator."""
    gen = detect(Path(args.project_dir), args.generator)
    cmd = gen.get_serve_command()
    print(f"[run_generator] Serving with {gen.name}: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=args.project_dir)
    return result.returncode


def cmd_info(args: argparse.Namespace) -> int:
    """Print info about the detected generator."""
    gen = detect(Path(args.project_dir), args.generator)
    print(f"Generator:    {gen.name}")
    print(f"Config file:  {gen.get_config_filename()}")
    print(f"Build cmd:    {' '.join(gen.get_build_command())}")
    print(f"Serve cmd:    {' '.join(gen.get_serve_command())}")
    print(f"Output dir:   {gen.get_build_output_dir()}")
    print(f"Docs dir:     {gen.get_docs_dir()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-detecting site generator wrapper"
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Project root directory (default: .)",
    )
    parser.add_argument(
        "--generator",
        choices=["mkdocs", "docusaurus", "sphinx", "hugo", "jekyll"],
        help="Force a specific generator instead of auto-detecting",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("detect", help="Print detected generator name")
    subparsers.add_parser("build", help="Run the build command")
    subparsers.add_parser("serve", help="Run the dev server")
    subparsers.add_parser("info", help="Print generator info")

    args = parser.parse_args()

    commands = {
        "detect": cmd_detect,
        "build": cmd_build,
        "serve": cmd_serve,
        "info": cmd_info,
    }

    if args.command in commands:
        return commands[args.command](args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
