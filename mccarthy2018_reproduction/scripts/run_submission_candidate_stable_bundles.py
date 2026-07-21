"""Run the preregistered Stage-H stable invariant-bundle campaign."""

from __future__ import annotations

import argparse
from collections import Counter
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
import tracemalloc
from typing import Any, Mapping

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPTS))

import build_submission_candidate_stage_h_registry as preregistration  # noqa: E402
import run_invariant_bundle_benchmarks as stage_e  # noqa: E402
from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    fingerprint_matches,
)
from qp_orbits.invariant_bundles import (  # noqa: E402
    InvariantBundleResult,
    assemble_discrete_cocycle_operator,
    qr_svd_cocycle_bundle_iteration,
    real_schur_bundle_tracking,
    traditional_pointwise_eigen_bundle,
)


STAGE_H = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
)
CONFIG = STAGE_H / "configs" / "stage_h_preregistration.json"
H1_REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
STAGE_C_REGISTRY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "benchmarks"
    / "benchmark_registry.csv"
)
OUTPUT_DIR = STAGE_H / "results" / "stable_bundles"
OUTPUT_CSV = OUTPUT_DIR / "stable_bundle_comparison.csv"
OUTPUT_NPZ = OUTPUT_DIR / "stable_bundle_results.npz"
SUMMARY = OUTPUT_DIR / "stable_bundle_summary.json"
CHECKPOINT = OUTPUT_DIR / "stable_bundle_checkpoint.json"
ENVIRONMENT = OUTPUT_DIR / "environment.json"
AUDIT = OUTPUT_DIR / "stable_bundle_audit.md"
FAILURE_EVIDENCE = OUTPUT_DIR / "failure_evidence.md"
ARTIFACT_HASHES = OUTPUT_DIR / "artifact_hashes.csv"

SCHEMA_VERSION = "submission_candidate_stable_bundle_v1"
METHODS = stage_e.METHODS
EXPECTED_CASES = (
    "h2_stable_em_halo_12p40_n45",
    "h2_stable_em_vertical_12p66_n57",
    "h2_stable_se_active_geometry_member_468",
)

FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "family",
    "system",
    "method",
    "branch",
    "bundle_dimension",
    "classification",
    "source_map_residual",
    "source_map_status",
    "source_gate_status",
    "evidence_class",
    "max_invariance_residual",
    "mean_invariance_residual",
    "selection_residual",
    "reciprocal_pair_error",
    "relative_imaginary_part",
    "phase_principal_angle_max_deg",
    "phase_principal_angle_mean_deg",
    "principal_angle_to_qr_max_deg",
    "bundle_multiplier_estimate",
    "lyapunov_estimate_per_day",
    "stable_multiplier_lt_one",
    "iterations",
    "converged",
    "runtime_seconds",
    "peak_memory_mb_estimate",
    "research_status",
    "failure_reason",
    "h1_registry_sha256",
    "stage_c_registry_sha256",
    "state_artifact_sha256",
    "cocycle_cache_sha256",
    "source_git_commit",
)

HASH_FIELDS = (
    "artifact",
    "hash_mode",
    "bytes",
    "sha256",
)


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".16g")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _write_csv(
    path: Path,
    fields: tuple[str, ...],
    rows: list[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=fields,
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row[field]) for field in fields})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _run_id() -> str:
    digest = hashlib.sha256()
    for path in (
        CONFIG,
        H1_REGISTRY,
        STAGE_C_REGISTRY,
        ROOT / "src" / "qp_orbits" / "invariant_bundles.py",
        Path(__file__),
    ):
        fingerprint = artifact_fingerprint(path)
        digest.update(fingerprint.sha256.encode("ascii"))
    return digest.hexdigest().upper()[:20]


def _sanitize(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_" for character in value
    )


def _principal_angle_to_reference(
    bases: np.ndarray,
    references: np.ndarray,
) -> float:
    if bases.shape != references.shape:
        return float("nan")
    angles: list[float] = []
    for basis, reference in zip(bases, references, strict=True):
        singular = np.linalg.svd(basis.T @ reference, compute_uv=False)
        singular = np.clip(singular, -1.0, 1.0)
        angles.append(float(np.max(np.degrees(np.arccos(singular)))))
    return max(angles, default=float("nan"))


