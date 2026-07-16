#!/usr/bin/env python3
"""Run one read-only physical invariant-bundle benchmark for fast CI."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.invariant_bundles import (  # noqa: E402
    qr_svd_cocycle_bundle_iteration,
    real_schur_bundle_tracking,
)


RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "ci_validation.json"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
COCYCLES = RESEARCH / "results" / "npz" / "cocycles"
AUTHORITATIVE_RESULTS = (RESEARCH / "results").resolve()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def safe_output_dir(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == AUTHORITATIVE_RESULTS or AUTHORITATIVE_RESULTS in resolved.parents:
        raise RuntimeError("CI physical benchmark may not write below authoritative results")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def read_case(case_id: str) -> dict[str, str]:
    with REGISTRY.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    matches = [row for row in rows if row["case_id"] == case_id]
    if len(matches) != 1:
        raise RuntimeError(f"registry case lookup returned {len(matches)} rows")
    return matches[0]


def result_row(case_id: str, result: Any, limit: float) -> dict[str, Any]:
    accepted = (
        result.bundle_dimension == 1
        and result.classification == "real_1d_hyperbolic_bundle"
        and result.max_invariance_residual <= limit
    )
    return {
        "schema_version": "ci_small_physical_benchmark_v1",
        "case_id": case_id,
        "method": result.method,
        "bundle_dimension": result.bundle_dimension,
        "classification": result.classification,
        "max_invariance_residual": result.max_invariance_residual,
        "mean_invariance_residual": result.mean_invariance_residual,
        "selection_residual": result.selection_residual,
        "iterations": result.iterations,
        "converged": str(result.converged).lower(),
        "acceptance_limit": limit,
        "status": "pass" if accepted else "fail",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = safe_output_dir(args.output_dir)
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    fast = config["fast_ci"]
    case_id = fast["small_physical_case"]
    row = read_case(case_id)
    cache_matches = sorted(COCYCLES.glob(f"{case_id}_*.npz"))
    if len(cache_matches) != 1:
        raise RuntimeError(
            f"expected exactly one committed cocycle for {case_id}; got {len(cache_matches)}"
        )
    cache_path = cache_matches[0]
    with np.load(cache_path, allow_pickle=False) as archive:
        cocycle = np.asarray(archive["stms"], dtype=float)
        phases = np.asarray(archive["phases"], dtype=float)
        cache_case = str(archive["case_id"][0])
        cache_registry_hash = str(archive["registry_sha256"][0])
    if cache_case != case_id:
        raise RuntimeError(f"cocycle case mismatch: {cache_case}")
    if cache_registry_hash != sha256(REGISTRY):
        raise RuntimeError("cocycle registry hash does not match the frozen registry")
    rho = float(row["rho"])
    schur = real_schur_bundle_tracking(cocycle, phases, rho)
    qr = qr_svd_cocycle_bundle_iteration(
        cocycle,
        phases,
        rho,
        bundle_dimension=schur.bundle_dimension,
    )
    rows = [
        result_row(
            case_id,
            schur,
            float(fast["max_schur_invariance_residual"]),
        ),
        result_row(
            case_id,
            qr,
            float(fast["max_qr_invariance_residual"]),
        ),
    ]
    csv_path = output / "ci_small_physical_benchmark.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    npz_path = output / "ci_small_physical_benchmark.npz"
    np.savez_compressed(
        npz_path,
        schema_version=np.asarray(["ci_small_physical_benchmark_v1"]),
        case_id=np.asarray([case_id]),
        phases=phases,
        schur_bases=schur.bases,
        schur_invariance_residuals=schur.invariance_residuals,
        qr_bases=qr.bases,
        qr_invariance_residuals=qr.invariance_residuals,
        cocycle_sha256=np.asarray([sha256(cache_path)]),
        registry_sha256=np.asarray([sha256(REGISTRY)]),
    )
    failures = [item for item in rows if item["status"] != "pass"]
    summary = {
        "schema_version": "ci_small_physical_benchmark_summary_v1",
        "status": "PASS" if not failures else "FAIL",
        "case_id": case_id,
        "source_kind": "committed_cocycle_read_only",
        "source_cocycle": str(cache_path.relative_to(ROOT)).replace("\\", "/"),
        "source_cocycle_sha256": sha256(cache_path),
        "registry_sha256": sha256(REGISTRY),
        "python": sys.version,
        "platform": platform.platform(),
        "results": rows,
        "truth_boundary": (
            "This smoke benchmark does not change the frozen reproduction level, "
            "Chapter 4 holdout, or Route H classifications."
        ),
    }
    (output / "ci_small_physical_benchmark.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "failure_evidence.md").write_text(
        "# Fast-CI physical benchmark failure evidence\n\n"
        f"- Failed method checks: {len(failures)}.\n"
        "- The pointwise baseline is intentionally outside this smoke acceptance; "
        "its committed failures remain visible in the full benchmark table.\n"
        "- No authoritative result file was opened for writing.\n",
        encoding="utf-8",
    )
    if failures:
        raise RuntimeError(f"small physical benchmark failed: {failures}")
    print(
        f"small physical benchmark PASS case={case_id} "
        f"schur={schur.max_invariance_residual:.3e} "
        f"qr={qr.max_invariance_residual:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
