#!/usr/bin/env python3
"""Orchestrate an isolated fresh-process rerun and compare it to Stage F."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "independent_rerun.json"
OUTPUT_ROOT = RESEARCH / "independent_rerun"
RESULTS = OUTPUT_ROOT / "results"
LOGS = OUTPUT_ROOT / "logs"
HASHES = OUTPUT_ROOT / "hashes"
COMPARISON = OUTPUT_ROOT / "comparison_to_stage_f.csv"
REPORT = OUTPUT_ROOT / "independent_rerun_report.md"
FAILURE_EVIDENCE = LOGS / "failure_evidence.md"
PROCESS_MANIFEST = LOGS / "process_manifest.json"
ENVIRONMENT = LOGS / "environment.json"
ARTIFACT_HASHES = HASHES / "artifact_hashes.csv"
SOURCE_HASHES = HASHES / "source_inputs.csv"
AUTHORITATIVE_HASHES = HASHES / "authoritative_before_after.csv"
WORKER = ROOT / "scripts" / "run_independent_rerun_worker.py"
REFERENCE_METHOD = RESEARCH / "results" / "csv" / "method_comparison.csv"
REFERENCE_MANIFOLD = RESEARCH / "results" / "csv" / "manifold_convergence.csv"
SCHEMA = "independent_rerun_field_comparison_v1"

COMPARISON_FIELDS = [
    "schema_version", "independent_run_id", "table", "row_key", "field",
    "reference_value", "rerun_value", "comparison_kind", "absolute_difference",
    "relative_difference", "absolute_tolerance", "relative_tolerance",
    "match", "comparison_status", "notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def file_rows(paths: list[Path], stage: str) -> list[dict[str, Any]]:
    return [
        {
            "artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
            "stage": stage,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in paths
    ]


def launch_worker(stage: str, run_id: str, max_wall: float) -> dict[str, Any]:
    command = [
        sys.executable, str(WORKER), "--stage", stage,
        "--output-root", str(OUTPUT_ROOT), "--run-id", run_id,
        "--max-wall-seconds", str(max_wall),
    ]
    log_path = LOGS / f"{stage}_worker_console.log"
    started = time.time()
    with log_path.open("wb") as stream:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=stream,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        )
        pid = process.pid
        return_code = process.wait(timeout=max_wall + 120.0)
    ended = time.time()
    record = {
        "stage": stage,
        "pid": pid,
        "parent_pid": os.getpid(),
        "command": command,
        "python_executable": sys.executable,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
        "completed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ended)),
        "elapsed_seconds": ended - started,
        "return_code": return_code,
        "console_log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
        "console_log_sha256": sha256(log_path),
    }
    if return_code != 0:
        raise RuntimeError(f"fresh {stage} worker failed return_code={return_code}; see {log_path}")
    return record


def parse_number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def compare_tables(
    reference_path: Path,
    rerun_path: Path,
    *,
    table: str,
    key_fields: tuple[str, ...],
    run_id: str,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    reference_rows = read_csv(reference_path)
    rerun_rows = read_csv(rerun_path)
    reference_index = {tuple(row[field] for field in key_fields): row for row in reference_rows}
    rerun_index = {tuple(row[field] for field in key_fields): row for row in rerun_rows}
    if reference_index.keys() != rerun_index.keys():
        missing = reference_index.keys() - rerun_index.keys()
        extra = rerun_index.keys() - reference_index.keys()
        raise RuntimeError(f"{table} row-key mismatch missing={list(missing)[:3]} extra={list(extra)[:3]}")
    informational = set(config["informational_fields"])
    abs_tol = float(config["numeric_absolute_tolerance"])
    rel_tol = float(config["numeric_relative_tolerance"])
    output: list[dict[str, Any]] = []
    for key in sorted(reference_index):
        reference = reference_index[key]
        rerun = rerun_index[key]
        fields = list(reference.keys())
        if fields != list(rerun.keys()):
            raise RuntimeError(f"{table} schema mismatch for {key}")
        row_key = "|".join(key)
        for field in fields:
            left = reference[field]
            right = rerun[field]
            left_number = parse_number(left)
            right_number = parse_number(right)
            if field in key_fields:
                kind = "row_key"
                matched = left == right
                status = "pass" if matched else "fail"
                absolute = relative = ""
                notes = "exact row identity"
            elif field in informational:
                kind = "informational_provenance"
                matched = True
                status = "info"
                absolute = relative = ""
                notes = "recorded but excluded from scientific acceptance"
            elif left_number is not None and right_number is not None:
                kind = "numeric_scientific"
                if math.isnan(left_number) and math.isnan(right_number):
                    matched = True
                    absolute = relative = 0.0
                elif math.isfinite(left_number) and math.isfinite(right_number):
                    absolute = abs(right_number - left_number)
                    relative = absolute / max(abs(left_number), abs(right_number), np.finfo(float).tiny)
                    matched = absolute <= abs_tol + rel_tol * abs(left_number)
                else:
                    matched = left_number == right_number
                    absolute = relative = 0.0 if matched else float("inf")
                status = "pass" if matched else "fail"
                notes = "fixed numeric tolerance"
            else:
                kind = "exact_scientific"
                matched = left == right
                status = "pass" if matched else "fail"
                absolute = relative = ""
                notes = "exact classification/status/schema comparison"
            output.append({
                "schema_version": SCHEMA,
                "independent_run_id": run_id,
                "table": table,
                "row_key": row_key,
                "field": field,
                "reference_value": left,
                "rerun_value": right,
                "comparison_kind": kind,
                "absolute_difference": absolute,
                "relative_difference": relative,
                "absolute_tolerance": abs_tol if kind == "numeric_scientific" else "",
                "relative_tolerance": rel_tol if kind == "numeric_scientific" else "",
                "match": str(matched).lower(),
                "comparison_status": status,
                "notes": notes,
            })
    return output


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if OUTPUT_ROOT.exists():
        raise RuntimeError(
            "independent_rerun already exists; refusing to overwrite evidence. "
            "Archive or explicitly remove the prior isolated rerun before starting another."
        )
    OUTPUT_ROOT.mkdir(parents=True)
    LOGS.mkdir()
    HASHES.mkdir()
    RESULTS.mkdir()
    run_id = f"FRESH-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8].upper()}"

    protected_paths = [ROOT / relative for relative in config["authoritative_files_protected"]]
    before_rows = file_rows(protected_paths, "before")
    source_paths = [ROOT / relative for relative in config["frozen_inputs"]] + [
        ROOT / "scripts" / "run_invariant_bundle_benchmarks.py",
        ROOT / "scripts" / "run_invariant_bundle_manifold_convergence.py",
        WORKER,
        Path(__file__),
        CONFIG,
    ]
    write_csv(SOURCE_HASHES, file_rows(source_paths, "input"), ["artifact", "stage", "bytes", "sha256"])

    process_records = [
        launch_worker("bundle", run_id, float(config["max_bundle_wall_time_seconds"])),
        launch_worker("manifold", run_id, float(config["max_manifold_wall_time_seconds"])),
    ]
    PROCESS_MANIFEST.write_text(
        json.dumps(
            {
                "schema_version": "independent_rerun_process_manifest_v1",
                "independent_run_id": run_id,
                "controller_pid": os.getpid(),
                "processes": process_records,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    comparison_rows = compare_tables(
        REFERENCE_METHOD, RESULTS / "csv" / "method_comparison.csv",
        table="method_comparison", key_fields=("case_id", "method"),
        run_id=run_id, config=config,
    )
    comparison_rows.extend(compare_tables(
        REFERENCE_MANIFOLD, RESULTS / "csv" / "manifold_convergence.csv",
        table="manifold_convergence",
        key_fields=("case_id", "method", "perturbation_norm", "perturbation_sign"),
        run_id=run_id, config=config,
    ))
    write_csv(COMPARISON, comparison_rows, COMPARISON_FIELDS)

    after_rows = file_rows(protected_paths, "after")
    before_index = {row["artifact"]: row for row in before_rows}
    protected_comparison: list[dict[str, Any]] = []
    for row in after_rows:
        before = before_index[row["artifact"]]
        protected_comparison.append({
            "artifact": row["artifact"],
            "before_bytes": before["bytes"],
            "after_bytes": row["bytes"],
            "before_sha256": before["sha256"],
            "after_sha256": row["sha256"],
            "unchanged": str(before["sha256"] == row["sha256"] and before["bytes"] == row["bytes"]).lower(),
        })
    write_csv(
        AUTHORITATIVE_HASHES, protected_comparison,
        ["artifact", "before_bytes", "after_bytes", "before_sha256", "after_sha256", "unchanged"],
    )

    fail_rows = [row for row in comparison_rows if row["comparison_status"] == "fail"]
    scientific_rows = [row for row in comparison_rows if row["comparison_status"] != "info"]
    method_rows = read_csv(RESULTS / "csv" / "method_comparison.csv")
    manifold_rows = read_csv(RESULTS / "csv" / "manifold_convergence.csv")
    reference_method_rows = read_csv(REFERENCE_METHOD)
    reference_bundle_run = sorted({row["run_id"] for row in reference_method_rows})
    rerun_bundle_run = sorted({row["run_id"] for row in method_rows})
    classification_match = all(
        row["comparison_status"] != "fail"
        for row in comparison_rows
        if row["field"] in {"classification", "research_status", "bundle_dimension"}
    )
    manifold_acceptance_match = all(
        row["comparison_status"] != "fail"
        for row in comparison_rows
        if row["table"] == "manifold_convergence" and row["field"] in {"status", "failure_reason"}
    )
    authoritative_unchanged = all(row["unchanged"] == "true" for row in protected_comparison)
    overall = not fail_rows and classification_match and manifold_acceptance_match and authoritative_unchanged
    report_lines = [
        "# Independent fresh-process rerun report", "",
        f"- Independent run ID: `{run_id}`",
        f"- Bundle worker PID: `{process_records[0]['pid']}`; manifold worker PID: `{process_records[1]['pid']}`; controller PID: `{os.getpid()}`.",
        f"- Python executable: `{sys.executable}`.",
        f"- Fresh cocycle files: `{len(list((RESULTS / 'npz' / 'cocycles').glob('*.npz')))}`.",
        f"- Bundle rows: `{len(method_rows)}`; manifold rows: `{len(manifold_rows)}`.",
        f"- Reference bundle run ID(s): `{reference_bundle_run}`.",
        f"- Independent bundle run ID(s): `{rerun_bundle_run}`.",
        f"- Field comparison rows: `{len(comparison_rows)}`; scientific checks: `{len(scientific_rows)}`; failures: `{len(fail_rows)}`.",
        f"- Classification/dimension agreement: `{classification_match}`.",
        f"- Manifold status/failure-reason agreement: `{manifold_acceptance_match}`.",
        f"- Protected authoritative hashes unchanged: `{authoritative_unchanged}`.",
        f"- Overall acceptance: `{'PASS' if overall else 'FAIL'}`.",
        "", "## Isolation and cache semantics", "",
        "The bundle worker started in a new Python process with an empty isolated cocycle directory and `refresh_cocycle=True`. "
        "It regenerated all 15 cocycles and bundle tables under `independent_rerun/results`. The second new process read "
        "only those rerun bundle files for its 126-row manifold campaign. The committed Stage-F tables were opened by "
        "the controller only after both workers completed.",
        "", "## Comparison policy", "",
        f"Scientific numeric fields use `atol={config['numeric_absolute_tolerance']}` and `rtol={config['numeric_relative_tolerance']}`; "
        "classification, status, failure reason, dimensions, and schemas require exact agreement. Run IDs, runtimes, "
        "memory estimates, newly written cache hashes, method-NPZ hash, and source commit are provenance-only and remain "
        "visible as informational comparison rows.",
        "", "## Truth boundary", "",
        "A reproducible rerun confirms implementation stability only. It does not change the 54-figure engineering-coverage "
        "label, the Chapter 4 frozen `0/4` projection holdout, or any paper-equivalence claim. Route H physical failures "
        "remain present in the rerun.",
    ]
    if fail_rows:
        report_lines.extend(["", "## Mismatches", ""])
        for row in fail_rows[:50]:
            report_lines.append(
                f"- `{row['table']}::{row['row_key']}::{row['field']}` reference=`{row['reference_value']}` rerun=`{row['rerun_value']}`"
            )
    REPORT.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    FAILURE_EVIDENCE.write_text(
        "# Independent rerun failure evidence\n\n"
        f"Worker process failures: `0`. Scientific field mismatches: `{len(fail_rows)}`. "
        f"Protected-authoritative hash changes: `{sum(row['unchanged'] != 'true' for row in protected_comparison)}`.\n\n"
        + (
            "No failure was observed. Console logs, per-process metadata, and all informational provenance differences "
            "are nevertheless retained.\n"
            if not fail_rows else
            "All mismatches remain in `comparison_to_stage_f.csv`; none was filtered from the overall FAIL result.\n"
        ),
        encoding="utf-8",
    )
    ENVIRONMENT.write_text(
        json.dumps(
            {
                "schema_version": "independent_rerun_environment_v1",
                "independent_run_id": run_id,
                "platform": platform.platform(),
                "python": sys.version,
                "python_executable": sys.executable,
                "numpy": np.__version__,
                "controller_pid": os.getpid(),
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    artifact_paths = sorted(
        path for path in OUTPUT_ROOT.rglob("*")
        if path.is_file() and path != ARTIFACT_HASHES
    )
    write_csv(
        ARTIFACT_HASHES, file_rows(artifact_paths, "rerun_artifact"),
        ["artifact", "stage", "bytes", "sha256"],
    )
    if not overall:
        raise RuntimeError(
            f"independent rerun acceptance failed mismatches={len(fail_rows)} "
            f"authoritative_unchanged={authoritative_unchanged}"
        )
    print(
        f"independent rerun PASS run_id={run_id} bundle_rows={len(method_rows)} "
        f"manifold_rows={len(manifold_rows)} field_checks={len(scientific_rows)}"
    )


if __name__ == "__main__":
    main()