def _load_frozen_cocycle(
    source: Mapping[str, str],
) -> tuple[np.ndarray, np.ndarray, float, Path]:
    states, phases = stage_e._load_states(source)
    max_step = 0.005 if source["system"] == "sun_earth" else 0.01
    key = stage_e._cocycle_cache_key(source, max_step=max_step)
    path = (
        stage_e.COCYCLE_DIR
        / f"{source['case_id']}_{key}.npz"
    )
    if not path.is_file():
        raise RuntimeError(
            "missing frozen Stage-E cocycle cache; Stage H may not write "
            f"the old authority: {_rel(path)}"
        )
    with np.load(path, allow_pickle=False) as archive:
        if str(archive["cache_key"][0]) != key:
            raise RuntimeError(f"cocycle cache key drifted for {source['case_id']}")
        stms = np.asarray(archive["stms"], dtype=float)
        stored_phases = np.asarray(archive["phases"], dtype=float)
        source_map_residual = float(archive["source_map_residual"][0])
    if stms.shape != (states.shape[0], 6, 6):
        raise RuntimeError(f"cocycle shape drifted for {source['case_id']}")
    np.testing.assert_allclose(stored_phases, phases, rtol=0.0, atol=0.0)
    return stms, phases, source_map_residual, path


def _method_runner(
    method: str,
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    schur_dimension: int | None,
    max_iterations: int,
    real_relative_imaginary_tolerance: float,
    angle_tolerance_deg: float,
) -> InvariantBundleResult:
    if method == METHODS[0]:
        return traditional_pointwise_eigen_bundle(
            cocycle,
            phases,
            rho,
            branch="stable",
        )
    if method == METHODS[1]:
        return real_schur_bundle_tracking(
            cocycle,
            phases,
            rho,
            branch="stable",
            real_relative_imaginary_tolerance=real_relative_imaginary_tolerance,
        )
    if method == METHODS[2]:
        return qr_svd_cocycle_bundle_iteration(
            cocycle,
            phases,
            rho,
            branch="stable",
            bundle_dimension=schur_dimension,
            max_iterations=max_iterations,
            angle_tolerance_deg=angle_tolerance_deg,
            real_relative_imaginary_tolerance=real_relative_imaginary_tolerance,
        )
    raise ValueError(f"unknown stable-bundle method: {method}")


def _classify(
    result: InvariantBundleResult,
    *,
    source_status: str,
    multiplier: float,
    thresholds: Mapping[str, Any],
) -> tuple[str, str]:
    reasons: list[str] = []
    if source_status != "pass":
        reasons.append("source_map_revalidation_failed")
    if result.bundle_dimension != 1:
        reasons.append("stable_bundle_dimension_not_one")
    if result.classification == "complex_vector_projected_to_real_1d_failure":
        reasons.append("complex_vector_projected_to_real_1d")
    if (
        result.method == "ordered_real_schur_tracking"
        and result.selection_residual
        > float(thresholds["accepted_max_selection_residual"])
    ):
        reasons.append("partial_schur_residual_gt_1e-8")
    if (
        result.method == "qr_svd_shifted_cocycle_iteration"
        and not result.converged
    ):
        reasons.append("qr_iteration_not_converged_at_cap")
    if (
        result.max_invariance_residual
        > float(thresholds["accepted_max_invariance_residual"])
    ):
        reasons.append("max_invariance_residual_gt_1e-6")
    if not multiplier < 1.0:
        reasons.append("stable_multiplier_not_below_one")
    if source_status == "pass" and not reasons:
        return "accepted", ""
    if (
        source_status == "pass"
        and result.bundle_dimension == 1
        and result.classification
        != "complex_vector_projected_to_real_1d_failure"
        and result.max_invariance_residual
        <= float(thresholds["boundary_max_invariance_residual"])
        and multiplier < 1.0
    ):
        return "boundary", ";".join(reasons)
    return "fail", ";".join(reasons)


