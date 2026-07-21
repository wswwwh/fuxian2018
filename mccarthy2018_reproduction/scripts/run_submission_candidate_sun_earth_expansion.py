"""Run the preregistered Stage-H5 independent Sun-Earth expansion."""

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
from typing import Any, Mapping

import numpy as np
import scipy


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPTS))

import build_submission_candidate_stage_h_registry as preregistration  # noqa: E402
import run_invariant_bundle_benchmarks as stage_e  # noqa: E402
import run_invariant_bundle_manifold_convergence as stage_f  # noqa: E402
from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    fingerprint_matches,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.invariant_bundles import (  # noqa: E402
    InvariantBundleResult,
    periodic_interpolation_matrix,
    qr_svd_cocycle_bundle_iteration,
    real_schur_bundle_tracking,
    traditional_pointwise_eigen_bundle,
)
from qp_orbits.variational import integrate_states_and_stms  # noqa: E402


STAGE_H = ROOT / "research" / "invariant_bundles" / "submission_candidate"
H1_REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
STAGE_C_REGISTRY = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "benchmarks"
    / "benchmark_registry.csv"
)
OUTPUT_DIR = STAGE_H / "results" / "sun_earth_expansion"
COCYCLE_DIR = OUTPUT_DIR / "cocycles"
SOURCE_CSV = OUTPUT_DIR / "source_validation.csv"
INDEPENDENCE_CSV = OUTPUT_DIR / "source_independence.csv"
ATTEMPTS_CSV = OUTPUT_DIR / "method_attempts.csv"
BENCHMARK_CSV = OUTPUT_DIR / "benchmark_comparison.csv"
MANIFOLD_CSV = OUTPUT_DIR / "manifold_validation.csv"
RESULTS_NPZ = OUTPUT_DIR / "benchmark_results.npz"
SUMMARY = OUTPUT_DIR / "sun_earth_expansion_summary.json"
CHECKPOINT = OUTPUT_DIR / "sun_earth_expansion_checkpoint.json"
ENVIRONMENT = OUTPUT_DIR / "environment.json"
AUDIT = OUTPUT_DIR / "sun_earth_expansion_audit.md"
FAILURE_EVIDENCE = OUTPUT_DIR / "failure_evidence.md"
ARTIFACT_HASHES = OUTPUT_DIR / "artifact_hashes.csv"

SCHEMA_VERSION = "submission_candidate_sun_earth_expansion_v1"
CASES = (
    "h5_se_active_event_step_1_n21",
    "h5_se_sharpness_stage_4_n21",
    "h5_se_energy_frontier_n21",
)
METHODS = stage_e.METHODS
IMPROVED_METHODS = METHODS[1:]
SIGNS = (-1, 1)
PERTURBATION = 1.0e-7
TIME_SAMPLES = 41
PASS_INVARIANCE = 1.0e-6
BOUNDARY_INVARIANCE = 1.0e-3
PASS_SELECTION = 1.0e-8
QR_ANGLE_TOLERANCE_DEG = 2.0e-6
JACOBI_LIMIT = 1.0e-10
INITIAL_LINEAR_RATIO_TOLERANCE = 0.05

SOURCE_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "member_id",
    "family",
    "system",
    "spectral_samples",
    "mapping_time_nd",
    "mapping_time_days",
    "rho",
    "registered_jacobi",
    "recomputed_jacobi_span",
    "registered_source_residual",
    "recomputed_map_residual",
    "source_map_residual_limit",
    "source_map_status",
    "source_gate_status",
    "evidence_class",
    "source_authority_boundary",
    "state_artifact",
    "state_artifact_hash_match",
    "state_array_sha256",
    "state_array_hash_match",
    "metadata_artifact",
    "metadata_fingerprint_match",
    "new_vs_stage_c_registry",
    "cocycle_artifact",
    "cocycle_sha256",
    "status",
    "h1_registry_sha256",
    "stage_c_registry_sha256",
    "source_git_commit",
)

INDEPENDENCE_FIELDS = (
    "schema_version",
    "run_id",
    "left_case_id",
    "right_case_id",
    "state_artifact_hash_distinct",
    "state_array_hash_distinct",
    "state_rms_difference",
    "state_max_abs_difference",
    "mapping_time_difference_days",
    "rho_difference",
    "distinct_local_source_artifacts",
    "status",
    "source_git_commit",
)

ATTEMPT_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "method",
    "attempt_index",
    "variant",
    "iteration_cap",
    "iterations_executed",
    "bundle_dimension",
    "classification",
    "max_invariance_residual",
    "mean_invariance_residual",
    "selection_residual",
    "converged",
    "bundle_multiplier_estimate",
    "algorithm_status",
    "source_authority_boundary",
    "h5_status",
    "failure_reason",
    "runtime_seconds",
    "selected_for_benchmark",
    "cocycle_sha256",
    "h1_registry_sha256",
    "source_git_commit",
)

BENCHMARK_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "member_id",
    "family",
    "system",
    "method",
    "selected_attempt_index",
    "selected_variant",
    "spectral_samples",
    "bundle_dimension",
    "classification",
    "max_invariance_residual",
    "mean_invariance_residual",
    "selection_residual",
    "phase_principal_angle_max_deg",
    "iterations",
    "converged",
    "selected_spectrum",
    "bundle_multiplier_estimate",
    "lyapunov_estimate_per_day",
    "source_map_residual_recomputed",
    "source_map_status",
    "source_jacobi_span",
    "source_gate_status",
    "evidence_class",
    "source_authority_boundary",
    "new_vs_stage_c_registry",
    "research_status",
    "failure_reason",
    "cocycle_sha256",
    "h1_registry_sha256",
    "source_git_commit",
)

