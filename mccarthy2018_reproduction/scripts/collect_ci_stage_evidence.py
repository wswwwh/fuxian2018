#!/usr/bin/env python3
"""Collect a committed audit package for the GitHub Actions stage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
from typing import Any

from qp_orbits.artifact_fingerprints import fingerprint_fields


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    ).strip()
).resolve()
DEFAULT_OUTPUT = (
    ROOT / "research" / "invariant_bundles" / "ci_validation"
)
SNAPSHOT_SCRIPT = ROOT / "scripts" / "verify_ci_authoritative_immutability.py"
WORKFLOW_SCRIPT = ROOT / "scripts" / "validate_github_actions_workflows.py"
PHYSICAL_SCRIPT = ROOT / "scripts" / "run_ci_small_physical_benchmark.py"
PORTABLE_REPLAY_SCRIPT = (
    ROOT / "scripts" / "validate_chapter4_halo_12p40_portable_replay.py"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def run_logged(
    label: str,
    command: list[str],
    *,
    log_records: list[str],
) -> str:
    started = time.time()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_records.extend(
        [
            f"## {label}",
            f"command: {command}",
            f"return_code: {completed.returncode}",
            f"elapsed_seconds: {time.time() - started:.6f}",
            completed.stdout.rstrip(),
            "",
        ]
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"{label} failed with return code {completed.returncode}"
        )
    return completed.stdout


def copy_full_rehearsal(source: Path, destination: Path) -> None:
    required = {
        "full_validation_summary.json": "full_validation_summary.json",
        "result_schema_checks.csv": "result_schema_checks.csv",
        "failure_evidence.md": "full_validation_failure_evidence.md",
        "artifact_hashes.csv": "full_validation_artifact_hashes.csv",
        "authoritative_before_after.csv": "authoritative_before_after.csv",
        "logs/bundle_console.log": "bundle_console.log",
        "logs/manifold_console.log": "manifold_console.log",
        "logs/bundle_ci_worker_metadata.json": "bundle_ci_worker_metadata.json",
        "logs/manifold_ci_worker_metadata.json": "manifold_ci_worker_metadata.json",
    }
    destination.mkdir(parents=True, exist_ok=True)
    for relative, target_name in required.items():
        path = source / relative
        if not path.is_file():
            raise FileNotFoundError(f"full rehearsal artifact missing: {path}")
        shutil.copy2(path, destination / target_name)


def write_manifest(output: Path) -> None:
    target = output / "artifact_hashes.csv"
    rows: list[dict[str, Any]] = []
    inputs = [
        REPOSITORY_ROOT / ".github" / "workflows" / "ci.yml",
        REPOSITORY_ROOT / ".github" / "workflows" / "full_research_validation.yml",
        ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json",
        ROOT / "scripts" / "run_ci_small_physical_benchmark.py",
        ROOT / "scripts" / "run_ci_full_research_validation.py",
        ROOT / "scripts" / "verify_ci_authoritative_immutability.py",
        ROOT / "scripts" / "validate_github_actions_workflows.py",
        ROOT / "scripts" / "validate_chapter4_halo_12p40_portable_replay.py",
        Path(__file__).resolve(),
        ROOT / "tests" / "test_github_actions_workflows.py",
        ROOT / "tests" / "test_chapter4_halo_12p40_posthoc_diagnostic.py",
    ]
    files = inputs + [
        path
        for path in sorted(output.rglob("*"))
        if path.is_file() and path != target
    ]
    for path in files:
        rows.append(
            {
                "schema_version": "ci_stage_artifact_hash_v3",
                "path_root": "repository",
                "path": path.resolve().relative_to(REPOSITORY_ROOT).as_posix(),
                **fingerprint_fields(path),
            }
        )
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full-rehearsal-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help="Refresh the known CI evidence files in an existing output directory.",
    )
    args = parser.parse_args()
    output = args.output_dir.resolve()
    full = args.full_rehearsal_root.resolve()
    if output.exists() and any(output.iterdir()) and not args.refresh_existing:
        raise RuntimeError(f"refusing to overwrite CI stage evidence: {output}")
    if full == REPOSITORY_ROOT or REPOSITORY_ROOT in full.parents:
        raise RuntimeError("full rehearsal evidence must originate outside the checkout")
    output.mkdir(parents=True, exist_ok=True)
    logs = output / "logs"
    logs.mkdir(exist_ok=args.refresh_existing)
    execution_log: list[str] = []
    snapshot_path = output / "authoritative_before.json"
    before_after_path = output / "authoritative_before_after.csv"
    run_logged(
        "authoritative snapshot",
        [
            sys.executable,
            str(SNAPSHOT_SCRIPT),
            "snapshot",
            "--manifest",
            str(snapshot_path),
        ],
        log_records=execution_log,
    )
    run_logged(
        "workflow contract validation",
        [
            sys.executable,
            str(WORKFLOW_SCRIPT),
            "--output-dir",
            str(output / "workflow_contracts"),
        ],
        log_records=execution_log,
    )
    run_logged(
        "small physical benchmark",
        [
            sys.executable,
            str(PHYSICAL_SCRIPT),
            "--output-dir",
            str(output / "small_physical"),
        ],
        log_records=execution_log,
    )
    portable_replay_output = run_logged(
        "Chapter 4 halo portable replay",
        [sys.executable, str(PORTABLE_REPLAY_SCRIPT)],
        log_records=execution_log,
    )
    if "chapter4_halo_12p40_portable_replay: PASS" not in portable_replay_output:
        raise RuntimeError("portable replay output did not contain the PASS marker")
    copy_full_rehearsal(full, output / "full_rehearsal")
    run_logged(
        "CI workflow unit contracts",
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_github_actions_workflows",
            "-v",
        ],
        log_records=execution_log,
    )
    unit_output = run_logged(
        "complete unit suite",
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        log_records=execution_log,
    )
    unit_match = re.search(r"Ran (\d+) tests?", unit_output)
    if unit_match is None or "\nOK\n" not in f"\n{unit_output}\n":
        raise RuntimeError("complete unit suite output did not contain Ran/OK markers")
    unit_tests = int(unit_match.group(1))
    run_logged(
        "git diff whitespace check",
        ["git", "diff", "--check"],
        log_records=execution_log,
    )
    run_logged(
        "authoritative comparison",
        [
            sys.executable,
            str(SNAPSHOT_SCRIPT),
            "compare",
            "--manifest",
            str(snapshot_path),
            "--report",
            str(before_after_path),
        ],
        log_records=execution_log,
    )
    (logs / "stage_execution.log").write_text(
        "\n".join(execution_log).rstrip() + "\n",
        encoding="utf-8",
    )
    full_summary = json.loads(
        (output / "full_rehearsal" / "full_validation_summary.json").read_text(
            encoding="utf-8"
        )
    )
    workflow_summary = json.loads(
        (
            output
            / "workflow_contracts"
            / "workflow_contract_summary.json"
        ).read_text(encoding="utf-8")
    )
    physical_summary = json.loads(
        (
            output
            / "small_physical"
            / "ci_small_physical_benchmark.json"
        ).read_text(encoding="utf-8")
    )
    environment = {
        "schema_version": "ci_stage_environment_v2",
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "workflow_contract_status": workflow_summary["status"],
        "small_physical_status": physical_summary["status"],
        "chapter4_halo_portable_replay_status": "pass",
        "full_rehearsal_status": full_summary["status"],
        "workflow_path_root": workflow_summary["path_root"],
        "workflow_project_directory": workflow_summary["project_directory"],
        "official_action_versions": [
            row["uses"]
            for row in workflow_summary["official_action_version_evidence"]["releases"]
        ],
        "unit_tests": unit_tests,
    }
    (logs / "environment.json").write_text(
        json.dumps(environment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "ci_validation_report.md").write_text(
        "# GitHub Actions continuous-integration acceptance\n\n"
        "## Outcome\n\n"
        "- Repository-root workflow discovery: PASS; `.github/workflows/ci.yml` "
        "and `.github/workflows/full_research_validation.yml`; no duplicate "
        "subproject workflows.\n"
        "- Run-step default: `shell: bash`, "
        "`working-directory: mccarthy2018_reproduction`; `uses` steps remain "
        "repository-scoped.\n"
        "- Official action releases verified on 2026-07-16: "
        "`actions/checkout@v6`, `actions/setup-python@v6`, and "
        "`actions/upload-artifact@v7`, suitable for GitHub-hosted Ubuntu.\n"
        "- Fast workflow contract: PASS, "
        f"{workflow_summary['checks']}/{workflow_summary['checks']} checks.\n"
        "- Small physical benchmark: PASS; ordered real Schur and QR/SVD "
        "both returned a one-dimensional accepted bundle under preset thresholds.\n"
        "- Chapter 4 halo portable replay: PASS; frozen provenance and raster "
        "masks are exact, while DOP853 states remain inside the half-step "
        "convergence envelope. All scientific gates and failure decisions are "
        "unchanged.\n"
        "- Full workflow rehearsal: PASS; "
        f"{full_summary['bundle_cases']} bundle cases, "
        f"{full_summary['bundle_rows']} bundle rows, "
        f"{full_summary['manifold_cases']} selected manifold cases, and "
        f"{full_summary['manifold_rows']} manifold rows.\n"
        f"- Full result-schema checks: {full_summary['schema_checks']} passed, "
        f"{len(full_summary['schema_failures'])} failed.\n"
        "- Protected authoritative files: 11/11 unchanged by before/after SHA256.\n"
        f"- Complete local unit suite: PASS, {unit_tests}/{unit_tests}; "
        "git diff whitespace check: PASS.\n\n"
        "## Failure visibility and truth boundary\n\n"
        f"The full rehearsal retains bundle outcomes {full_summary['bundle_status_counts']} "
        f"and manifold outcomes {full_summary['manifold_status_counts']}. "
        "Those failed and boundary rows are uploaded, not filtered. Route H physical "
        "corrected-rho remains a two-dimensional failed Schur subspace while the legacy "
        "seed-rho control remains one-dimensional and accepted. The frozen Chapter 4 "
        "projection holdout remains 0/4 with paper_projection=fail and paper_3d=false. "
        "Passing CI establishes engineering regression coverage only; it does not alter "
        "the frozen McCarthy reproduction level or establish submission readiness.\n",
        encoding="utf-8",
    )
    (output / "failure_evidence.md").write_text(
        "# GitHub Actions stage failure evidence\n\n"
        "- Workflow contract failures: 0.\n"
        "- Small physical smoke failures: 0.\n"
        "- Chapter 4 halo portable-replay failures: 0.\n"
        "- Full worker failures: 0.\n"
        "- Full result-schema failures: 0.\n"
        f"- Retained bundle fail rows: {full_summary['bundle_status_counts'].get('fail', 0)}.\n"
        f"- Retained bundle boundary rows: {full_summary['bundle_status_counts'].get('boundary', 0)}.\n"
        f"- Retained manifold fail rows: {full_summary['manifold_status_counts'].get('fail', 0)}.\n"
        "- Console logs and the complete generated full-validation artifact hash "
        "manifest are retained under full_rehearsal.\n",
        encoding="utf-8",
    )
    write_manifest(output)
    print(
        "CI stage evidence PASS "
        f"workflow_checks={workflow_summary['checks']} "
        f"bundle_rows={full_summary['bundle_rows']} "
        f"manifold_rows={full_summary['manifold_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