def _empty_failure_row(
    preregistered: Mapping[str, str],
    source: Mapping[str, str],
    *,
    method: str,
    run_id: str,
    source_map_residual: float,
    source_status: str,
    runtime: float,
    peak_memory_mb: float,
    h1_hash: str,
    stage_c_hash: str,
    cache_hash: str,
    commit: str,
    error: Exception,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "case_id": preregistered["case_id"],
        "source_case_id": source["case_id"],
        "family": source["family"],
        "system": source["system"],
        "method": method,
        "branch": "stable",
        "bundle_dimension": 0,
        "classification": "method_exception",
        "source_map_residual": source_map_residual,
        "source_map_status": source_status,
        "source_gate_status": preregistered["source_gate_status"],
        "evidence_class": preregistered["evidence_class"],
        "max_invariance_residual": float("nan"),
        "mean_invariance_residual": float("nan"),
        "selection_residual": float("nan"),
        "reciprocal_pair_error": float("nan"),
        "relative_imaginary_part": float("nan"),
        "phase_principal_angle_max_deg": float("nan"),
        "phase_principal_angle_mean_deg": float("nan"),
        "principal_angle_to_qr_max_deg": float("nan"),
        "bundle_multiplier_estimate": float("nan"),
        "lyapunov_estimate_per_day": float("nan"),
        "stable_multiplier_lt_one": False,
        "iterations": 0,
        "converged": False,
        "runtime_seconds": runtime,
        "peak_memory_mb_estimate": peak_memory_mb,
        "research_status": "fail",
        "failure_reason": f"{type(error).__name__}: {error}",
        "h1_registry_sha256": h1_hash,
        "stage_c_registry_sha256": stage_c_hash,
        "state_artifact_sha256": preregistered["state_artifact_sha256"],
        "cocycle_cache_sha256": cache_hash,
        "source_git_commit": commit,
    }


