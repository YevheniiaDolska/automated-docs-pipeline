from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.generate_api_test_assets import generate_assets, merge_cases


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
    assert {"Title", "Section", "Type", "Priority", "Origin", "Preconditions", "Steps", "Expected Result", "Refs"} <= set(
        rows[0].keys()
    )

    # All auto-generated cases have merge metadata
    for case in cases["cases"]:
        assert case["origin"] == "auto"
        assert case["customized"] is False
        assert case["needs_review"] is False
        assert case["spec_hash"]


MINI_SPEC = """
openapi: 3.0.3
info:
  title: Demo API
  version: "1.0.0"
paths:
  /items/{id}:
    get:
      operationId: getItem
      summary: Get item
      tags: [Items]
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: OK
        "404":
          description: Not found
""".strip() + "\n"


def _run_generate(tmp_path: Path, spec_text: str = MINI_SPEC) -> dict:
    spec = tmp_path / "openapi.yaml"
    spec.write_text(spec_text, encoding="utf-8")
    out_dir = tmp_path / "reports" / "api-test-assets"
    csv_path = out_dir / "testrail.csv"
    zephyr_path = out_dir / "zephyr.json"
    generate_assets(spec, out_dir, csv_path, zephyr_path)
    return json.loads((out_dir / "api_test_cases.json").read_text(encoding="utf-8"))


def test_first_run_no_existing(tmp_path: Path) -> None:
    """First run with no existing cases creates clean output."""
    data = _run_generate(tmp_path)
    assert len(data["cases"]) >= 2
    assert data["summary"]["manual_cases"] == 0
    assert data["summary"]["customized_cases"] == 0
    ids = [c["id"] for c in data["cases"]]
    assert len(ids) == len(set(ids)), "Duplicate IDs detected"


def test_merge_no_duplicates(tmp_path: Path) -> None:
    """Running twice produces no duplicate IDs."""
    _run_generate(tmp_path)
    data = _run_generate(tmp_path)
    ids = [c["id"] for c in data["cases"]]
    assert len(ids) == len(set(ids)), "Duplicate IDs after second run"


def test_merge_preserves_manual_cases(tmp_path: Path) -> None:
    """Manual cases survive re-generation."""
    data = _run_generate(tmp_path)

    # Inject a manual case
    manual_case = {
        "id": "TC-manual-business-logic-1",
        "title": "Order status transition: pending to shipped",
        "suite": "Business Logic",
        "operation_id": "manual",
        "traceability": {"method": "POST", "path": "/orders/ship", "operation_id": "manual"},
        "preconditions": ["Order exists in pending status."],
        "steps": ["Call POST /orders/ship with order_id.", "Verify status changes to shipped."],
        "expected_result": "Order status is shipped and tracking number is assigned.",
        "priority": "high",
        "type": "functional",
        "origin": "manual",
        "customized": False,
        "needs_review": False,
        "review_reason": None,
        "spec_hash": "",
    }
    data["cases"].append(manual_case)

    cases_path = tmp_path / "reports" / "api-test-assets" / "api_test_cases.json"
    cases_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Re-generate
    result = _run_generate(tmp_path)
    ids = [c["id"] for c in result["cases"]]
    assert "TC-manual-business-logic-1" in ids
    manual = next(c for c in result["cases"] if c["id"] == "TC-manual-business-logic-1")
    assert manual["origin"] == "manual"
    assert manual["title"] == "Order status transition: pending to shipped"
    assert result["summary"]["manual_cases"] == 1


def test_merge_preserves_customized_cases(tmp_path: Path) -> None:
    """Customized auto cases are not overwritten."""
    data = _run_generate(tmp_path)

    # Mark one auto case as customized with QA edits
    target = data["cases"][0]
    target["customized"] = True
    target["steps"] = ["Custom step 1: check business rule.", "Custom step 2: verify side effect."]
    target["expected_result"] = "Custom expected result from QA."

    cases_path = tmp_path / "reports" / "api-test-assets" / "api_test_cases.json"
    cases_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Re-generate (same spec, so spec_hash unchanged)
    result = _run_generate(tmp_path)
    customized = next(c for c in result["cases"] if c["id"] == target["id"])
    assert customized["customized"] is True
    assert customized["steps"][0] == "Custom step 1: check business rule."
    assert customized["expected_result"] == "Custom expected result from QA."
    assert customized["needs_review"] is False


def test_merge_flags_stale_customized(tmp_path: Path) -> None:
    """Customized case gets needs_review when spec changes."""
    data = _run_generate(tmp_path)

    target = data["cases"][0]
    target["customized"] = True
    target["steps"] = ["Custom step from QA."]
    original_hash = target["spec_hash"]

    cases_path = tmp_path / "reports" / "api-test-assets" / "api_test_cases.json"
    cases_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Change the spec (add a response code -> changes spec_hash)
    changed_spec = MINI_SPEC.replace(
        '"404":\n          description: Not found',
        '"404":\n          description: Not found\n        "401":\n          description: Unauthorized',
    )
    result = _run_generate(tmp_path, spec_text=changed_spec)

    flagged = next(c for c in result["cases"] if c["id"] == target["id"])
    assert flagged["customized"] is True
    assert flagged["needs_review"] is True
    assert "API spec changed" in (flagged.get("review_reason") or "")
    assert result["summary"]["needs_review_cases"] >= 1


def test_merge_drops_stale_auto_cases(tmp_path: Path) -> None:
    """Auto cases for removed operations are dropped."""
    data = _run_generate(tmp_path)
    original_count = len(data["cases"])
    assert original_count >= 2

    # Re-generate with a spec that has no paths (all operations removed)
    empty_spec = """
openapi: 3.0.3
info:
  title: Demo API
  version: "2.0.0"
paths: {}
""".strip() + "\n"
    result = _run_generate(tmp_path, spec_text=empty_spec)
    assert len(result["cases"]) == 0
    assert result["summary"]["merge_stats"]["auto_dropped"] == original_count


def test_merge_unit_function() -> None:
    """Direct unit test of merge_cases function."""
    new_cases = [
        {"id": "TC-a", "origin": "auto", "customized": False, "spec_hash": "aaa", "title": "A new"},
        {"id": "TC-b", "origin": "auto", "customized": False, "spec_hash": "bbb", "title": "B new"},
    ]
    existing_cases = [
        {"id": "TC-a", "origin": "auto", "customized": False, "spec_hash": "aaa", "title": "A old"},
        {"id": "TC-b", "origin": "auto", "customized": True, "spec_hash": "xxx", "title": "B customized",
         "needs_review": False, "review_reason": None},
        {"id": "TC-manual-1", "origin": "manual", "customized": False, "spec_hash": "", "title": "Manual"},
        {"id": "TC-stale", "origin": "auto", "customized": False, "spec_hash": "zzz", "title": "Stale auto"},
    ]

    merged, stats = merge_cases(new_cases, existing_cases)
    ids = [c["id"] for c in merged]

    # No duplicates
    assert len(ids) == len(set(ids))

    # TC-a: pure auto, same hash -> kept/updated
    a = next(c for c in merged if c["id"] == "TC-a")
    assert a["title"] == "A new"  # overwritten

    # TC-b: customized, hash changed -> flagged
    b = next(c for c in merged if c["id"] == "TC-b")
    assert b["title"] == "B customized"  # preserved
    assert b["needs_review"] is True

    # Manual preserved
    assert "TC-manual-1" in ids

    # Stale auto dropped
    assert "TC-stale" not in ids

    assert stats["manual_preserved"] == 1
    assert stats["customized_flagged"] == 1
    assert stats["auto_dropped"] == 1