MANIFOLD_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "member_id",
    "family",
    "system",
    "method",
    "branch",
    "propagation_direction",
    "bundle_dimension",
    "spectral_samples",
    "subspace_angular_samples",
    "perturbation_sign",
    "perturbation_norm",
    "propagation_time_nd",
    "propagation_time_days",
    "time_samples",
    "coordinate_system",
    "integrator",
    "event_condition",
    "benchmark_research_status",
    "benchmark_invariance_residual_max",
    "manifold_generated",
    "diagnostic_only",
    "direction_principal_angle_max_deg_to_qr",
    "branch_sign_consistent",
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio",
    "final_linear_growth_ratio",
    "forward_growth_factor_mean",
    "forward_growth_factor_max",
    "secondary_min_distance_km",
    "normalized_3d_manifold_distance_to_qr",
    "normalized_displacement_distance_to_qr",
    "runtime_seconds",
    "status",
    "failure_reason",
    "cocycle_sha256",
    "state_artifact_sha256",
    "h1_registry_sha256",
    "source_git_commit",
)

HASH_FIELDS = ("artifact", "hash_mode", "bytes", "sha256")


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
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row[field]) for field in fields})


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _key(case_id: str, method: str) -> str:
    return f"{_sanitize(case_id)}__{_sanitize(method)}"


def _manifold_key(case_id: str, method: str, sign: int) -> str:
    prefix = f"{_key(case_id, method)}__sign_{sign:+d}"
    return prefix.replace("+", "p").replace("-", "m")


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _run_id(rows: list[Mapping[str, str]]) -> str:
    digest = hashlib.sha256()
    paths = [H1_REGISTRY, STAGE_C_REGISTRY, Path(__file__)]
    for row in rows:
        paths.extend(
            [ROOT / row["state_artifact"], ROOT / row["source_metadata_artifact"]]
        )
    for path in paths:
        digest.update(artifact_fingerprint(path).sha256.encode("ascii"))
    return digest.hexdigest().upper()[:20]


