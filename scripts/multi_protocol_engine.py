#!/usr/bin/env python3
"""Protocol adapters and orchestration for multi-protocol docs-ops."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.api_protocols import default_asyncapi_ws_endpoint, default_websocket_endpoint


@dataclass
class StageResult:
    stage: str
    protocol: str
    ok: bool
    rc: int
    command: list[str]
    details: dict[str, Any]


class ProtocolAdapter:
    def __init__(self, protocol: str, settings: dict[str, Any], *, repo_root: Path, scripts_dir: Path) -> None:
        self.protocol = protocol
        self.settings = settings
        self.repo_root = repo_root
        self.scripts_dir = scripts_dir
        self.py = sys.executable

    def _mode(self) -> str:
        return str(self.settings.get("mode", "api-first")).strip().lower()

    def _code_first_export_cmd(self) -> str:
        if self.protocol == "graphql":
            return str(self.settings.get("code_first_schema_export_cmd", "")).strip()
        if self.protocol == "grpc":
            return str(self.settings.get("code_first_proto_export_cmd", "")).strip()
        if self.protocol in {"asyncapi", "websocket"}:
            return str(self.settings.get("code_first_contract_export_cmd", "")).strip()
        return ""

    def _run(self, stage: str, cmd: list[str], *, allow_fail: bool) -> StageResult:
        print(f"[{self.protocol}:{stage}] $ {' '.join(cmd)}")
        completed = subprocess.run(cmd, cwd=str(self.repo_root), check=False)
        ok = completed.returncode == 0
        if not ok and not allow_fail:
            raise RuntimeError(f"{self.protocol}:{stage} failed rc={completed.returncode}")
        return StageResult(stage=stage, protocol=self.protocol, ok=ok, rc=completed.returncode, command=cmd, details={})

    def _run_shell(self, stage: str, command: str, *, allow_fail: bool) -> StageResult:
        print(f"[{self.protocol}:{stage}] $ {command}")
        completed = subprocess.run(command, cwd=str(self.repo_root), shell=True, check=False)
        ok = completed.returncode == 0
        if not ok and not allow_fail:
            raise RuntimeError(f"{self.protocol}:{stage} failed rc={completed.returncode}")
        return StageResult(
            stage=stage,
            protocol=self.protocol,
            ok=ok,
            rc=completed.returncode,
            command=["sh", "-lc", command],
            details={},
        )

    def source(self) -> str:
        if self.protocol == "rest":
            return str(self.settings.get("spec_path", "api/openapi.yaml"))
        if self.protocol == "graphql":
            return str(self.settings.get("schema_path", "api/schema.graphql"))
        if self.protocol == "grpc":
            proto_paths = self.settings.get("proto_paths", ["api/proto"])
            if isinstance(proto_paths, list) and proto_paths:
                return str(proto_paths[0])
            return "api/proto"
        if self.protocol == "asyncapi":
            return str(self.settings.get("spec_path", "api/asyncapi.yaml"))
        if self.protocol == "websocket":
            return str(self.settings.get("contract_path", "api/websocket.yaml"))
        raise ValueError(f"Unsupported protocol: {self.protocol}")

    def notes_path(self) -> str:
        if self.protocol == "graphql":
            return str(self.settings.get("notes_path", "notes/graphql-api-planning.md"))
        if self.protocol == "grpc":
            return str(self.settings.get("notes_path", "notes/grpc-api-planning.md"))
        if self.protocol == "asyncapi":
            return str(self.settings.get("notes_path", "notes/asyncapi-planning.md"))
        if self.protocol == "websocket":
            return str(self.settings.get("notes_path", "notes/websocket-api-planning.md"))
        return str(self.settings.get("notes_path", "notes/api-planning.md"))

    def maybe_generate_contract_from_notes(self, *, allow_fail: bool) -> StageResult | None:
        if self.protocol == "rest":
            return None
        if not bool(self.settings.get("generate_from_notes", True)):
            return None

        source = (self.repo_root / self.source()).resolve()
        source_exists = source.exists()
        if source.is_dir():
            source_exists = any(source.rglob("*.proto")) if self.protocol == "grpc" else source_exists
        if source_exists:
            return None

        notes = (self.repo_root / self.notes_path()).resolve()
        if not notes.exists():
            if not allow_fail:
                raise FileNotFoundError(f"{self.protocol}: planning notes not found: {notes}")
            return StageResult(
                stage="contract_from_notes_generation",
                protocol=self.protocol,
                ok=False,
                rc=2,
                command=["missing_notes", str(notes)],
                details={"notes_path": str(notes), "source": str(source)},
            )

        project_name = str(
            self.settings.get("project_name")
            or self.settings.get("project_slug")
            or self.repo_root.name
        ).strip() or "API Project"

        cmd = [
            self.py,
            str(self.scripts_dir / "generate_protocol_contract_from_planning_notes.py"),
            "--protocol",
            self.protocol,
            "--notes",
            str(notes),
            "--output",
            self.source(),
            "--project-name",
            project_name,
        ]
        result = self._run("contract_from_notes_generation", cmd, allow_fail=allow_fail)
        result.details["notes_path"] = str(notes)
        result.details["source"] = str(source)
        result.details["project_name"] = project_name
        return result

    def ingest(self, *, allow_fail: bool) -> StageResult:
        mode = self._mode()
        export_cmd = self._code_first_export_cmd()
        if mode in {"code-first", "hybrid"} and export_cmd:
            export_result = self._run_shell("code_first_export", export_cmd, allow_fail=allow_fail)
            if not export_result.ok and not allow_fail:
                raise RuntimeError(f"{self.protocol}:code_first_export failed rc={export_result.rc}")

        source = (self.repo_root / self.source()).resolve()
        ok = source.exists()
        rc = 0 if ok else 2
        if not ok and not allow_fail:
            raise FileNotFoundError(f"{self.protocol}: source not found: {source}")
        return StageResult(
            stage="ingest",
            protocol=self.protocol,
            ok=ok,
            rc=rc,
            command=["exists", str(source)],
            details={"source": str(source)},
        )

    def lint(self, *, allow_fail: bool) -> StageResult:
        if self.protocol == "rest":
            cmd = [self.py, str(self.scripts_dir / "validate_openapi_contract.py"), self.source()]
        elif self.protocol == "graphql":
            cmd = [
                self.py,
                str(self.scripts_dir / "run_protocol_lint_stack.py"),
                "--protocol",
                "graphql",
                "--source",
                self.source(),
                "--json-report",
                str(self.repo_root / "reports" / "graphql_lint_stack_report.json"),
            ]
        elif self.protocol == "grpc":
            cmd = [
                self.py,
                str(self.scripts_dir / "run_protocol_lint_stack.py"),
                "--protocol",
                "grpc",
                "--source",
                self.source(),
                "--json-report",
                str(self.repo_root / "reports" / "grpc_lint_stack_report.json"),
            ]
        elif self.protocol == "asyncapi":
            cmd = [
                self.py,
                str(self.scripts_dir / "run_protocol_lint_stack.py"),
                "--protocol",
                "asyncapi",
                "--source",
                self.source(),
                "--json-report",
                str(self.repo_root / "reports" / "asyncapi_lint_stack_report.json"),
            ]
        elif self.protocol == "websocket":
            cmd = [
                self.py,
                str(self.scripts_dir / "run_protocol_lint_stack.py"),
                "--protocol",
                "websocket",
                "--source",
                self.source(),
                "--json-report",
                str(self.repo_root / "reports" / "websocket_lint_stack_report.json"),
            ]
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")
        return self._run("lint", cmd, allow_fail=allow_fail)

    def contract_validation(self, *, allow_fail: bool) -> StageResult:
        if self.protocol == "rest":
            cmd = [self.py, str(self.scripts_dir / "validate_openapi_contract.py"), self.source()]
        elif self.protocol == "graphql":
            cmd = [self.py, str(self.scripts_dir / "validate_graphql_contract.py"), self.source()]
        elif self.protocol == "grpc":
            cmd = [self.py, str(self.scripts_dir / "validate_proto_contract.py"), "--proto", self.source()]
        elif self.protocol == "asyncapi":
            cmd = [self.py, str(self.scripts_dir / "validate_asyncapi_contract.py"), self.source()]
        elif self.protocol == "websocket":
            cmd = [self.py, str(self.scripts_dir / "validate_websocket_contract.py"), self.source()]
        else:
            raise ValueError(f"Unsupported protocol: {self.protocol}")
        return self._run("contract_validation", cmd, allow_fail=allow_fail)

    def regression(self, *, allow_fail: bool) -> StageResult:
        source = self.source()
        snapshot = str(self.settings.get("regression_snapshot_path", "")).strip()
        if not snapshot:
            src = Path(source)
            if src.is_dir():
                snapshot = str(src / f".{self.protocol}-regression.json")
            else:
                snapshot = str(src.parent / f".{self.protocol}-regression.json")

        cmd = [
            self.py,
            str(self.scripts_dir / "check_protocol_regression.py"),
            "--protocol",
            self.protocol,
            "--snapshot",
            snapshot,
            "--input",
            source,
        ]
        if bool(self.settings.get("update_regression_snapshot", False)):
            cmd.append("--update")
        result = self._run("regression", cmd, allow_fail=True)
        if result.rc == 2:
            bootstrap_cmd = [
                self.py,
                str(self.scripts_dir / "check_protocol_regression.py"),
                "--protocol",
                self.protocol,
                "--snapshot",
                snapshot,
                "--input",
                source,
                "--update",
            ]
            bootstrap = self._run("regression_bootstrap", bootstrap_cmd, allow_fail=allow_fail)
            result.details["bootstrap_rc"] = bootstrap.rc
            if bootstrap.ok:
                result.ok = True
                result.rc = 0
        if not result.ok and not allow_fail:
            raise RuntimeError(f"{self.protocol}:regression failed rc={result.rc}")
        return result

    def docs_generation(self, *, allow_fail: bool) -> StageResult:
        output = str(self.settings.get("generated_docs_output", f"docs/reference/{self.protocol}-api.md"))
        cmd = [
            self.py,
            str(self.scripts_dir / "generate_protocol_docs.py"),
            "--protocol",
            self.protocol,
            "--source",
            self.source(),
            "--output",
            output,
        ]
        mode = self._mode()
        if mode:
            cmd.extend(["--mode", mode])
        if self.protocol == "graphql":
            endpoint = str(self.settings.get("graphql_endpoint", "")).strip()
            if endpoint:
                cmd.extend(["--endpoint", endpoint])
        elif self.protocol == "grpc":
            endpoint = str(self.settings.get("grpc_gateway_endpoint", "")).strip()
            if endpoint:
                cmd.extend(["--endpoint", endpoint])
        elif self.protocol == "asyncapi":
            ws_endpoint = str(self.settings.get("asyncapi_ws_endpoint", "")).strip() or default_asyncapi_ws_endpoint()
            http_endpoint = str(self.settings.get("asyncapi_http_publish_endpoint", "")).strip()
            if ws_endpoint:
                cmd.extend(["--ws-endpoint", ws_endpoint])
            if http_endpoint:
                cmd.extend(["--http-endpoint", http_endpoint])
        elif self.protocol == "websocket":
            endpoint = str(self.settings.get("websocket_endpoint", "")).strip() or default_websocket_endpoint()
            if endpoint:
                cmd.extend(["--ws-endpoint", endpoint])

        result = self._run("docs_generation", cmd, allow_fail=allow_fail)
        result.details["generated_doc"] = output
        return result

    def quality_gates(self, *, allow_fail: bool, generated_doc: str | None = None) -> list[StageResult]:
        results: list[StageResult] = []
        target_doc = generated_doc or str(self.settings.get("generated_docs_output", f"docs/reference/{self.protocol}-api.md"))
        quality_suite = self.scripts_dir / "run_protocol_docs_quality_suite.py"
        if self.protocol in {"graphql", "grpc", "asyncapi", "websocket"} and quality_suite.exists():
            required_languages = self.settings.get("required_languages", ["curl", "javascript", "python"])
            if isinstance(required_languages, list):
                required_languages_csv = ",".join(str(v).strip() for v in required_languages if str(v).strip())
            else:
                required_languages_csv = "curl,javascript,python"
            quality_cmd = [
                self.py,
                str(quality_suite),
                "--protocol",
                self.protocol,
                "--generated-doc",
                target_doc,
                "--docs-root",
                str(self.settings.get("docs_root", "docs")),
                "--reports-dir",
                str(self.settings.get("quality_reports_dir", "reports")),
                "--required-languages",
                required_languages_csv or "curl,javascript,python",
                "--glossary",
                str(self.settings.get("glossary_path", "glossary.yml")),
                "--json-report",
                str(self.settings.get("quality_suite_report", f"reports/{self.protocol}_quality_suite_report.json")),
                "--semantic-required",
            ]
            autofix_attempts_raw = self.settings.get("semantic_autofix_max_attempts", 3)
            try:
                autofix_attempts = max(1, int(autofix_attempts_raw))
            except Exception:  # noqa: BLE001
                autofix_attempts = 3

            attempt = 1
            while True:
                suite_result = self._run("quality_suite", quality_cmd, allow_fail=True)
                suite_result.stage = "semantic_lint_and_quality_suite"
                suite_result.details["attempt"] = attempt
                suite_result.details["max_attempts"] = autofix_attempts
                results.append(suite_result)
                if suite_result.ok:
                    break

                if attempt >= autofix_attempts:
                    if not allow_fail:
                        raise RuntimeError(
                            f"{self.protocol}:quality_suite semantic consistency failed "
                            f"after {autofix_attempts} attempts"
                        )
                    break

                regen = self.docs_generation(allow_fail=True)
                regen.stage = "docs_regeneration"
                regen.details["attempt"] = attempt + 1
                regen.details["reason"] = "semantic_consistency_autofix"
                results.append(regen)

                if not regen.ok:
                    if not allow_fail:
                        raise RuntimeError(
                            f"{self.protocol}:docs_regeneration failed during semantic autofix "
                            f"(attempt {attempt + 1})"
                        )
                    break
                attempt += 1
        frontmatter = self.scripts_dir / "validate_frontmatter.py"
        schema_path = self.repo_root / "docs-schema.yml"
        if frontmatter.exists() and schema_path.exists():
            results.append(self._run("quality_gate_frontmatter", [self.py, str(frontmatter)], allow_fail=allow_fail))
        snippets = self.scripts_dir / "lint_code_snippets.py"
        if snippets.exists():
            results.append(self._run("quality_gate_snippets", [self.py, str(snippets), target_doc], allow_fail=True))
        if self.protocol in {"graphql", "grpc", "asyncapi", "websocket"} and bool(self.settings.get("self_verify_runtime", True)):
            verify_cmd = [
                self.py,
                str(self.scripts_dir / "run_protocol_self_verify.py"),
                "--protocol",
                self.protocol,
                "--json-report",
                str(self.repo_root / "reports" / f"{self.protocol}_self_verify_report.json"),
            ]
            if bool(self.settings.get("self_verify_require_endpoint", False)):
                verify_cmd.append("--require-endpoint")
            if self.protocol == "graphql":
                endpoint = str(self.settings.get("graphql_endpoint", "")).strip()
                if endpoint:
                    verify_cmd.extend(["--endpoint", endpoint])
            elif self.protocol == "grpc":
                endpoint = str(self.settings.get("grpc_gateway_endpoint", "")).strip()
                if endpoint:
                    verify_cmd.extend(["--endpoint", endpoint])
            elif self.protocol == "asyncapi":
                ws_endpoint = str(self.settings.get("asyncapi_ws_endpoint", "")).strip() or default_asyncapi_ws_endpoint()
                http_endpoint = str(self.settings.get("asyncapi_http_publish_endpoint", "")).strip()
                if ws_endpoint:
                    verify_cmd.extend(["--ws-endpoint", ws_endpoint])
                if http_endpoint:
                    verify_cmd.extend(["--http-endpoint", http_endpoint])
            elif self.protocol == "websocket":
                ws_endpoint = str(self.settings.get("websocket_endpoint", "")).strip() or default_websocket_endpoint()
                if ws_endpoint:
                    verify_cmd.extend(["--ws-endpoint", ws_endpoint])
                http_endpoint = str(self.settings.get("websocket_http_bridge_endpoint", "")).strip()
                if http_endpoint:
                    verify_cmd.extend(["--http-endpoint", http_endpoint])
            results.append(self._run("quality_gate_self_verify", verify_cmd, allow_fail=allow_fail))
        return results

    def test_assets(self, *, allow_fail: bool) -> StageResult:
        output_dir = str(self.settings.get("test_assets_output_dir", "reports/api-test-assets"))
        cmd = [
            self.py,
            str(self.scripts_dir / "generate_protocol_test_assets.py"),
            "--protocols",
            self.protocol,
            "--source",
            self.source(),
            "--output-dir",
            output_dir,
            "--testrail-csv",
            str(self.settings.get("testrail_csv", "reports/api-test-assets/testrail_test_cases.csv")),
            "--zephyr-json",
            str(self.settings.get("zephyr_json", "reports/api-test-assets/zephyr_test_cases.json")),
        ]
        result = self._run("test_assets", cmd, allow_fail=allow_fail)
        coverage_cmd = [
            self.py,
            str(self.scripts_dir / "validate_protocol_test_coverage.py"),
            "--cases-json",
            str(Path(output_dir) / "api_test_cases.json"),
            "--report",
            str(Path(output_dir) / "coverage_report.json"),
        ]
        coverage = self._run("test_assets_coverage", coverage_cmd, allow_fail=allow_fail)
        result.details["coverage_ok"] = coverage.ok
        result.details["coverage_rc"] = coverage.rc
        if not coverage.ok:
            result.ok = False
            result.rc = coverage.rc
        return result

    def upload(self, *, allow_fail: bool) -> StageResult:
        output_dir = str(self.settings.get("test_assets_output_dir", "reports/api-test-assets"))
        cmd = [
            self.py,
            str(self.scripts_dir / "upload_api_test_assets.py"),
            "--cases-json",
            str(Path(output_dir) / "api_test_cases.json"),
            "--report",
            str(self.settings.get("test_assets_upload_report", "reports/api-test-assets/upload_report.json")),
        ]
        if bool(self.settings.get("upload_test_assets_strict", False)):
            cmd.append("--strict")
        return self._run("upload", cmd, allow_fail=allow_fail)

    def publish(self, *, allow_fail: bool, generated_doc: str | None = None) -> StageResult:
        target_root = str(self.settings.get("publish_target_root", "docs/assets/protocols"))
        output = generated_doc or str(self.settings.get("generated_docs_output", f"docs/reference/{self.protocol}-api.md"))
        cmd = [
            self.py,
            str(self.scripts_dir / "publish_protocol_assets.py"),
            "--protocol",
            self.protocol,
            "--source",
            self.source(),
            "--generated-doc",
            output,
            "--target-root",
            target_root,
        ]
        return self._run("publish", cmd, allow_fail=allow_fail)