def _write_checkpoint(payload: Mapping[str, Any]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_environment(commit: str, run_id: str) -> None:
    payload = {
        "schema_version": "submission_candidate_stable_bundle_environment_v1",
        "run_id": run_id,
        "source_git_commit": commit,
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
    }
    ENVIRONMENT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_audit(
    rows: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    index = {
        (str(row["case_id"]), str(row["method"])): row for row in rows
    }
    lines = [
        "# Stage H2 stable invariant-bundle audit",
        "",
        f"- Run ID: {summary['run_id']}",
        f"- Cases: {summary['cases']}",
        f"- Method rows: {summary['method_rows']}",
        f"- Accepted improved-method rows: {summary['accepted_improved_rows']}",
        f"- Cases with both improved methods accepted: {summary['cases_with_both_improved_methods_accepted']}",
        f"- H2 submission-candidate gate: {summary['h2_gate_status']}",
        "",
        "## Results",
        "",
        "| case | method | dim | multiplier | max residual | status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for case_id in EXPECTED_CASES:
        for method in METHODS:
            row = index[(case_id, method)]
            lines.append(
                f"| {case_id} | {method} | {row['bundle_dimension']} | "
                f"{float(row['bundle_multiplier_estimate']):.6e} | "
                f"{float(row['max_invariance_residual']):.3e} | "
                f"{row['research_status']} |"
            )
    lines += [
        "",
        "## Truth boundary",
        "",
        "These are Stage-H research results for the stable branch. They do not",
        "modify the frozen 54-figure registry, Chapter-4 holdout, or any",
        "McCarthy paper-equivalence claim. Pointwise failures remain in the",
        "comparison denominator.",
        "",
    ]
    AUDIT.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def _write_failure_evidence(rows: list[Mapping[str, Any]]) -> None:
    failed = [
        row for row in rows if str(row["research_status"]) != "accepted"
    ]
    lines = [
        "# Stage H2 failure and boundary evidence",
        "",
        f"- Non-accepted rows retained: {len(failed)}",
        "",
    ]
    for row in failed:
        lines.append(
            f"- {row['case_id']} / {row['method']}: "
            f"{row['research_status']} - {row['failure_reason']}"
        )
    lines += [
        "",
        "No failed or boundary row is removed from the campaign denominator.",
        "",
    ]
    FAILURE_EVIDENCE.write_text(
        "\n".join(lines),
        encoding="utf-8",
        newline="\n",
    )


def _write_artifact_hashes() -> None:
    artifacts = (
        OUTPUT_CSV,
        OUTPUT_NPZ,
        SUMMARY,
        CHECKPOINT,
        ENVIRONMENT,
        AUDIT,
        FAILURE_EVIDENCE,
    )
    rows: list[dict[str, Any]] = []
    for path in artifacts:
        fingerprint = artifact_fingerprint(path)
        rows.append(
            {
                "artifact": _rel(path),
                "hash_mode": fingerprint.hash_mode,
                "bytes": fingerprint.bytes,
                "sha256": fingerprint.sha256,
            }
        )
    _write_csv(ARTIFACT_HASHES, HASH_FIELDS, rows)


def run_campaign(*, max_wall_seconds: float) -> None:
    preregistration.check_outputs()
    specification = json.loads(CONFIG.read_text(encoding="utf-8"))
    thresholds = specification["thresholds"]
    h1_rows = [
        row
        for row in _read_csv(H1_REGISTRY)
        if row["campaign"] == "H2_stable_bundle"
    ]
    if tuple(row["case_id"] for row in h1_rows) != EXPECTED_CASES:
        raise RuntimeError("the preregistered H2 case order drifted")
    caps = [float(row["max_wall_seconds"]) for row in h1_rows]
    if max_wall_seconds <= 0.0 or max_wall_seconds > min(caps):
        raise ValueError(
            f"max-wall-seconds must be in (0, {min(caps)}]"
        )
    stage_c_rows = _read_csv(STAGE_C_REGISTRY)
    stage_c_index = {row["case_id"]: row for row in stage_c_rows}
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stage_c_hash = artifact_fingerprint(STAGE_C_REGISTRY).sha256
    run_id = _run_id()
    commit = _git_commit()
    started_campaign = time.perf_counter()
    records: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "h1_registry_sha256": np.asarray([h1_hash]),
        "stage_c_registry_sha256": np.asarray([stage_c_hash]),
        "source_git_commit": np.asarray([commit]),
        "case_ids": np.asarray(EXPECTED_CASES),
        "methods": np.asarray(METHODS),
    }
    completed_cases: list[str] = []
    for case_index, preregistered in enumerate(h1_rows, start=1):
        if time.perf_counter() - started_campaign > max_wall_seconds:
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "wall_time_cap_reached",
                    "completed_cases": completed_cases,
                    "max_wall_seconds": max_wall_seconds,
                }
            )
            raise RuntimeError("H2 campaign reached the preregistered wall-time cap")
        source_case_id = preregistered["source_case_id"]
        if source_case_id not in stage_c_index:
            raise RuntimeError(f"missing Stage-C source: {source_case_id}")
        source = stage_c_index[source_case_id]
        cocycle, phases, source_map_residual, cache_path = (
            _load_frozen_cocycle(source)
        )
        cache_hash = _sha256(cache_path)
        source_status = stage_e._source_map_status(source, source_map_residual)
        operator_spectrum = np.linalg.eigvals(
            assemble_discrete_cocycle_operator(
                cocycle,
                phases,
                float(source["rho"]),
            )
        )
        methods = tuple(preregistered["methods"].split(";"))
        if methods != METHODS:
            raise RuntimeError("H2 method list drifted from the frozen comparison")
        print(
            f"H2 case {case_index}/{len(h1_rows)} "
            f"{preregistered['case_id']} source={source_status}",
            flush=True,
        )
        case_rows: list[dict[str, Any]] = []
        case_results: dict[str, InvariantBundleResult] = {}
        schur_dimension: int | None = None
        for method in methods:
            started = time.perf_counter()
            tracemalloc.start()
            try:
                result = _method_runner(
                    method,
                    cocycle,
                    phases,
                    float(source["rho"]),
                    schur_dimension=schur_dimension,
                    max_iterations=int(preregistered["max_iterations"]),
                    real_relative_imaginary_tolerance=1.0e-10,
                    angle_tolerance_deg=float(
                        thresholds["qr_angle_tolerance_deg"]
                    ),
                )
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                runtime = time.perf_counter() - started
                if method == METHODS[1]:
                    schur_dimension = result.bundle_dimension
                multiplier = stage_e._bundle_multiplier(result)
                reciprocal = stage_e._reciprocal_pair_error(
                    result.selected_spectrum,
                    operator_spectrum,
                )
                status, reason = _classify(
                    result,
                    source_status=source_status,
                    multiplier=multiplier,
                    thresholds=thresholds,
                )
                output_method = (
                    "ordered_partial_real_schur_tracking"
                    if result.method == "ordered_real_schur_tracking"
                    else result.method
                )
                estimated_bytes = (
                    result.bases.nbytes
                    + result.local_reduced_maps.nbytes
                    + result.invariance_residuals.nbytes
                    + result.phase_principal_angles_deg.nbytes
                )
                row = {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "case_id": preregistered["case_id"],
                    "source_case_id": source_case_id,
                    "family": source["family"],
                    "system": source["system"],
                    "method": output_method,
                    "branch": "stable",
                    "bundle_dimension": result.bundle_dimension,
                    "classification": result.classification,
                    "source_map_residual": source_map_residual,
                    "source_map_status": source_status,
                    "source_gate_status": preregistered["source_gate_status"],
                    "evidence_class": preregistered["evidence_class"],
                    "max_invariance_residual": result.max_invariance_residual,
                    "mean_invariance_residual": result.mean_invariance_residual,
                    "selection_residual": result.selection_residual,
                    "reciprocal_pair_error": reciprocal,
                    "relative_imaginary_part": result.relative_imaginary,
                    "phase_principal_angle_max_deg": result.max_phase_principal_angle_deg,
                    "phase_principal_angle_mean_deg": result.mean_phase_principal_angle_deg,
                    "principal_angle_to_qr_max_deg": float("nan"),
                    "bundle_multiplier_estimate": multiplier,
                    "lyapunov_estimate_per_day": math.log(multiplier)
                    / float(source["mapping_time"]),
                    "stable_multiplier_lt_one": multiplier < 1.0,
                    "iterations": result.iterations,
                    "converged": result.converged,
                    "runtime_seconds": runtime,
                    "peak_memory_mb_estimate": max(peak, estimated_bytes)
                    / (1024.0**2),
                    "research_status": status,
                    "failure_reason": reason,
                    "h1_registry_sha256": h1_hash,
                    "stage_c_registry_sha256": stage_c_hash,
                    "state_artifact_sha256": preregistered[
                        "state_artifact_sha256"
                    ],
                    "cocycle_cache_sha256": cache_hash,
                    "source_git_commit": commit,
                }
                case_rows.append(row)
                case_results[output_method] = result
                prefix = (
                    f"{_sanitize(preregistered['case_id'])}__"
                    f"{_sanitize(output_method)}"
                )
                arrays[prefix + "__bases"] = result.bases
                arrays[prefix + "__local_reduced_maps"] = (
                    result.local_reduced_maps
                )
                arrays[prefix + "__invariance_residuals"] = (
                    result.invariance_residuals
                )
                arrays[prefix + "__phase_principal_angles_deg"] = (
                    result.phase_principal_angles_deg
                )
                arrays[prefix + "__selected_spectrum"] = (
                    result.selected_spectrum
                )
                arrays[prefix + "__convergence_history"] = (
                    result.convergence_history
                )
                arrays[
                    f"{_sanitize(preregistered['case_id'])}__phases"
                ] = phases
                print(
                    f"  {output_method}: {status} "
                    f"max_res={result.max_invariance_residual:.3e} "
                    f"mult={multiplier:.6e}",
                    flush=True,
                )
            except Exception as error:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                runtime = time.perf_counter() - started
                case_rows.append(
                    _empty_failure_row(
                        preregistered,
                        source,
                        method=method,
                        run_id=run_id,
                        source_map_residual=source_map_residual,
                        source_status=source_status,
                        runtime=runtime,
                        peak_memory_mb=peak / (1024.0**2),
                        h1_hash=h1_hash,
                        stage_c_hash=stage_c_hash,
                        cache_hash=cache_hash,
                        commit=commit,
                        error=error,
                    )
                )
                print(
                    f"  {method}: fail {type(error).__name__}: {error}",
                    flush=True,
                )
        qr = case_results.get("qr_svd_shifted_cocycle_iteration")
        for row in case_rows:
            result = case_results.get(str(row["method"]))
            if result is not None and qr is not None:
                row["principal_angle_to_qr_max_deg"] = (
                    _principal_angle_to_reference(result.bases, qr.bases)
                )
        records.extend(case_rows)
        completed_cases.append(preregistered["case_id"])
        _write_checkpoint(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "status": "running",
                "completed_cases": completed_cases,
                "total_cases": len(h1_rows),
                "elapsed_seconds": time.perf_counter() - started_campaign,
                "max_wall_seconds": max_wall_seconds,
            }
        )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(OUTPUT_CSV, FIELDS, records)
    np.savez_compressed(OUTPUT_NPZ, **arrays)
    improved = [
        row
        for row in records
        if row["method"]
        in (
            "ordered_partial_real_schur_tracking",
            "qr_svd_shifted_cocycle_iteration",
        )
    ]
    cases_with_both = sum(
        all(
            next(
                row
                for row in improved
                if row["case_id"] == case_id and row["method"] == method
            )["research_status"]
            == "accepted"
            for method in (
                "ordered_partial_real_schur_tracking",
                "qr_svd_shifted_cocycle_iteration",
            )
        )
        for case_id in EXPECTED_CASES
    )
    counts = Counter(str(row["research_status"]) for row in records)
    elapsed = time.perf_counter() - started_campaign
    summary = {
        "schema_version": "submission_candidate_stable_bundle_summary_v1",
        "run_id": run_id,
        "status": "complete",
        "cases": len(EXPECTED_CASES),
        "methods": len(METHODS),
        "method_rows": len(records),
        "status_counts": dict(counts),
        "accepted_improved_rows": sum(
            row["research_status"] == "accepted" for row in improved
        ),
        "cases_with_both_improved_methods_accepted": cases_with_both,
        "h2_minimum_accepted_cases": 2,
        "h2_gate_status": "pass" if cases_with_both >= 2 else "fail",
        "elapsed_seconds": elapsed,
        "max_wall_seconds": max_wall_seconds,
        "h1_registry_sha256": h1_hash,
        "stage_c_registry_sha256": stage_c_hash,
        "source_git_commit": commit,
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_checkpoint({**summary, "completed_cases": completed_cases})
    _write_environment(commit, run_id)
    _write_audit(records, summary)
    _write_failure_evidence(records)
    _write_artifact_hashes()
    print(
        "STAGE-H2 STABLE BUNDLE WRITE PASS "
        f"cases={len(EXPECTED_CASES)} rows={len(records)} "
        f"gate={summary['h2_gate_status']} elapsed={elapsed:.3f}s",
        flush=True,
    )


def check_outputs() -> None:
    preregistration.check_outputs()
    rows = _read_csv(OUTPUT_CSV)
    expected_rows = len(EXPECTED_CASES) * len(METHODS)
    if len(rows) != expected_rows:
        raise RuntimeError(
            f"stable-bundle row count {len(rows)} != {expected_rows}"
        )
    if {row["case_id"] for row in rows} != set(EXPECTED_CASES):
        raise RuntimeError("stable-bundle case coverage drifted")
    if {row["method"] for row in rows} != set(METHODS):
        raise RuntimeError("stable-bundle method coverage drifted")
    if {row["branch"] for row in rows} != {"stable"}:
        raise RuntimeError("stable-bundle branch semantics drifted")
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stage_c_hash = artifact_fingerprint(STAGE_C_REGISTRY).sha256
    if any(row["h1_registry_sha256"] != h1_hash for row in rows):
        raise RuntimeError("stable-bundle H1 registry hash drifted")
    if any(row["stage_c_registry_sha256"] != stage_c_hash for row in rows):
        raise RuntimeError("stable-bundle Stage-C registry hash drifted")
    improved = [
        row
        for row in rows
        if row["method"]
        in (
            "ordered_partial_real_schur_tracking",
            "qr_svd_shifted_cocycle_iteration",
        )
    ]
    if sum(row["research_status"] == "accepted" for row in improved) < 4:
        raise RuntimeError("H2 no longer clears the minimum improved-method gate")
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["h2_gate_status"] != "pass":
        raise RuntimeError("stored H2 stable-bundle gate is not passing")
    if summary["cases_with_both_improved_methods_accepted"] < 2:
        raise RuntimeError("fewer than two H2 cases accept both improved methods")
    with np.load(OUTPUT_NPZ, allow_pickle=False) as archive:
        if str(archive["h1_registry_sha256"][0]) != h1_hash:
            raise RuntimeError("stable-bundle NPZ H1 hash drifted")
        for case_id in EXPECTED_CASES:
            for method in METHODS:
                prefix = f"{_sanitize(case_id)}__{_sanitize(method)}"
                if prefix + "__bases" not in archive.files:
                    raise RuntimeError(
                        f"stable-bundle NPZ lacks {prefix} bases"
                    )
    hash_rows = _read_csv(ARTIFACT_HASHES)
    if len(hash_rows) != 7:
        raise RuntimeError("stable-bundle artifact manifest count drifted")
    for row in hash_rows:
        path = ROOT / row["artifact"]
        if not fingerprint_matches(
            path,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(f"stable-bundle artifact hash drifted: {_rel(path)}")
    for path in (
        AUDIT,
        FAILURE_EVIDENCE,
        ENVIRONMENT,
        CHECKPOINT,
    ):
        if not path.is_file():
            raise RuntimeError(f"missing stable-bundle evidence: {_rel(path)}")
    print(
        "STAGE-H2 STABLE BUNDLE CHECK PASS "
        f"cases={len(EXPECTED_CASES)} rows={expected_rows} "
        f"gate={summary['h2_gate_status']}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-wall-seconds", type=float, default=1800.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        check_outputs()
    else:
        run_campaign(max_wall_seconds=args.max_wall_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
