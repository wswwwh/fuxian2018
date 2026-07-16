#!/usr/bin/env python3
"""Run full research validation outside the checkout and validate its schemas."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT / "src"))

import run_invariant_bundle_benchmarks as benchmark  # noqa: E402
import run_invariant_bundle_manifold_convergence as manifold  # noqa: E402
from run_independent_rerun_worker import (  # noqa: E402
    configure_benchmark,
    configure_manifold,
)


CONFIG = (
    ROOT / "research" / "invariant_bundles" / "configs" / "ci_validation.json"
)
REGISTRY = (
    ROOT / "research" / "invariant_bundles" / "benchmarks" / "benchmark_registry.csv"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def external_output_root(path: Path, *, require_existing: bool) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise RuntimeError(
            "full CI numerical output must be outside the repository checkout"
        )
    if require_existing and not resolved.is_dir():
        raise FileNotFoundError(f"full validation output is missing: {resolved}")
    return resolved


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    if not rows:
        raise RuntimeError(f"refusing to write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def worker(stage: str, output: Path, run_id: str, max_wall: float) -> None:
    output = external_output_root(output, require_existing=True)
    metadata: dict[str, Any] = {
        "schema_version": "ci_full_research_worker_v1",
        "stage": stage,
        "run_id": run_id,
        "pid": os.getpid(),
        "python_executable": sys.executable,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if stage == "bundle":
        configure_benchmark(output, run_id)
        benchmark.COCYCLE_DIR.mkdir(parents=True, exist_ok=True)
        if any(benchmark.COCYCLE_DIR.iterdir()):
            raise RuntimeError("CI cocycle directory was not empty at worker start")
        benchmark.run_campaign(refresh_cocycle=True, max_wall_seconds=max_wall)
        cocycles = sorted(benchmark.COCYCLE_DIR.glob("*.npz"))
        if len(cocycles) != benchmark.MAX_CASES:
            raise RuntimeError(
                f"fresh cocycle count {len(cocycles)} != {benchmark.MAX_CASES}"
            )
        metadata["fresh_cocycle_files"] = len(cocycles)
    elif stage == "manifold":
        configure_manifold(output, run_id)
        if not manifold.METHOD_CSV.is_file() or not manifold.METHOD_NPZ.is_file():
            raise RuntimeError("manifold worker cannot find isolated bundle outputs")
        manifold.run_campaign(max_wall_seconds=max_wall)
    else:
        raise ValueError(f"unknown worker stage: {stage}")
    metadata["completed_utc"] = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
    )
    metadata["status"] = "complete"
    metadata_path = output / "logs" / f"{stage}_ci_worker_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"CI research worker PASS stage={stage} pid={os.getpid()}")


def launch_worker(
    stage: str,
    output: Path,
    run_id: str,
    max_wall: float,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker-stage",
        stage,
        "--output-root",
        str(output),
        "--run-id",
        run_id,
        "--max-worker-wall-seconds",
        str(max_wall),
    ]
    log_path = output / "logs" / f"{stage}_console.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with log_path.open("wb") as stream:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=max_wall + 180.0,
            check=False,
        )
    record = {
        "stage": stage,
        "return_code": completed.returncode,
        "elapsed_seconds": time.time() - started,
        "console_log": str(log_path),
        "console_log_sha256": sha256(log_path),
    }
    if completed.returncode != 0:
        raise RuntimeError(
            f"{stage} worker failed with return code {completed.returncode}; "
            f"see {log_path}"
        )
    return record


def add_check(
    rows: list[dict[str, str]],
    check_id: str,
    passed: bool,
    observed: Any,
    expected: Any,
) -> None:
    rows.append(
        {
            "schema_version": "ci_full_result_schema_check_v1",
            "check_id": check_id,
            "status": "pass" if passed else "fail",
            "observed": json.dumps(observed, ensure_ascii=False, sort_keys=True),
            "expected": json.dumps(expected, ensure_ascii=False, sort_keys=True),
        }
    )


def result_checks(output: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    expected = config["full_validation"]
    csv_dir = output / "results" / "csv"
    npz_dir = output / "results" / "npz"
    method_path = csv_dir / "method_comparison.csv"
    manifold_path = csv_dir / "manifold_convergence.csv"
    method_rows = read_csv(method_path)
    manifold_rows = read_csv(manifold_path)
    registry_rows = read_csv(REGISTRY)
    checks: list[dict[str, str]] = []
    add_check(
        checks,
        "bundle_columns",
        list(method_rows[0]) == list(benchmark.METHOD_FIELDS),
        list(method_rows[0]),
        list(benchmark.METHOD_FIELDS),
    )
    add_check(
        checks,
        "bundle_rows",
        len(method_rows) == expected["bundle_rows"],
        len(method_rows),
        expected["bundle_rows"],
    )
    add_check(
        checks,
        "bundle_case_set",
        {row["case_id"] for row in method_rows}
        == {row["case_id"] for row in registry_rows},
        sorted({row["case_id"] for row in method_rows}),
        sorted({row["case_id"] for row in registry_rows}),
    )
    add_check(
        checks,
        "bundle_method_set",
        {row["method"] for row in method_rows} == set(benchmark.METHODS),
        sorted({row["method"] for row in method_rows}),
        sorted(benchmark.METHODS),
    )
    add_check(
        checks,
        "bundle_schema_version",
        {row["schema_version"] for row in method_rows}
        == {benchmark.SCHEMA_VERSION},
        sorted({row["schema_version"] for row in method_rows}),
        [benchmark.SCHEMA_VERSION],
    )
    cocycles = sorted((npz_dir / "cocycles").glob("*.npz"))
    add_check(
        checks,
        "fresh_cocycle_count",
        len(cocycles) == expected["fresh_cocycle_files"],
        len(cocycles),
        expected["fresh_cocycle_files"],
    )
    with np.load(npz_dir / "method_comparison.npz", allow_pickle=False) as archive:
        method_npz_keys = set(archive.files)
    add_check(
        checks,
        "bundle_npz_required_keys",
        {"schema_version", "run_id", "registry_sha256"}.issubset(method_npz_keys),
        sorted(method_npz_keys),
        ["schema_version", "run_id", "registry_sha256"],
    )
    add_check(
        checks,
        "manifold_columns",
        list(manifold_rows[0]) == list(manifold.FIELDS),
        list(manifold_rows[0]),
        list(manifold.FIELDS),
    )
    add_check(
        checks,
        "manifold_rows",
        len(manifold_rows) == expected["manifold_rows"],
        len(manifold_rows),
        expected["manifold_rows"],
    )
    add_check(
        checks,
        "manifold_case_set",
        {row["case_id"] for row in manifold_rows} == set(manifold.CASES),
        sorted({row["case_id"] for row in manifold_rows}),
        sorted(manifold.CASES),
    )
    add_check(
        checks,
        "manifold_method_set",
        {row["method"] for row in manifold_rows} == set(manifold.METHODS),
        sorted({row["method"] for row in manifold_rows}),
        sorted(manifold.METHODS),
    )
    add_check(
        checks,
        "manifold_schema_version",
        {row["schema_version"] for row in manifold_rows}
        == {manifold.SCHEMA_VERSION},
        sorted({row["schema_version"] for row in manifold_rows}),
        [manifold.SCHEMA_VERSION],
    )
    method_index = {
        (row["case_id"], row["method"]): row for row in method_rows
    }
    schur_method = "ordered_partial_real_schur_tracking"
    physical = method_index[("route_h_member_68", schur_method)]
    legacy = method_index[("route_h_member_68_legacy_dg_positive", schur_method)]
    route_boundary = (
        physical["bundle_dimension"] == "2"
        and physical["research_status"] == "fail"
        and legacy["bundle_dimension"] == "1"
        and legacy["research_status"] == "accepted"
    )
    add_check(
        checks,
        "route_h_physical_legacy_boundary",
        route_boundary,
        {
            "physical_dimension": physical["bundle_dimension"],
            "physical_status": physical["research_status"],
            "legacy_dimension": legacy["bundle_dimension"],
            "legacy_status": legacy["research_status"],
        },
        {
            "physical_dimension": "2",
            "physical_status": "fail",
            "legacy_dimension": "1",
            "legacy_status": "accepted",
        },
    )
    status_counts = Counter(row["research_status"] for row in method_rows)
    manifold_counts = Counter(row["status"] for row in manifold_rows)
    add_check(
        checks,
        "failed_bundle_cases_visible",
        status_counts["fail"] > 0,
        dict(status_counts),
        "at least one fail",
    )
    add_check(
        checks,
        "failed_manifold_cases_visible",
        manifold_counts["fail"] > 0,
        dict(manifold_counts),
        "at least one fail",
    )
    summary = {
        "schema_version": "ci_full_research_validation_summary_v1",
        "bundle_rows": len(method_rows),
        "bundle_cases": len({row["case_id"] for row in method_rows}),
        "bundle_status_counts": dict(status_counts),
        "manifold_rows": len(manifold_rows),
        "manifold_cases": len({row["case_id"] for row in manifold_rows}),
        "manifold_status_counts": dict(manifold_counts),
        "fresh_cocycle_files": len(cocycles),
        "route_h_physical_schur": {
            "bundle_dimension": int(physical["bundle_dimension"]),
            "status": physical["research_status"],
        },
        "route_h_legacy_schur": {
            "bundle_dimension": int(legacy["bundle_dimension"]),
            "status": legacy["research_status"],
        },
    }
    return checks, summary


def artifact_manifest(output: Path) -> None:
    manifest = output / "artifact_hashes.csv"
    rows = []
    for path in sorted(item for item in output.rglob("*") if item.is_file()):
        if path == manifest:
            continue
        rows.append(
            {
                "schema_version": "ci_full_artifact_hash_v1",
                "path": str(path.relative_to(output)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    write_csv(manifest, rows)


def validate_and_record(output: Path, run_id: str, processes: list[dict[str, Any]]) -> None:
    checks, summary = result_checks(output)
    failures = [row for row in checks if row["status"] != "pass"]
    write_csv(output / "result_schema_checks.csv", checks)
    summary.update(
        {
            "status": "PASS" if not failures else "FAIL",
            "run_id": run_id,
            "processes": processes,
            "schema_checks": len(checks),
            "schema_failures": [row["check_id"] for row in failures],
            "output_is_outside_checkout": True,
            "truth_boundary": (
                "Full CI validates reproducibility and schemas only. It does not "
                "change the frozen reproduction level, the Chapter 4 0/4 holdout, "
                "or submission-readiness status."
            ),
        }
    )
    (output / "full_validation_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "failure_evidence.md").write_text(
        "# Full-CI failure evidence\n\n"
        f"- Worker failures: 0.\n"
        f"- Result-schema failures: {len(failures)}.\n"
        f"- Bundle status counts: {summary['bundle_status_counts']}.\n"
        f"- Manifold status counts: {summary['manifold_status_counts']}.\n"
        "- Numerical failures and boundary cases remain present in generated CSV files.\n"
        "- All numerical outputs were written outside the checkout.\n",
        encoding="utf-8",
    )
    artifact_manifest(output)
    if failures:
        raise RuntimeError(
            f"full validation schema failures: {[row['check_id'] for row in failures]}"
        )


def controller(
    output: Path,
    *,
    max_bundle_wall: float,
    max_manifold_wall: float,
) -> None:
    output = external_output_root(output, require_existing=False)
    if output.exists() and any(output.iterdir()):
        raise RuntimeError(f"refusing to overwrite full validation evidence: {output}")
    output.mkdir(parents=True, exist_ok=True)
    run_id = (
        f"CI-FULL-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-"
        f"{uuid.uuid4().hex[:8].upper()}"
    )
    processes: list[dict[str, Any]] = []
    try:
        processes.append(
            launch_worker("bundle", output, run_id, max_bundle_wall)
        )
        processes.append(
            launch_worker("manifold", output, run_id, max_manifold_wall)
        )
        validate_and_record(output, run_id, processes)
    except Exception as error:
        failure_path = output / "failure_evidence.md"
        failure_path.parent.mkdir(parents=True, exist_ok=True)
        prior = failure_path.read_text(encoding="utf-8") if failure_path.is_file() else ""
        failure_path.write_text(
            prior
            + "\n# Controller exception\n\n"
            + f"- Exception type: {type(error).__name__}\n"
            + f"- Message: {error}\n",
            encoding="utf-8",
        )
        if any(output.rglob("*")):
            artifact_manifest(output)
        raise
    print(
        f"full research validation PASS run_id={run_id} "
        f"output={output}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--worker-stage", choices=("bundle", "manifold"))
    parser.add_argument("--run-id")
    parser.add_argument("--max-worker-wall-seconds", type=float)
    parser.add_argument("--max-bundle-wall-seconds", type=float, default=1800.0)
    parser.add_argument("--max-manifold-wall-seconds", type=float, default=1800.0)
    args = parser.parse_args()
    if args.worker_stage:
        if not args.run_id or args.max_worker_wall_seconds is None:
            parser.error("worker mode requires --run-id and --max-worker-wall-seconds")
        worker(
            args.worker_stage,
            args.output_root,
            args.run_id,
            args.max_worker_wall_seconds,
        )
        return 0
    output = external_output_root(
        args.output_root,
        require_existing=args.check_only,
    )
    if args.check_only:
        checks, _ = result_checks(output)
        failures = [row for row in checks if row["status"] != "pass"]
        if failures:
            raise RuntimeError(
                f"full validation check-only failures: {[row['check_id'] for row in failures]}"
            )
        print(f"full validation schema CHECK PASS checks={len(checks)}")
        return 0
    controller(
        output,
        max_bundle_wall=args.max_bundle_wall_seconds,
        max_manifold_wall=args.max_manifold_wall_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
