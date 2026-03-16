from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.generate_api_test_assets import generate_assets


def test_generate_api_test_assets_outputs_expected_files(tmp_path: Path) -> None:
    spec = tmp_path / "openapi.yaml"
    spec.write_text(
        """
openapi: 3.0.3
info:
  title: Demo API
  version: "1.0.0"
paths:
  /users/{user_id}:
    get:
      operationId: getUser
      summary: Get user
      tags: [Users]
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: OK
        "401":
          description: Unauthorized
        "404":
          description: Not found
  /users:
    post:
      operationId: createUser
      summary: Create user
      tags: [Users]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email]
              properties:
                email:
                  type: string
                  maxLength: 120
      responses:
        "201":
          description: Created
        "400":
          description: Bad request
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
""".strip()
        + "\n",
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports" / "api-test-assets"
    testrail_csv = out_dir / "testrail.csv"
    zephyr_json = out_dir / "zephyr.json"
    summary = generate_assets(spec, out_dir, testrail_csv, zephyr_json)

    assert summary["operations_count"] == 2
    assert summary["test_cases_count"] >= 6

    cases = json.loads((out_dir / "api_test_cases.json").read_text(encoding="utf-8"))
    matrix = json.loads((out_dir / "api_test_matrix.json").read_text(encoding="utf-8"))
    fuzz_props = json.loads((out_dir / "api_property_fuzz_scenarios.json").read_text(encoding="utf-8"))
    zephyr = json.loads(zephyr_json.read_text(encoding="utf-8"))
    report = json.loads((out_dir / "api_test_assets_report.json").read_text(encoding="utf-8"))

    assert cases["summary"]["operations_count"] == 2
    assert matrix["summary"]["operations"] == 2
    assert isinstance(fuzz_props["scenarios"], list)
    assert zephyr["count"] == len(zephyr["issues"])
    assert report["operations_count"] == 2

    with testrail_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {"Title", "Section", "Type", "Priority", "Preconditions", "Steps", "Expected Result", "Refs"} <= set(
        rows[0].keys()
    )
