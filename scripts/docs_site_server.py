#!/usr/bin/env python3
"""Build the MkDocs documentation site and serve it locally for screenshot capture.

The autopipeline screenshot stage needs real, rendered pages to point Playwright at.
Without a running site, every ``page.goto`` against ``http://localhost:3000`` times out
and the pipeline captures zero screenshots. This helper builds the MkDocs site to a
temporary directory and serves it over loopback so the capture stage has live pages.

Everything degrades gracefully: if MkDocs is missing, the build fails, or no index page
is produced, ``serve_docs_site`` returns ``None`` and the caller skips capture instead of
failing the pipeline.

Standalone usage (mostly for debugging):

    python scripts/docs_site_server.py --seconds 30
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Static handler that does not spam stdout/stderr with per-request logs."""

    def log_message(self, *args, **kwargs) -> None:  # noqa: D401, ANN002, ANN003
        return


class _ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class DocsSiteServer:
    """Handle to a running local docs site. Call ``stop()`` when capture finishes."""

    def __init__(
        self,
        base_url: str,
        site_dir: Path,
        httpd: _ThreadingHTTPServer,
        thread: threading.Thread,
        tmp: "tempfile.TemporaryDirectory[str]",
    ) -> None:
        self.base_url = base_url
        self.site_dir = site_dir
        self._httpd = httpd
        self._thread = thread
        self._tmp = tmp

    def stop(self) -> None:
        with contextlib.suppress(Exception):
            self._httpd.shutdown()
        with contextlib.suppress(Exception):
            self._httpd.server_close()
        with contextlib.suppress(Exception):
            self._thread.join(timeout=5)
        # On Windows the temp tree can hold locked handles briefly; never let cleanup
        # failures propagate into the pipeline.
        with contextlib.suppress(Exception):
            self._tmp.cleanup()


def _free_port(host: str = "127.0.0.1") -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])
    finally:
        sock.close()


def _build_site(repo_root: Path, config_file: Optional[Path], out_dir: Path, timeout_s: int) -> bool:
    cmd = [sys.executable, "-m", "mkdocs", "build", "-q", "-d", str(out_dir)]
    if config_file:
        cmd += ["-f", str(config_file)]
    try:
        proc = subprocess.run(cmd, cwd=str(repo_root), timeout=timeout_s, check=False)
    except Exception:  # noqa: BLE001
        return False
    return proc.returncode == 0


def _wait_ready(base_url: str, timeout_s: float) -> bool:
    deadline = time.time() + timeout_s
    url = base_url.rstrip("/") + "/"
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:  # noqa: S310
                if 200 <= int(resp.status) < 500:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(0.3)
    return False


def serve_docs_site(
    repo_root: Path | str,
    config_file: Optional[Path | str] = None,
    host: str = "127.0.0.1",
    port: Optional[int] = None,
    build_timeout_s: int = 600,
    ready_timeout_s: float = 20.0,
) -> Optional[DocsSiteServer]:
    """Build and serve the MkDocs site locally. Returns ``None`` on any failure."""
    repo_root = Path(repo_root)
    config_path = Path(config_file) if config_file else None

    try:
        import mkdocs  # noqa: F401
    except Exception:  # noqa: BLE001
        print("[docs-site] skipped: mkdocs is not installed")
        return None

    tmp: "tempfile.TemporaryDirectory[str]" = tempfile.TemporaryDirectory(prefix="veriops-docs-site-")
    site_dir = Path(tmp.name) / "site"

    if not _build_site(repo_root, config_path, site_dir, build_timeout_s):
        print("[docs-site] skipped: mkdocs build failed")
        with contextlib.suppress(Exception):
            tmp.cleanup()
        return None

    if not (site_dir / "index.html").exists():
        print("[docs-site] skipped: build produced no index.html")
        with contextlib.suppress(Exception):
            tmp.cleanup()
        return None

    handler = functools.partial(_QuietHandler, directory=str(site_dir))
    chosen_port = int(port) if port else _free_port(host)
    try:
        httpd = _ThreadingHTTPServer((host, chosen_port), handler)
    except OSError:
        # Requested port is busy; fall back to an ephemeral one.
        chosen_port = _free_port(host)
        try:
            httpd = _ThreadingHTTPServer((host, chosen_port), handler)
        except OSError:
            print("[docs-site] skipped: could not bind a local port")
            with contextlib.suppress(Exception):
                tmp.cleanup()
            return None

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{host}:{chosen_port}"

    if not _wait_ready(base_url, ready_timeout_s):
        print(f"[docs-site] skipped: site did not become ready at {base_url}")
        with contextlib.suppress(Exception):
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
            tmp.cleanup()
        return None

    print(f"[docs-site] serving built docs at {base_url}")
    return DocsSiteServer(base_url, site_dir, httpd, thread, tmp)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and serve MkDocs docs locally")
    parser.add_argument("--config-file", default="", help="Path to mkdocs.yml (optional)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="0 selects a free port")
    parser.add_argument("--seconds", type=int, default=0, help="Serve for N seconds then stop (0 = until Ctrl+C)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    config_file = args.config_file.strip() or None
    server = serve_docs_site(
        repo_root,
        config_file=config_file,
        host=args.host,
        port=args.port or None,
    )
    if server is None:
        return 1

    print(server.base_url)
    try:
        if args.seconds > 0:
            time.sleep(args.seconds)
        else:
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
