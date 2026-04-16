from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))


def test_compile_module_uses_setup_filename_in_output_cwd(tmp_path: Path, monkeypatch) -> None:
    import compile_protected as mod

    source = tmp_path / "sample_mod.py"
    source.write_text("x = 1\n", encoding="utf-8")
    output_dir = tmp_path / "dist" / "compiled"
    output_dir.mkdir(parents=True)

    captured: dict[str, object] = {}

    class _Result:
        def __init__(self) -> None:
            self.returncode = 0
            self.stderr = ""
            self.stdout = ""

    def fake_run(cmd, cwd, check, capture_output, text):  # type: ignore[no-untyped-def]
        captured["cmd"] = list(cmd)
        captured["cwd"] = cwd
        # Simulate generated extension artifact.
        (output_dir / "sample_mod.cpython-310-x86_64-linux-gnu.so").write_bytes(b"so")
        return _Result()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    compiled = mod._compile_module(source, output_dir, "linux-x86_64")

    assert compiled is not None
    assert Path(captured["cwd"]) == output_dir
    # Must be a local filename because subprocess cwd is already output_dir.
    assert captured["cmd"][1] == "setup_sample_mod.py"