def _state_array_sha256(states: np.ndarray) -> str:
    values = np.ascontiguousarray(states)
    header = json.dumps(
        {"dtype": values.dtype.str, "shape": list(values.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(header + b"\0" + values.tobytes()).hexdigest().upper()


def _local_random_bases(samples: int, seed: int) -> np.ndarray:
    generator = np.random.default_rng(seed)
    values = generator.standard_normal((samples, 6, 1))
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / norms


def _bundle_multiplier(result: InvariantBundleResult) -> float:
    determinants = np.abs(np.linalg.det(result.local_reduced_maps))
    determinants = np.maximum(determinants, np.finfo(float).tiny)
    return float(
        np.exp(np.mean(np.log(determinants)) / result.bundle_dimension)
    )


def _algorithm_status(result: InvariantBundleResult) -> tuple[str, str]:
    hard_reasons: list[str] = []
    if result.classification == "complex_vector_projected_to_real_1d_failure":
        hard_reasons.append("complex_vector_projected_to_real_1d")
    if result.method == "ordered_real_schur_tracking" and result.selection_residual > PASS_SELECTION:
        hard_reasons.append("partial_schur_residual_gt_1e-8")
    if result.method == "qr_svd_shifted_cocycle_iteration" and not result.converged:
        hard_reasons.append("qr_iteration_not_converged_at_cap")
    if hard_reasons:
        return "fail", ";".join(hard_reasons)
    if result.max_invariance_residual <= PASS_INVARIANCE:
        return "accepted", ""
    residual_reason = "max_invariance_residual_gt_1e-6"
    if result.max_invariance_residual <= BOUNDARY_INVARIANCE:
        return "boundary", residual_reason
    return "fail", residual_reason


def _h5_status(
    algorithm_status: str,
    *,
    source_boundary: bool,
    reason: str,
) -> tuple[str, str]:
    if algorithm_status == "fail":
        return "fail", reason
    if source_boundary or algorithm_status == "boundary":
        reasons = [item for item in (reason, "source_authority_boundary" if source_boundary else "") if item]
        return "boundary", ";".join(reasons)
    return "accepted", ""


def _attempt_row(
    *,
    run_id: str,
    case: Mapping[str, str],
    method: str,
    attempt_index: int,
    variant: str,
    iteration_cap: int,
    result: InvariantBundleResult,
    runtime: float,
    source_boundary: bool,
    cocycle_hash: str,
    h1_hash: str,
    commit: str,
) -> dict[str, Any]:
    algorithm_status, algorithm_reason = _algorithm_status(result)
    h5_status, failure_reason = _h5_status(
        algorithm_status,
        source_boundary=source_boundary,
        reason=algorithm_reason,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "case_id": case["case_id"],
        "method": method,
        "attempt_index": attempt_index,
        "variant": variant,
        "iteration_cap": iteration_cap,
        "iterations_executed": result.iterations,
        "bundle_dimension": result.bundle_dimension,
        "classification": result.classification,
        "max_invariance_residual": result.max_invariance_residual,
        "mean_invariance_residual": result.mean_invariance_residual,
        "selection_residual": result.selection_residual,
        "converged": result.converged,
        "bundle_multiplier_estimate": _bundle_multiplier(result),
        "algorithm_status": algorithm_status,
        "source_authority_boundary": source_boundary,
        "h5_status": h5_status,
        "failure_reason": failure_reason,
        "runtime_seconds": runtime,
        "selected_for_benchmark": False,
        "cocycle_sha256": cocycle_hash,
        "h1_registry_sha256": h1_hash,
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
        "schema_version": "submission_candidate_sun_earth_expansion_environment_v1",
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
    sources: list[Mapping[str, Any]],
    independence: list[Mapping[str, Any]],
    benchmarks: list[Mapping[str, Any]],
    manifolds: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    lines = [
        "# Stage H5 independent Sun-Earth benchmark audit",
        "",
        f"- Run ID: {summary['run_id']}",
        f"- New source benchmarks: {summary['independent_new_source_benchmarks']}",
        f"- Selected method rows: {summary['benchmark_rows']}",
        f"- Manifold rows: {summary['manifold_rows']}",
        f"- Benchmark status counts: {summary['benchmark_status_counts']}",
        f"- H5 gate: {summary['h5_gate_status']}",
        "",
        "## Source validation",
        "",
        "| case | map residual | source limit | Jacobi span | source gate | authority boundary | new vs Stage C |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for row in sources:
        lines.append(
            f"| {row['case_id']} | {float(row['recomputed_map_residual']):.3e} | "
            f"{float(row['source_map_residual_limit']):.3e} | "
            f"{float(row['recomputed_jacobi_span']):.3e} | "
            f"{row['source_gate_status']} | {row['source_authority_boundary']} | "
            f"{row['new_vs_stage_c_registry']} |"
        )
    lines += [
        "",
        "All three checkpoint artifacts and state-array hashes are distinct from",
        "each other and absent from the frozen Stage-C registry. Here independent",
        "means distinct local source artifacts and arrays; it is not a claim of an",
        "external independent solver or independent physical experiment.",
        "",
        "## Pairwise source distinction",
        "",
        "| left | right | state RMS difference | mapping-time difference days | rho difference | status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in independence:
        lines.append(
            f"| {row['left_case_id']} | {row['right_case_id']} | "
            f"{float(row['state_rms_difference']):.3e} | "
            f"{float(row['mapping_time_difference_days']):.6f} | "
            f"{float(row['rho_difference']):.3e} | {row['status']} |"
        )
    lines += [
        "",
        "## Selected benchmark methods",
        "",
        "| case | method | selected attempt | dimension | max residual | multiplier | status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in benchmarks:
        lines.append(
            f"| {row['case_id']} | {row['method']} | {row['selected_attempt_index']} | "
            f"{row['bundle_dimension']} | {float(row['max_invariance_residual']):.3e} | "
            f"{float(row['bundle_multiplier_estimate']):.6e} | {row['research_status']} |"
        )
    lines += [
        "",
        "The pointwise baseline remains fail in all three cases. One and four",
        "graph-transform refinements are retained for Schur; the selected four-step",
        "result and all QR/SVD variants remain boundary at N21, not accepted.",
        "",
        "## One-map nonlinear propagation",
        "",
        "| case | method | sign | Jacobi drift | initial ratio | growth mean | distance to QR | status |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in manifolds:
        lines.append(
            f"| {row['case_id']} | {row['method']} | {row['perturbation_sign']} | "
            f"{float(row['manifold_jacobi_drift']):.3e} | "
            f"{float(row['initial_linear_growth_ratio']):.9f} | "
            f"{float(row['forward_growth_factor_mean']):.6e} | "
            f"{float(row['normalized_3d_manifold_distance_to_qr']):.3e} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Authority boundary",
        "",
        "Every H5 source was preregistered with a target-pair or reproduction",
        "boundary. Therefore no numerical method can be promoted above boundary",
        "in this campaign. The frozen Stage-C registry is not modified, and these",
        "new research benchmarks do not alter the 54-figure baseline, Chapter 4",
        "holdout, or paper-equivalence labels.",
        "",
    ]
    AUDIT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _write_failure_evidence(
    attempts: list[Mapping[str, Any]],
    benchmarks: list[Mapping[str, Any]],
    manifolds: list[Mapping[str, Any]],
) -> None:
    failed_attempts = [row for row in attempts if row["h5_status"] == "fail"]
    failed_benchmarks = [row for row in benchmarks if row["research_status"] == "fail"]
    failed_manifolds = [row for row in manifolds if row["status"] == "fail"]
    lines = [
        "# Stage H5 failure and boundary evidence",
        "",
        f"- Failed method attempts retained: {len(failed_attempts)}",
        f"- Failed selected benchmark rows retained: {len(failed_benchmarks)}",
        f"- Failed diagnostic manifold rows retained: {len(failed_manifolds)}",
        "",
    ]
    for row in failed_attempts:
        lines.append(
            f"- {row['case_id']} / {row['method']} / attempt {row['attempt_index']} "
            f"({row['variant']}): {row['failure_reason']}"
        )
    lines += [
        "",
        "All improved-method results remain boundary because their N21 residuals",
        "are between 1e-6 and 1e-3 and every source carries a preregistered",
        "authority boundary. No failed or boundary row is promoted or omitted.",
        "",
    ]
    FAILURE_EVIDENCE.write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def _write_artifact_hashes(cocycle_paths: list[Path]) -> None:
    artifacts = (
        SOURCE_CSV,
        INDEPENDENCE_CSV,
        ATTEMPTS_CSV,
        BENCHMARK_CSV,
        MANIFOLD_CSV,
        RESULTS_NPZ,
        SUMMARY,
        CHECKPOINT,
        ENVIRONMENT,
        AUDIT,
        FAILURE_EVIDENCE,
        *cocycle_paths,
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
    h1_list = [
        row
        for row in _read_csv(H1_REGISTRY)
        if row["campaign"] == "H5_sun_earth_expansion"
    ]
    if tuple(row["case_id"] for row in h1_list) != CASES:
        raise RuntimeError("the H5 case order drifted")
    h1_rows = {row["case_id"]: row for row in h1_list}
    cap = min(float(row["max_wall_seconds"]) for row in h1_list)
    if max_wall_seconds <= 0.0 or max_wall_seconds > cap:
        raise ValueError(f"max-wall-seconds must be in (0, {cap}]")
    for row in h1_list:
        if int(row["spectral_samples"]) != 21:
            raise RuntimeError("H5 must retain the preregistered N21 grid")
        if int(row["max_retries"]) != 2:
            raise RuntimeError("H5 retry allowance drifted")
        if int(row["time_samples"]) != TIME_SAMPLES:
            raise RuntimeError("H5 time-sample count drifted")

    stage_c_rows = _read_csv(STAGE_C_REGISTRY)
    stage_c_state_hashes: set[str] = set()
    for stage_c_row in stage_c_rows:
        with np.load(
            ROOT / stage_c_row["state_artifact"], allow_pickle=False
        ) as stage_c_archive:
            stage_c_states = np.asarray(
                stage_c_archive[stage_c_row["state_key"]], dtype=float
            )
        stage_c_state_hashes.add(_state_array_sha256(stage_c_states))
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stage_c_hash = artifact_fingerprint(STAGE_C_REGISTRY).sha256
    run_id = _run_id(h1_list)
    commit = _git_commit()
    started_campaign = time.perf_counter()
    source_rows: list[dict[str, Any]] = []
    independence_rows: list[dict[str, Any]] = []
    attempt_rows: list[dict[str, Any]] = []
    benchmark_rows: list[dict[str, Any]] = []
    manifold_rows: list[dict[str, Any]] = []
    source_data: dict[str, dict[str, Any]] = {}
    selected_results: dict[tuple[str, str], InvariantBundleResult] = {}
    selected_attempts: dict[tuple[str, str], dict[str, Any]] = {}
    cocycle_paths: list[Path] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "case_ids": np.asarray(CASES),
        "methods": np.asarray(METHODS),
        "signs": np.asarray(SIGNS),
        "perturbation_norm": np.asarray([PERTURBATION]),
        "h1_registry_sha256": np.asarray([h1_hash]),
        "stage_c_registry_sha256": np.asarray([stage_c_hash]),
        "source_git_commit": np.asarray([commit]),
    }
    system = SYSTEMS["sun_earth"]
    if system.time_unit_days is None or system.length_unit_km is None:
        raise RuntimeError("Sun-Earth physical scales are missing")

    for case_index, case_id in enumerate(CASES, start=1):
        if time.perf_counter() - started_campaign > max_wall_seconds:
            raise RuntimeError("H5 campaign reached the preregistered cap")
        case = h1_rows[case_id]
        state_path = ROOT / case["state_artifact"]
        metadata_path = ROOT / case["source_metadata_artifact"]
        state_fingerprint = artifact_fingerprint(state_path)
        metadata_match = fingerprint_matches(
            metadata_path,
            expected_bytes=int(case["source_metadata_bytes"]),
            expected_sha256=case["source_metadata_sha256"],
            hash_mode=case["source_metadata_hash_mode"],
        )
        with np.load(state_path, allow_pickle=False) as archive:
            states = np.asarray(archive[case["state_key"]], dtype=float)
            mapping_time = float(archive["mapping_time"])
            rho = float(archive["rotation"])
            registered_jacobi = float(archive["jacobi"])
        if states.shape != (21, 6):
            raise RuntimeError(f"{case_id} state shape drifted")
        phases = np.linspace(0.0, 2.0 * np.pi, states.shape[0], endpoint=False)
        state_array_hash = _state_array_sha256(states)
        mapped_states, cocycle = stage_e._stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=system.mu,
            max_step=0.005,
        )
        target_states = periodic_interpolation_matrix(
            phases, phases + rho
        ) @ states
        source_map_residual = float(
            np.max(np.linalg.norm(mapped_states - target_states, axis=1))
        )
        source_limit = max(5.0e-9, 20.0 * float(case["source_residual"]))
        source_map_status = "pass" if source_map_residual <= source_limit else "fail"
        jacobi_values = jacobi_constant(states, system.mu)
        jacobi_span = float(np.max(jacobi_values) - np.min(jacobi_values))
        source_boundary = bool(
            "boundary" in case["source_gate_status"].lower()
            or "boundary" in case["evidence_class"].lower()
        )
        new_vs_stage_c = state_array_hash not in stage_c_state_hashes
        cache_path = COCYCLE_DIR / f"{case_id}.npz"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            schema_version=np.asarray(["submission_candidate_h5_cocycle_v1"]),
            run_id=np.asarray([run_id]),
            case_id=np.asarray([case_id]),
            states=states,
            phases=phases,
            mapped_states=mapped_states,
            target_states=target_states,
            stms=cocycle,
            mapping_time_nd=np.asarray([mapping_time]),
            mapping_time_days=np.asarray([mapping_time * system.time_unit_days]),
            rho=np.asarray([rho]),
            mu=np.asarray([system.mu]),
            source_map_residual=np.asarray([source_map_residual]),
            state_artifact_sha256=np.asarray([state_fingerprint.sha256]),
            state_array_sha256=np.asarray([state_array_hash]),
            source_git_commit=np.asarray([commit]),
        )
        cocycle_hash = artifact_fingerprint(cache_path).sha256
        cocycle_paths.append(cache_path)
        status = bool(
            source_map_status == "pass"
            and state_fingerprint.sha256 == case["state_artifact_sha256"]
            and state_array_hash == case["state_array_sha256"]
            and metadata_match
            and new_vs_stage_c
        )
        source_rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "case_id": case_id,
                "member_id": case["member_id"],
                "family": case["family"],
                "system": case["system"],
                "spectral_samples": states.shape[0],
                "mapping_time_nd": mapping_time,
                "mapping_time_days": mapping_time * system.time_unit_days,
                "rho": rho,
                "registered_jacobi": registered_jacobi,
                "recomputed_jacobi_span": jacobi_span,
                "registered_source_residual": float(case["source_residual"]),
                "recomputed_map_residual": source_map_residual,
                "source_map_residual_limit": source_limit,
                "source_map_status": source_map_status,
                "source_gate_status": case["source_gate_status"],
                "evidence_class": case["evidence_class"],
                "source_authority_boundary": source_boundary,
                "state_artifact": case["state_artifact"],
                "state_artifact_hash_match": (
                    state_fingerprint.sha256 == case["state_artifact_sha256"]
                ),
                "state_array_sha256": state_array_hash,
                "state_array_hash_match": state_array_hash == case["state_array_sha256"],
                "metadata_artifact": case["source_metadata_artifact"],
                "metadata_fingerprint_match": metadata_match,
                "new_vs_stage_c_registry": new_vs_stage_c,
                "cocycle_artifact": _rel(cache_path),
                "cocycle_sha256": cocycle_hash,
                "status": "pass" if status else "fail",
                "h1_registry_sha256": h1_hash,
                "stage_c_registry_sha256": stage_c_hash,
                "source_git_commit": commit,
            }
        )
        if not status:
            raise RuntimeError(f"{case_id} source validation failed")
        source_data[case_id] = {
            "case": case,
            "states": states,
            "phases": phases,
            "mapping_time": mapping_time,
            "rho": rho,
            "cocycle": cocycle,
            "source_map_residual": source_map_residual,
            "jacobi_span": jacobi_span,
            "source_boundary": source_boundary,
            "new_vs_stage_c": new_vs_stage_c,
            "cocycle_hash": cocycle_hash,
            "state_array_hash": state_array_hash,
            "state_artifact_hash": state_fingerprint.sha256,
        }
        prefix = _sanitize(case_id)
        arrays[prefix + "__states"] = states
        arrays[prefix + "__phases"] = phases
        arrays[prefix + "__mapped_states"] = mapped_states
        arrays[prefix + "__stms"] = cocycle
        print(
            f"H5 source {case_index}/{len(CASES)} {case_id} "
            f"map={source_map_residual:.3e} boundary={source_boundary}",
            flush=True,
        )

    for left_index, left_id in enumerate(CASES):
        for right_id in CASES[left_index + 1 :]:
            left = source_data[left_id]
            right = source_data[right_id]
            difference = left["states"] - right["states"]
            distinct = bool(
                left["state_artifact_hash"] != right["state_artifact_hash"]
                and left["state_array_hash"] != right["state_array_hash"]
                and np.max(np.abs(difference)) > 0.0
            )
            independence_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "left_case_id": left_id,
                    "right_case_id": right_id,
                    "state_artifact_hash_distinct": (
                        left["state_artifact_hash"] != right["state_artifact_hash"]
                    ),
                    "state_array_hash_distinct": (
                        left["state_array_hash"] != right["state_array_hash"]
                    ),
                    "state_rms_difference": float(np.sqrt(np.mean(difference**2))),
                    "state_max_abs_difference": float(np.max(np.abs(difference))),
                    "mapping_time_difference_days": abs(
                        left["mapping_time"] - right["mapping_time"]
                    ) * system.time_unit_days,
                    "rho_difference": abs(left["rho"] - right["rho"]),
                    "distinct_local_source_artifacts": distinct,
                    "status": "pass" if distinct else "fail",
                    "source_git_commit": commit,
                }
            )

    for case_id in CASES:
        data = source_data[case_id]
        case = data["case"]
        cocycle = data["cocycle"]
        phases = data["phases"]
        rho = data["rho"]
        source_boundary = data["source_boundary"]
        case_attempts: dict[str, list[tuple[dict[str, Any], InvariantBundleResult]]] = {
            method: [] for method in METHODS
        }

        started = time.perf_counter()
        traditional = traditional_pointwise_eigen_bundle(cocycle, phases, rho)
        runtime = time.perf_counter() - started
        row = _attempt_row(
            run_id=run_id,
            case=case,
            method=METHODS[0],
            attempt_index=1,
            variant="pointwise_baseline",
            iteration_cap=0,
            result=traditional,
            runtime=runtime,
            source_boundary=source_boundary,
            cocycle_hash=data["cocycle_hash"],
            h1_hash=h1_hash,
            commit=commit,
        )
        attempt_rows.append(row)
        case_attempts[METHODS[0]].append((row, traditional))

        schur_results: list[InvariantBundleResult] = []
        for attempt_index, refinement in enumerate((0, 1, 4), start=1):
            started = time.perf_counter()
            result = real_schur_bundle_tracking(
                cocycle,
                phases,
                rho,
                refinement_iterations=refinement,
            )
            runtime = time.perf_counter() - started
            schur_results.append(result)
            row = _attempt_row(
                run_id=run_id,
                case=case,
                method=METHODS[1],
                attempt_index=attempt_index,
                variant=f"graph_refinement_{refinement}",
                iteration_cap=refinement,
                result=result,
                runtime=runtime,
                source_boundary=source_boundary,
                cocycle_hash=data["cocycle_hash"],
                h1_hash=h1_hash,
                commit=commit,
            )
            attempt_rows.append(row)
            case_attempts[METHODS[1]].append((row, result))

        schur_seed = schur_results[-1].bases
        qr_initializations = (
            ("local_svd", None),
            ("refined_schur_seed", schur_seed),
            (
                "deterministic_random",
                _local_random_bases(21, seed=5000 + CASES.index(case_id)),
            ),
        )
        for attempt_index, (variant, initial_bases) in enumerate(
            qr_initializations, start=1
        ):
            started = time.perf_counter()
            result = qr_svd_cocycle_bundle_iteration(
                cocycle,
                phases,
                rho,
                bundle_dimension=1,
                max_iterations=int(case["max_iterations"]),
                angle_tolerance_deg=QR_ANGLE_TOLERANCE_DEG,
                initial_bases=initial_bases,
            )
            runtime = time.perf_counter() - started
            row = _attempt_row(
                run_id=run_id,
                case=case,
                method=METHODS[2],
                attempt_index=attempt_index,
                variant=variant,
                iteration_cap=int(case["max_iterations"]),
                result=result,
                runtime=runtime,
                source_boundary=source_boundary,
                cocycle_hash=data["cocycle_hash"],
                h1_hash=h1_hash,
                commit=commit,
            )
            attempt_rows.append(row)
            case_attempts[METHODS[2]].append((row, result))

        status_rank = {"accepted": 0, "boundary": 1, "fail": 2}
        for method in METHODS:
            selected_row, selected_result = min(
                case_attempts[method],
                key=lambda item: (
                    status_rank[str(item[0]["h5_status"])],
                    float(item[0]["max_invariance_residual"]),
                ),
            )
            selected_row["selected_for_benchmark"] = True
            selected_results[(case_id, method)] = selected_result
            selected_attempts[(case_id, method)] = selected_row
            output_method = (
                "ordered_partial_real_schur_tracking"
                if selected_result.method == "ordered_real_schur_tracking"
                else selected_result.method
            )
            multiplier = _bundle_multiplier(selected_result)
            benchmark_rows.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "case_id": case_id,
                    "member_id": case["member_id"],
                    "family": case["family"],
                    "system": case["system"],
                    "method": output_method,
                    "selected_attempt_index": selected_row["attempt_index"],
                    "selected_variant": selected_row["variant"],
                    "spectral_samples": 21,
                    "bundle_dimension": selected_result.bundle_dimension,
                    "classification": selected_result.classification,
                    "max_invariance_residual": selected_result.max_invariance_residual,
                    "mean_invariance_residual": selected_result.mean_invariance_residual,
                    "selection_residual": selected_result.selection_residual,
                    "phase_principal_angle_max_deg": (
                        selected_result.max_phase_principal_angle_deg
                    ),
                    "iterations": selected_result.iterations,
                    "converged": selected_result.converged,
                    "selected_spectrum": ";".join(
                        format(complex(value), ".16g")
                        for value in selected_result.selected_spectrum
                    ),
                    "bundle_multiplier_estimate": multiplier,
                    "lyapunov_estimate_per_day": math.log(multiplier)
                    / float(case["mapping_time_days"]),
                    "source_map_residual_recomputed": data["source_map_residual"],
                    "source_map_status": "pass",
                    "source_jacobi_span": data["jacobi_span"],
                    "source_gate_status": case["source_gate_status"],
                    "evidence_class": case["evidence_class"],
                    "source_authority_boundary": source_boundary,
                    "new_vs_stage_c_registry": data["new_vs_stage_c"],
                    "research_status": selected_row["h5_status"],
                    "failure_reason": selected_row["failure_reason"],
                    "cocycle_sha256": data["cocycle_hash"],
                    "h1_registry_sha256": h1_hash,
                    "source_git_commit": commit,
                }
            )
            prefix = _key(case_id, output_method)
            arrays[prefix + "__bases"] = selected_result.bases
            arrays[prefix + "__local_reduced_maps"] = (
                selected_result.local_reduced_maps
            )
            arrays[prefix + "__invariance_residuals"] = (
                selected_result.invariance_residuals
            )
            arrays[prefix + "__selected_spectrum"] = (
                selected_result.selected_spectrum
            )
            arrays[prefix + "__convergence_history"] = (
                selected_result.convergence_history
            )

    benchmark_index = {
        (row["case_id"], row["method"]): row for row in benchmark_rows
    }
    surfaces: dict[tuple[str, str, int], np.ndarray] = {}
    displacements: dict[tuple[str, str, int], np.ndarray] = {}
    for case_id in CASES:
        data = source_data[case_id]
        case = data["case"]
        states = data["states"]
        duration = data["mapping_time"]
        evaluation_times = np.linspace(0.0, duration, TIME_SAMPLES)
        base_solution = integrate_states_and_stms(
            states,
            (0.0, duration),
            system.mu,
            t_eval=evaluation_times,
            max_step=0.005,
        )
        if not base_solution.success:
            raise RuntimeError(base_solution.message)
        base_values = base_solution.y.T.reshape(TIME_SAMPLES, 21, 42)
        base_history = base_values[:, :, :6]
        state_transition_history = base_values[:, :, 6:].reshape(
            TIME_SAMPLES, 21, 6, 6
        )
        case_prefix = _sanitize(case_id)
        arrays[case_prefix + "__times_nd"] = evaluation_times
        arrays[case_prefix + "__base_states"] = base_history
        qr_direction = selected_results[(case_id, METHODS[2])].bases[:, :, 0]
        secondary_position = np.array([1.0 - system.mu, 0.0, 0.0])
        for method in METHODS:
            benchmark = benchmark_index[(case_id, method)]
            result = selected_results[(case_id, method)]
            direction = result.bases[:, :, 0].copy()
            dots = np.sum(direction * qr_direction, axis=1)
            if float(np.mean(dots)) < 0.0:
                direction *= -1.0
                dots *= -1.0
            direction_angle = float(
                np.max(
                    np.degrees(np.arccos(np.clip(np.abs(dots), 0.0, 1.0)))
                )
            )
            branch_consistent = bool(np.all(dots > 0.0))
            arrays[_key(case_id, method) + "__directions"] = direction
            for sign in SIGNS:
                started = time.perf_counter()
                initial = states + float(sign) * PERTURBATION * direction
                solution = integrate_states_cr3bp(
                    initial,
                    (0.0, duration),
                    system.mu,
                    t_eval=evaluation_times,
                    max_step=0.005,
                )
                if not solution.success:
                    raise RuntimeError(solution.message)
                history = solution.y.T.reshape(TIME_SAMPLES, 21, 6)
                separation = np.linalg.norm(history - base_history, axis=2)
                linear = np.einsum(
                    "tnij,nj->tni",
                    state_transition_history,
                    float(sign) * PERTURBATION * direction,
                )
                linear_separation = np.linalg.norm(linear, axis=2)
                ratios = separation[1:] / np.maximum(
                    linear_separation[1:], np.finfo(float).tiny
                )
                jacobi = jacobi_constant(
                    history.reshape(-1, 6), system.mu
                ).reshape(TIME_SAMPLES, 21)
                jacobi_drift = float(
                    np.max(np.abs(jacobi - jacobi[0][None, :]))
                )
                growth = separation[-1] / PERTURBATION
                secondary_distance = np.linalg.norm(
                    history[:, :, :3] - secondary_position, axis=2
                )
                initial_ratio = float(np.mean(ratios[0]))
                numerical_pass = bool(
                    jacobi_drift <= JACOBI_LIMIT
                    and abs(initial_ratio - 1.0)
                    <= INITIAL_LINEAR_RATIO_TOLERANCE
                )
                reasons: list[str] = []
                if benchmark["research_status"] == "fail":
                    reasons.append("upstream_benchmark_failed")
                if jacobi_drift > JACOBI_LIMIT:
                    reasons.append("jacobi_drift_gt_1e-10")
                if (
                    abs(initial_ratio - 1.0)
                    > INITIAL_LINEAR_RATIO_TOLERANCE
                ):
                    reasons.append("initial_linear_ratio_outside_5pct")
                if not numerical_pass or benchmark["research_status"] == "fail":
                    status = "fail"
                elif benchmark["research_status"] == "boundary":
                    status = "boundary"
                else:
                    status = "accepted"
                manifold_rows.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "case_id": case_id,
                        "member_id": case["member_id"],
                        "family": case["family"],
                        "system": case["system"],
                        "method": method,
                        "branch": "unstable",
                        "propagation_direction": "forward",
                        "bundle_dimension": result.bundle_dimension,
                        "spectral_samples": 21,
                        "subspace_angular_samples": 1,
                        "perturbation_sign": sign,
                        "perturbation_norm": PERTURBATION,
                        "propagation_time_nd": duration,
                        "propagation_time_days": duration * system.time_unit_days,
                        "time_samples": TIME_SAMPLES,
                        "coordinate_system": "cr3bp_synodic_rotating_nondimensional",
                        "integrator": "DOP853_rtol1e-11_atol1e-13",
                        "event_condition": case["event_condition"],
                        "benchmark_research_status": benchmark["research_status"],
                        "benchmark_invariance_residual_max": float(
                            benchmark["max_invariance_residual"]
                        ),
                        "manifold_generated": True,
                        "diagnostic_only": benchmark["research_status"] == "fail",
                        "direction_principal_angle_max_deg_to_qr": direction_angle,
                        "branch_sign_consistent": branch_consistent,
                        "manifold_jacobi_drift": jacobi_drift,
                        "initial_linear_growth_ratio": initial_ratio,
                        "final_linear_growth_ratio": float(np.mean(ratios[-1])),
                        "forward_growth_factor_mean": float(np.mean(growth)),
                        "forward_growth_factor_max": float(np.max(growth)),
                        "secondary_min_distance_km": float(
                            np.min(secondary_distance) * system.length_unit_km
                        ),
                        "normalized_3d_manifold_distance_to_qr": float("nan"),
                        "normalized_displacement_distance_to_qr": float("nan"),
                        "runtime_seconds": time.perf_counter() - started,
                        "status": status,
                        "failure_reason": ";".join(reasons),
                        "cocycle_sha256": data["cocycle_hash"],
                        "state_artifact_sha256": data["state_artifact_hash"],
                        "h1_registry_sha256": h1_hash,
                        "source_git_commit": commit,
                    }
                )
                key = (case_id, method, sign)
                surfaces[key] = history[:, :, :3]
                displacements[key] = (
                    history[:, :, :3] - base_history[:, :, :3]
                ) / PERTURBATION
                prefix = _manifold_key(case_id, method, sign)
                arrays[prefix + "__manifold_states"] = history
                arrays[prefix + "__linear_separation"] = linear_separation

    manifold_index = {
        (row["case_id"], row["method"], int(row["perturbation_sign"])): row
        for row in manifold_rows
    }
    for key, row in manifold_index.items():
        case_id, method, sign = key
        qr_key = (case_id, METHODS[2], sign)
        _, row["normalized_3d_manifold_distance_to_qr"] = stage_f._symmetric_hd95(
            surfaces[qr_key], surfaces[key]
        )
        _, row["normalized_displacement_distance_to_qr"] = stage_f._symmetric_hd95(
            displacements[qr_key], displacements[key]
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(SOURCE_CSV, SOURCE_FIELDS, source_rows)
    _write_csv(INDEPENDENCE_CSV, INDEPENDENCE_FIELDS, independence_rows)
    _write_csv(ATTEMPTS_CSV, ATTEMPT_FIELDS, attempt_rows)
    _write_csv(BENCHMARK_CSV, BENCHMARK_FIELDS, benchmark_rows)
    _write_csv(MANIFOLD_CSV, MANIFOLD_FIELDS, manifold_rows)
    np.savez_compressed(RESULTS_NPZ, **arrays)
    benchmark_counts = Counter(str(row["research_status"]) for row in benchmark_rows)
    manifold_counts = Counter(str(row["status"]) for row in manifold_rows)
    improved = [row for row in benchmark_rows if row["method"] in IMPROVED_METHODS]
    cases_with_two_improved_boundaries = sum(
        all(
            row["research_status"] in {"accepted", "boundary"}
            for row in improved
            if row["case_id"] == case_id
        )
        for case_id in CASES
    )
    gate = bool(
        all(row["status"] == "pass" for row in source_rows)
        and all(row["status"] == "pass" for row in independence_rows)
        and cases_with_two_improved_boundaries == len(CASES)
        and all(row["status"] == "boundary" for row in manifold_rows if row["method"] in IMPROVED_METHODS)
    )
    elapsed = time.perf_counter() - started_campaign
    summary = {
        "schema_version": "submission_candidate_sun_earth_expansion_summary_v1",
        "run_id": run_id,
        "status": "complete",
        "independent_new_source_benchmarks": len(source_rows),
        "pairwise_independence_rows": len(independence_rows),
        "method_attempt_rows": len(attempt_rows),
        "benchmark_rows": len(benchmark_rows),
        "manifold_rows": len(manifold_rows),
        "benchmark_status_counts": dict(benchmark_counts),
        "manifold_status_counts": dict(manifold_counts),
        "cases_with_two_improved_boundary_or_better_methods": (
            cases_with_two_improved_boundaries
        ),
        "source_authority_boundary_cases": sum(
            bool(row["source_authority_boundary"]) for row in source_rows
        ),
        "h5_gate_status": "pass" if gate else "fail",
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
    _write_checkpoint({**summary, "completed_cases": list(CASES)})
    _write_environment(commit, run_id)
    _write_audit(
        source_rows,
        independence_rows,
        benchmark_rows,
        manifold_rows,
        summary,
    )
    _write_failure_evidence(attempt_rows, benchmark_rows, manifold_rows)
    _write_artifact_hashes(cocycle_paths)
    print(
        "STAGE-H5 SUN-EARTH EXPANSION WRITE PASS "
        f"cases={len(CASES)} benchmarks={len(benchmark_rows)} "
        f"manifolds={len(manifold_rows)} gate={summary['h5_gate_status']} "
        f"elapsed={elapsed:.3f}s",
        flush=True,
    )


def check_outputs() -> None:
    preregistration.check_outputs()
    sources = _read_csv(SOURCE_CSV)
    independence = _read_csv(INDEPENDENCE_CSV)
    attempts = _read_csv(ATTEMPTS_CSV)
    benchmarks = _read_csv(BENCHMARK_CSV)
    manifolds = _read_csv(MANIFOLD_CSV)
    if len(sources) != 3 or {row["case_id"] for row in sources} != set(CASES):
        raise RuntimeError("H5 source coverage drifted")
    if len(independence) != 3:
        raise RuntimeError("H5 pairwise independence grid drifted")
    if len(attempts) != 21:
        raise RuntimeError("H5 method-attempt grid drifted")
    if len(benchmarks) != 9:
        raise RuntimeError("H5 selected benchmark grid drifted")
    if len(manifolds) != 18:
        raise RuntimeError("H5 manifold grid drifted")
    if any(row["status"] != "pass" for row in sources):
        raise RuntimeError("H5 source validation no longer passes")
    if any(row["source_map_status"] != "pass" for row in sources):
        raise RuntimeError("H5 source map revalidation regressed")
    if any(row["source_authority_boundary"] != "true" for row in sources):
        raise RuntimeError("H5 source authority boundary was promoted")
    if any(row["new_vs_stage_c_registry"] != "true" for row in sources):
        raise RuntimeError("H5 source is no longer new versus Stage C")
    if any(row["status"] != "pass" for row in independence):
        raise RuntimeError("H5 local-source independence evidence regressed")
    if any(row["distinct_local_source_artifacts"] != "true" for row in independence):
        raise RuntimeError("H5 source artifacts are no longer distinct")

    selected = [row for row in attempts if row["selected_for_benchmark"] == "true"]
    if len(selected) != 9:
        raise RuntimeError("H5 selected-attempt count drifted")
    for case_id in CASES:
        case_attempts = [row for row in attempts if row["case_id"] == case_id]
        if Counter(row["method"] for row in case_attempts) != {
            METHODS[0]: 1,
            METHODS[1]: 3,
            METHODS[2]: 3,
        }:
            raise RuntimeError(f"H5 retry layout drifted for {case_id}")
    benchmark_counts = Counter(row["research_status"] for row in benchmarks)
    if benchmark_counts != {"boundary": 6, "fail": 3}:
        raise RuntimeError(f"H5 benchmark outcomes drifted: {benchmark_counts}")
    for row in benchmarks:
        if int(row["bundle_dimension"]) != 1:
            raise RuntimeError("H5 selected bundle dimension drifted")
        if row["method"] in IMPROVED_METHODS:
            if row["research_status"] != "boundary":
                raise RuntimeError("H5 improved method was promoted or failed")
            residual = float(row["max_invariance_residual"])
            if not PASS_INVARIANCE < residual <= BOUNDARY_INVARIANCE:
                raise RuntimeError("H5 improved residual left the boundary band")
        else:
            if row["research_status"] != "fail":
                raise RuntimeError("H5 pointwise failure was promoted")

    manifold_counts = Counter(row["status"] for row in manifolds)
    if manifold_counts != {"boundary": 12, "fail": 6}:
        raise RuntimeError(f"H5 manifold outcomes drifted: {manifold_counts}")
    for row in manifolds:
        if row["manifold_generated"] != "true":
            raise RuntimeError("H5 manifold history is missing")
        if float(row["manifold_jacobi_drift"]) > JACOBI_LIMIT:
            raise RuntimeError("H5 manifold violates the Jacobi gate")
        if (
            abs(float(row["initial_linear_growth_ratio"]) - 1.0)
            > INITIAL_LINEAR_RATIO_TOLERANCE
        ):
            raise RuntimeError("H5 manifold violates the linearity gate")
        if row["method"] in IMPROVED_METHODS and row["status"] != "boundary":
            raise RuntimeError("H5 improved manifold boundary drifted")
        if row["method"] == METHODS[0] and row["diagnostic_only"] != "true":
            raise RuntimeError("H5 failed pointwise propagation lost diagnostic label")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["h5_gate_status"] != "pass":
        raise RuntimeError("stored H5 gate is not passing")
    if summary["independent_new_source_benchmarks"] != 3:
        raise RuntimeError("H5 new-source count drifted")
    if summary["source_authority_boundary_cases"] != 3:
        raise RuntimeError("H5 source boundary count drifted")

    with np.load(RESULTS_NPZ, allow_pickle=False) as archive:
        for case_id in CASES:
            prefix = _sanitize(case_id)
            if archive[prefix + "__states"].shape != (21, 6):
                raise RuntimeError("H5 state archive shape drifted")
            if archive[prefix + "__stms"].shape != (21, 6, 6):
                raise RuntimeError("H5 STM archive shape drifted")
            if archive[prefix + "__base_states"].shape != (41, 21, 6):
                raise RuntimeError("H5 base-state archive shape drifted")
            for method in METHODS:
                if archive[_key(case_id, method) + "__bases"].shape != (21, 6, 1):
                    raise RuntimeError("H5 bundle archive shape drifted")
                for sign in SIGNS:
                    key = _manifold_key(case_id, method, sign)
                    if archive[key + "__manifold_states"].shape != (41, 21, 6):
                        raise RuntimeError("H5 manifold archive shape drifted")
        for row in sources:
            cache_path = ROOT / row["cocycle_artifact"]
            if artifact_fingerprint(cache_path).sha256 != row["cocycle_sha256"]:
                raise RuntimeError("H5 cocycle hash drifted")
            with np.load(cache_path, allow_pickle=False) as cache:
                if cache["stms"].shape != (21, 6, 6):
                    raise RuntimeError("H5 cocycle cache shape drifted")

    hash_rows = _read_csv(ARTIFACT_HASHES)
    if len(hash_rows) != 14:
        raise RuntimeError("H5 artifact-hash manifest row count drifted")
    for row in hash_rows:
        path = ROOT / row["artifact"]
        if not fingerprint_matches(
            path,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(f"H5 artifact fingerprint mismatch: {path}")
    audit = AUDIT.read_text(encoding="utf-8")
    for marker in (
        "external independent solver or independent physical experiment",
        "no numerical method can be promoted above boundary",
        "The frozen Stage-C registry is not modified",
    ):
        if marker not in audit:
            raise RuntimeError(f"H5 audit boundary marker missing: {marker}")
    print(
        "STAGE-H5 SUN-EARTH EXPANSION CHECK PASS "
        f"cases={len(CASES)} benchmarks={len(benchmarks)} "
        f"manifolds={len(manifolds)} gate=pass",
        flush=True,
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
