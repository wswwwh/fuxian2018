#!/usr/bin/env python3
"""Validate the two GitHub Actions workflow contracts without executing them."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json"


def load_workflow(path: Path) -> dict[str, Any]:
    parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"workflow is not a YAML mapping: {path}")
    return parsed


def scalar_commands(workflow: dict[str, Any]) -> str:
    return json.dumps(workflow, ensure_ascii=False, sort_keys=True)


def record(rows: list[dict[str, str]], check_id: str, passed: bool, detail: str) -> None:
    rows.append(
        {
            "schema_version": "github_actions_contract_check_v1",
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "detail": detail,
        }
    )


def validate(output: Path) -> list[dict[str, str]]:
    output.mkdir(parents=True, exist_ok=True)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    contract = config["workflow_contract"]
    fast_path = ROOT / contract["fast_workflow"]
    full_path = ROOT / contract["full_workflow"]
    fast_text = fast_path.read_text(encoding="utf-8")
    full_text = full_path.read_text(encoding="utf-8")
    fast = load_workflow(fast_path)
    full = load_workflow(full_path)
    fast_blob = scalar_commands(fast)
    full_blob = scalar_commands(full)
    rows: list[dict[str, str]] = []
    fast_on = fast.get("on", {})
    full_on = full.get("on", {})
    record(rows, "fast_yaml_parse", True, str(fast_path.relative_to(ROOT)))
    record(rows, "full_yaml_parse", True, str(full_path.relative_to(ROOT)))
    record(
        rows,
        "fast_push_pull_request",
        isinstance(fast_on, dict) and {"push", "pull_request"}.issubset(fast_on),
        "fast workflow must run on push and pull_request",
    )
    record(
        rows,
        "full_workflow_dispatch",
        isinstance(full_on, dict) and "workflow_dispatch" in full_on,
        "full workflow must be manually dispatchable",
    )
    for action_key in ("checkout_action", "setup_python_action"):
        expected = contract[action_key]
        record(
            rows,
            f"fast_{action_key}",
            expected in fast_text,
            expected,
        )
        record(
            rows,
            f"full_{action_key}",
            expected in full_text,
            expected,
        )
    expected_upload = contract["upload_artifact_action"]
    record(rows, "fast_artifact_action", expected_upload in fast_text, expected_upload)
    record(rows, "full_artifact_action", expected_upload in full_text, expected_upload)
    fast_requirements = {
        "import_checks": "import qp_orbits",
        "unit_tests": "unittest discover",
        "benchmark_registry_integrity": "test_invariant_bundle_benchmark_registry",
        "small_synthetic_bundle_tests": "test_bundle_phase_alignment",
        "one_small_physical_benchmark": "run_ci_small_physical_benchmark.py",
        "document_registry_consistency": "test_stage_g_delivery_artifacts",
        "git_diff_check": "git diff --check",
    }
    for check_id, needle in fast_requirements.items():
        record(rows, f"fast_{check_id}", needle in fast_blob, needle)
    full_requirements = {
        "isolated_controller": "run_ci_full_research_validation.py",
        "fifteen_case_bundle": "--max-bundle-wall-seconds",
        "selected_manifold": "--max-manifold-wall-seconds",
        "schema_check": "--check-only",
        "artifact_upload": "Upload full validation artifacts",
    }
    for check_id, needle in full_requirements.items():
        record(rows, f"full_{check_id}", needle in full_blob, needle)
    record(
        rows,
        "fast_read_only_permissions",
        fast.get("permissions", {}).get("contents") == "read",
        "permissions.contents=read",
    )
    record(
        rows,
        "full_read_only_permissions",
        full.get("permissions", {}).get("contents") == "read",
        "permissions.contents=read",
    )
    record(
        rows,
        "fast_runner_temp_output",
        "RUNNER_TEMP" in fast_text and "runner.temp" in fast_text,
        "generated evidence uses runner temporary storage",
    )
    record(
        rows,
        "full_runner_temp_output",
        "RUNNER_TEMP" in full_text and "runner.temp" in full_text,
        "full numerical outputs use runner temporary storage",
    )
    record(
        rows,
        "fast_no_direct_authoritative_campaign",
        "run_invariant_bundle_benchmarks.py" not in fast_text
        and "run_invariant_bundle_manifold_convergence.py" not in fast_text,
        "fast workflow does not invoke authoritative writers",
    )
    record(
        rows,
        "both_authoritative_hash_guard",
        "verify_ci_authoritative_immutability.py" in fast_text
        and "verify_ci_authoritative_immutability.py" in full_text,
        "before/after hash guard present",
    )
    csv_path = output / "workflow_contract_checks.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["status"] != "pass"]
    summary = {
        "schema_version": "github_actions_contract_summary_v1",
        "status": "PASS" if not failures else "FAIL",
        "checks": len(rows),
        "passed": len(rows) - len(failures),
        "failed": len(failures),
        "failed_check_ids": [row["check_id"] for row in failures],
        "fast_workflow": str(fast_path.relative_to(ROOT)).replace("\\", "/"),
        "full_workflow": str(full_path.relative_to(ROOT)).replace("\\", "/"),
        "truth_boundary": config["truth_boundaries"],
    }
    (output / "workflow_contract_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if failures:
        raise RuntimeError(f"workflow contract failures: {summary['failed_check_ids']}")
    print(f"workflow contract PASS checks={len(rows)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    validate(args.output_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
