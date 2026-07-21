"""Build the preregistered Stage-H3 Route-H two-dimensional manifolds.

The frozen Stage-E tables classify the two Route-H cases as failures because
their phase-wise orthonormal frames do not survive Fourier interpolation at
the frozen N45 resolution.  This generator does not rewrite that evidence.
It retains those failures and separately validates the latent complex
eigenfield before local gauge normalization.  A complex eigenfield and its
conjugate define a real two-dimensional invariant subspace, so its real and
imaginary parts provide a gauge-consistent representation for the H3 sheet.
"""

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
from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    fingerprint_matches,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.invariant_bundles import (  # noqa: E402
    assemble_discrete_cocycle_operator,
    periodic_interpolation_matrix,
    qr_svd_cocycle_bundle_iteration,
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
STAGE_E_CSV = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "method_comparison.csv"
)
STAGE_E_NPZ = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "npz"
    / "method_comparison.npz"
)
INDEPENDENT_CSV = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "results"
    / "csv"
    / "independent_schur_backend_comparison.csv"
)

OUTPUT_DIR = STAGE_H / "results" / "route_h_2d_manifolds"
ATTEMPTS_CSV = OUTPUT_DIR / "route_h_2d_method_attempts.csv"
DIAGNOSTICS_CSV = OUTPUT_DIR / "route_h_2d_subspace_diagnostics.csv"
MANIFOLD_CSV = OUTPUT_DIR / "route_h_2d_manifold_convergence.csv"
RESULTS_NPZ = OUTPUT_DIR / "route_h_2d_manifold_results.npz"
SUMMARY = OUTPUT_DIR / "route_h_2d_summary.json"
CHECKPOINT = OUTPUT_DIR / "route_h_2d_checkpoint.json"
ENVIRONMENT = OUTPUT_DIR / "environment.json"
AUDIT = OUTPUT_DIR / "route_h_2d_audit.md"
FAILURE_EVIDENCE = OUTPUT_DIR / "failure_evidence.md"
ARTIFACT_HASHES = OUTPUT_DIR / "artifact_hashes.csv"

SCHEMA_VERSION = "submission_candidate_route_h_2d_manifold_v1"
CASES = (
    "h3_route_h_member_68_2d",
    "h3_route_h_member_32_2d",
)
METHODS = (
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
)
PERTURBATIONS = (5.0e-8, 1.0e-7)
ANGULAR_SAMPLES = 8
HYPERBOLIC_TOLERANCE = 1.0e-3
INVARIANCE_LIMIT = 1.0e-6
SELECTION_LIMIT = 1.0e-8
JACOBI_LIMIT = 1.0e-10
INITIAL_LINEAR_RATIO_TOLERANCE = 0.05
QR_ANGLE_TOLERANCE_DEG = 2.0e-6

ATTEMPT_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "family",
    "system",
    "method",
    "attempt_index",
    "initialization",
    "iteration_cap",
    "iterations_executed",
    "bundle_dimension",
    "classification",
    "target_eigenvalue_real",
    "target_eigenvalue_imag",
    "target_eigenvalue_abs",
    "global_selection_residual",
    "raw_equation_residual_max",
    "gauge_consistent_subspace_residual_max",
    "legacy_normalized_frame_residual_max",
    "algorithm_invariance_residual_max",
    "raw_local_condition_max",
    "converged",
    "stage_e_research_status",
    "independent_dimension_agreement",
    "independent_validation_verdict",
    "h3_status",
    "failure_reason",
    "runtime_seconds",
    "h1_registry_sha256",
    "stage_c_registry_sha256",
    "stage_e_npz_sha256",
    "independent_csv_sha256",
    "cocycle_cache_sha256",
    "source_git_commit",
)

DIAGNOSTIC_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "phase_index",
    "phase_rad",
    "raw_local_rank",
    "raw_singular_value_max",
    "raw_singular_value_min",
    "raw_local_condition",
    "raw_equation_residual",
    "gauge_consistent_subspace_residual",
    "local_map_singular_value_max",
    "local_map_singular_value_min",
    "local_area_multiplier_sqrt",
    "stage_e_normalized_frame_residual",
    "normalized_projector_interpolation_residual",
    "source_git_commit",
)

MANIFOLD_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "source_case_id",
    "family",
    "system",
    "method",
    "branch",
    "propagation_direction",
    "bundle_dimension",
    "spectral_samples",
    "angular_samples",
    "perturbation_norm",
    "propagation_time_nd",
    "propagation_time_days",
    "time_samples",
    "coordinate_system",
    "integrator",
    "event_condition",
    "stage_e_research_status",
    "h3_representation_status",
    "manifold_generated",
    "target_eigenvalue_abs",
    "global_selection_residual",
    "gauge_consistent_subspace_residual_max",
    "initial_sheet_rank_min",
    "antipodal_direction_error_max",
    "direction_norm_min",
    "direction_norm_max",
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio_mean",
    "initial_linear_growth_ratio_max_deviation",
    "final_linear_growth_ratio_mean",
    "final_linear_growth_ratio_max_deviation",
    "final_growth_factor_mean",
    "final_growth_factor_geometric_mean",
    "final_growth_factor_min",
    "final_growth_factor_max",
    "runtime_seconds",
    "status",
    "failure_reason",
    "h1_registry_sha256",
    "stage_e_npz_sha256",
    "cocycle_cache_sha256",
    "state_artifact_sha256",
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
        H1_REGISTRY,
        STAGE_C_REGISTRY,
        STAGE_E_CSV,
        STAGE_E_NPZ,
        INDEPENDENT_CSV,
        Path(__file__),
    ):
        digest.update(artifact_fingerprint(path).sha256.encode("ascii"))
    return digest.hexdigest().upper()[:20]


def _local_qr(values: np.ndarray) -> np.ndarray:
    bases = np.empty_like(values, dtype=float)
    for index, value in enumerate(values):
        q, r = np.linalg.qr(value, mode="reduced")
        if q.shape[1] != 2 or np.min(np.abs(np.diag(r))) < 1.0e-14:
            raise RuntimeError(f"two-dimensional frame lost rank at phase {index}")
        signs = np.sign(np.diag(r))
        signs[signs == 0.0] = 1.0
        bases[index] = q * signs
    return bases


def _select_complex_pair(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
) -> dict[str, Any]:
    operator = assemble_discrete_cocycle_operator(cocycle, phases, rho)
    eigenvalues, eigenvectors = np.linalg.eig(operator)
    candidates = np.flatnonzero(
        np.abs(eigenvalues) > 1.0 + HYPERBOLIC_TOLERANCE
    )
    if candidates.size == 0:
        raise RuntimeError("Route-H operator has no unstable hyperbolic spectrum")
    values = eigenvalues[candidates]
    relative_imaginary = np.abs(values.imag) / np.maximum(
        np.abs(values), np.finfo(float).tiny
    )
    minimum = float(np.min(relative_imaginary))
    near_axis = candidates[relative_imaginary <= minimum + 1.0e-12]
    selected_index = int(
        near_axis[np.argmax(np.abs(eigenvalues[near_axis]))]
    )
    target = complex(eigenvalues[selected_index])
    if abs(target.imag) / abs(target) <= 1.0e-10:
        raise RuntimeError("preregistered Route-H target unexpectedly became real")
    eigenvector = eigenvectors[:, selected_index]
    selection_residual = float(
        np.linalg.norm(operator @ eigenvector - target * eigenvector)
        / max(np.linalg.norm(operator @ eigenvector), np.finfo(float).tiny)
    )
    complex_field = eigenvector.reshape(phases.size, 6)
    raw_frames = np.stack((complex_field.real, complex_field.imag), axis=2)
    forward = periodic_interpolation_matrix(phases, phases + rho)
    shifted_raw_frames = np.einsum("ij,jdk->idk", forward, raw_frames)
    multiplier = np.array(
        [[target.real, target.imag], [-target.imag, target.real]],
        dtype=float,
    )
    bases = _local_qr(raw_frames)
    shifted_bases = _local_qr(shifted_raw_frames)
    raw_singular_values = np.linalg.svd(raw_frames, compute_uv=False)
    raw_ranks = np.asarray(
        [np.linalg.matrix_rank(frame) for frame in raw_frames], dtype=int
    )
    equation_residuals = np.empty(phases.size, dtype=float)
    subspace_residuals = np.empty(phases.size, dtype=float)
    local_maps = np.empty((phases.size, 2, 2), dtype=float)
    local_map_singular_values = np.empty((phases.size, 2), dtype=float)
    for index, matrix in enumerate(cocycle):
        transported_raw = matrix @ raw_frames[index]
        equation_defect = (
            transported_raw - shifted_raw_frames[index] @ multiplier
        )
        equation_residuals[index] = float(
            np.linalg.norm(equation_defect, ord="fro")
            / max(np.linalg.norm(transported_raw, ord="fro"), np.finfo(float).tiny)
        )
        transported = matrix @ bases[index]
        local_maps[index] = shifted_bases[index].T @ transported
        defect = transported - shifted_bases[index] @ local_maps[index]
        subspace_residuals[index] = float(
            np.linalg.norm(defect, ord="fro")
            / max(np.linalg.norm(transported, ord="fro"), np.finfo(float).tiny)
        )
        local_map_singular_values[index] = np.linalg.svd(
            local_maps[index], compute_uv=False
        )
    return {
        "operator": operator,
        "target": target,
        "selection_residual": selection_residual,
        "raw_frames": raw_frames,
        "shifted_raw_frames": shifted_raw_frames,
        "bases": bases,
        "shifted_bases": shifted_bases,
        "raw_singular_values": raw_singular_values,
        "raw_ranks": raw_ranks,
        "equation_residuals": equation_residuals,
        "subspace_residuals": subspace_residuals,
        "local_maps": local_maps,
        "local_map_singular_values": local_map_singular_values,
    }


def _normalized_projector_residuals(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    legacy_bases: np.ndarray,
) -> np.ndarray:
    projectors = np.einsum("nik,njk->nij", legacy_bases, legacy_bases)
    forward = periodic_interpolation_matrix(phases, phases + rho)
    shifted_projectors = np.einsum("ij,jab->iab", forward, projectors)
    residuals = np.empty(phases.size, dtype=float)
    for index, matrix in enumerate(cocycle):
        projector = 0.5 * (
            shifted_projectors[index] + shifted_projectors[index].T
        )
        values, vectors = np.linalg.eigh(projector)
        shifted_basis = vectors[:, np.argsort(values)[::-1][:2]]
        transported = matrix @ legacy_bases[index]
        reduced = shifted_basis.T @ transported
        defect = transported - shifted_basis @ reduced
        residuals[index] = float(
            np.linalg.norm(defect, ord="fro")
            / max(np.linalg.norm(transported, ord="fro"), np.finfo(float).tiny)
        )
    return residuals


def _deterministic_random_bases(samples: int, seed: int) -> np.ndarray:
    generator = np.random.default_rng(seed)
    return _local_qr(generator.standard_normal((samples, 6, 2)))


def _attempt_common(
    *,
    run_id: str,
    case: Mapping[str, str],
    source: Mapping[str, str],
    target: complex,
    stage_e_row: Mapping[str, str],
    independent_row: Mapping[str, str],
    h1_hash: str,
    stage_c_hash: str,
    stage_e_npz_hash: str,
    independent_hash: str,
    cache_hash: str,
    commit: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "case_id": case["case_id"],
        "source_case_id": source["case_id"],
        "family": source["family"],
        "system": source["system"],
        "target_eigenvalue_real": target.real,
        "target_eigenvalue_imag": target.imag,
        "target_eigenvalue_abs": abs(target),
        "stage_e_research_status": stage_e_row["research_status"],
        "independent_dimension_agreement": independent_row[
            "dimension_agreement"
        ],
        "independent_validation_verdict": independent_row[
            "validation_verdict"
        ],
        "h1_registry_sha256": h1_hash,
        "stage_c_registry_sha256": stage_c_hash,
        "stage_e_npz_sha256": stage_e_npz_hash,
        "independent_csv_sha256": independent_hash,
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
        "schema_version": "submission_candidate_route_h_2d_environment_v1",
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
    attempts: list[Mapping[str, Any]],
    manifolds: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
) -> None:
    schur_attempts = [
        row
        for row in attempts
        if row["method"] == "ordered_partial_real_schur_tracking"
    ]
    qr_attempts = [
        row
        for row in attempts
        if row["method"] == "qr_svd_shifted_cocycle_iteration"
    ]
    lines = [
        "# Stage H3 Route-H two-dimensional manifold audit",
        "",
        f"- Run ID: {summary['run_id']}",
        f"- Cases: {summary['cases']}",
        f"- Manifold rows: {summary['manifold_rows']}",
        f"- Accepted Schur sheet rows: {summary['accepted_schur_manifold_rows']}",
        f"- QR bounded-failure cases: {summary['qr_bounded_failure_cases']}",
        f"- H3 gate: {summary['h3_gate_status']}",
        "",
        "## Gauge-consistent two-dimensional result",
        "",
        "| case | |lambda| | global residual | raw equation max | subspace max | legacy normalized-frame max | condition max | status |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in schur_attempts:
        lines.append(
            f"| {row['case_id']} | {float(row['target_eigenvalue_abs']):.9f} | "
            f"{float(row['global_selection_residual']):.3e} | "
            f"{float(row['raw_equation_residual_max']):.3e} | "
            f"{float(row['gauge_consistent_subspace_residual_max']):.3e} | "
            f"{float(row['legacy_normalized_frame_residual_max']):.3e} | "
            f"{float(row['raw_local_condition_max']):.3e} | {row['h3_status']} |"
        )
    lines += [
        "",
        "The global complex eigenfield satisfies the frozen collocation operator",
        "to near machine precision. Its real and imaginary parts have local rank",
        "two at every phase and give a gauge-consistent real invariant subspace.",
        "The large Stage-E normalized-frame residual is retained: it measures the",
        "Fourier interpolation of a locally normalized gauge at N45, whose local",
        "conditioning is poor, rather than invalidating the latent complex pair.",
        "",
        "## Bounded QR/SVD retries",
        "",
        "| case | initialization | iterations | max residual | final angle deg | status |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in qr_attempts:
        lines.append(
            f"| {row['case_id']} | {row['initialization']} | "
            f"{row['iterations_executed']} | "
            f"{float(row['algorithm_invariance_residual_max']):.3e} | "
            f"{float(row['global_selection_residual']):.3e} | {row['h3_status']} |"
        )
    lines += [
        "",
        "No manifold was generated from a nonconverged QR/SVD frame.",
        "All three permitted attempts (initial plus two retries) remain preserved.",
        "",
        "## Nonlinear one-map sheets",
        "",
        "| case | method | epsilon | Jacobi drift | initial ratio | geometric growth | status |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in manifolds:
        if not bool(row["manifold_generated"]):
            continue
        lines.append(
            f"| {row['case_id']} | {row['method']} | "
            f"{float(row['perturbation_norm']):.1e} | "
            f"{float(row['manifold_jacobi_drift']):.3e} | "
            f"{float(row['initial_linear_growth_ratio_mean']):.9f} | "
            f"{float(row['final_growth_factor_geometric_mean']):.6f} | "
            f"{row['status']} |"
        )
    lines += [
        "",
        "## Authority boundary",
        "",
        "Stage-E method_comparison.csv remains unchanged and both physical Route-H",
        "Schur rows remain research_status=fail under the normalized-frame metric.",
        "H3 adds a two-dimensional research object; it does not relabel the object",
        "as one-dimensional, does not promote the McCarthy reproduction baseline,",
        "and does not change the frozen Chapter 4 holdout or paper-equivalence gates.",
        "",
    ]
    AUDIT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def _write_failure_evidence(
    attempts: list[Mapping[str, Any]],
    manifolds: list[Mapping[str, Any]],
) -> None:
    failed_attempts = [
        row for row in attempts if str(row["h3_status"]) != "accepted"
    ]
    skipped = [
        row for row in manifolds if not bool(row["manifold_generated"])
    ]
    lines = [
        "# Stage H3 bounded-failure evidence",
        "",
        f"- Non-accepted method attempts retained: {len(failed_attempts)}",
        f"- Manifold cells deliberately not generated: {len(skipped)}",
        "",
    ]
    for row in failed_attempts:
        lines.append(
            f"- {row['case_id']} / {row['method']} / attempt "
            f"{row['attempt_index']} ({row['initialization']}): "
            f"{row['h3_status']} - {row['failure_reason']}"
        )
    lines += [
        "",
        "The frozen Stage-E Schur failures are also retained even though H3",
        "accepts the latent raw-gauge two-dimensional object. No one-dimensional",
        "Route-H result is introduced.",
        "",
    ]
    FAILURE_EVIDENCE.write_text(
        "\n".join(lines), encoding="utf-8", newline="\n"
    )


def _write_artifact_hashes() -> None:
    artifacts = (
        ATTEMPTS_CSV,
        DIAGNOSTICS_CSV,
        MANIFOLD_CSV,
        RESULTS_NPZ,
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


def _manifold_row_common(
    *,
    run_id: str,
    case: Mapping[str, str],
    source: Mapping[str, str],
    method: str,
    epsilon: float,
    duration: float,
    duration_days: float,
    target_abs: float,
    selection_residual: float,
    subspace_residual: float,
    stage_e_status: str,
    h3_status: str,
    h1_hash: str,
    stage_e_npz_hash: str,
    cache_hash: str,
    commit: str,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "case_id": case["case_id"],
        "source_case_id": source["case_id"],
        "family": source["family"],
        "system": source["system"],
        "method": method,
        "branch": "unstable",
        "propagation_direction": "forward",
        "bundle_dimension": 2,
        "spectral_samples": int(source["spectral_samples"]),
        "angular_samples": int(case["subspace_angular_samples"]),
        "perturbation_norm": epsilon,
        "propagation_time_nd": duration,
        "propagation_time_days": duration_days,
        "time_samples": int(case["time_samples"]),
        "coordinate_system": "cr3bp_synodic_rotating_nondimensional",
        "integrator": "DOP853_rtol1e-11_atol1e-13",
        "event_condition": case["event_condition"],
        "stage_e_research_status": stage_e_status,
        "h3_representation_status": h3_status,
        "target_eigenvalue_abs": target_abs,
        "global_selection_residual": selection_residual,
        "gauge_consistent_subspace_residual_max": subspace_residual,
        "h1_registry_sha256": h1_hash,
        "stage_e_npz_sha256": stage_e_npz_hash,
        "cocycle_cache_sha256": cache_hash,
        "state_artifact_sha256": case["state_artifact_sha256"],
        "source_git_commit": commit,
    }


def run_campaign(*, max_wall_seconds: float) -> None:
    preregistration.check_outputs()
    h1_rows = {
        row["case_id"]: row
        for row in _read_csv(H1_REGISTRY)
        if row["campaign"] == "H3_route_h_2d_manifold"
    }
    if tuple(h1_rows) != CASES:
        raise RuntimeError("the H3 Route-H case order drifted")
    cap = min(float(row["max_wall_seconds"]) for row in h1_rows.values())
    if max_wall_seconds <= 0.0 or max_wall_seconds > cap:
        raise ValueError(f"max-wall-seconds must be in (0, {cap}]")
    for row in h1_rows.values():
        if int(row["expected_bundle_dimension"]) != 2:
            raise RuntimeError("H3 must remain explicitly two-dimensional")
        if int(row["subspace_angular_samples"]) != ANGULAR_SAMPLES:
            raise RuntimeError("H3 angular sample count drifted")
        if int(row["max_iterations"]) != 500 or int(row["max_retries"]) != 2:
            raise RuntimeError("H3 retry boundary drifted")

    stage_c_rows = _read_csv(STAGE_C_REGISTRY)
    stage_c_index = {row["case_id"]: row for row in stage_c_rows}
    stage_e_rows = _read_csv(STAGE_E_CSV)
    stage_e_index = {
        (row["case_id"], row["method"]): row for row in stage_e_rows
    }
    independent_rows = _read_csv(INDEPENDENT_CSV)
    independent_index = {row["case_id"]: row for row in independent_rows}
    h1_hash = artifact_fingerprint(H1_REGISTRY).sha256
    stage_c_hash = artifact_fingerprint(STAGE_C_REGISTRY).sha256
    stage_e_npz_hash = artifact_fingerprint(STAGE_E_NPZ).sha256
    independent_hash = artifact_fingerprint(INDEPENDENT_CSV).sha256
    run_id = _run_id()
    commit = _git_commit()
    campaign_started = time.perf_counter()
    attempts: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    manifolds: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "case_ids": np.asarray(CASES),
        "methods": np.asarray(METHODS),
        "perturbations": np.asarray(PERTURBATIONS),
        "angles_rad": np.linspace(
            0.0, 2.0 * np.pi, ANGULAR_SAMPLES, endpoint=False
        ),
        "h1_registry_sha256": np.asarray([h1_hash]),
        "stage_e_npz_sha256": np.asarray([stage_e_npz_hash]),
        "source_git_commit": np.asarray([commit]),
    }
    completed_cases: list[str] = []

    with np.load(STAGE_E_NPZ, allow_pickle=False) as stage_e_archive:
        for case_index, case_id in enumerate(CASES, start=1):
            elapsed = time.perf_counter() - campaign_started
            if elapsed > max_wall_seconds:
                _write_checkpoint(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "status": "wall_time_cap_reached",
                        "completed_cases": completed_cases,
                        "elapsed_seconds": elapsed,
                        "max_wall_seconds": max_wall_seconds,
                    }
                )
                raise RuntimeError("H3 campaign reached the preregistered cap")

            case = h1_rows[case_id]
            source = stage_c_index[case["source_case_id"]]
            states, loaded_phases = stage_e._load_states(source)
            cocycle, phases, source_residual, cache_path, _ = (
                stage_e._load_or_compute_cocycle(source, refresh=False)
            )
            np.testing.assert_allclose(phases, loaded_phases, rtol=0.0, atol=0.0)
            source_status = stage_e._source_map_status(source, source_residual)
            if source_status != "pass":
                raise RuntimeError(f"{source['case_id']} source revalidation failed")
            cache_hash = artifact_fingerprint(cache_path).sha256
            rho = float(source["rho"])
            pair_started = time.perf_counter()
            pair = _select_complex_pair(cocycle, phases, rho)
            pair_runtime = time.perf_counter() - pair_started
            target = pair["target"]
            if pair["raw_ranks"].min() != 2:
                raise RuntimeError(f"{source['case_id']} latent real pair lost rank")

            schur_method = METHODS[0]
            qr_method = METHODS[1]
            schur_stage_e = stage_e_index[(source["case_id"], schur_method)]
            qr_stage_e = stage_e_index[(source["case_id"], qr_method)]
            independent = independent_index[source["case_id"]]
            if (
                independent["dimension_agreement"] != "true"
                or int(independent["independent_selected_block_dimension"]) != 2
                or independent["validation_verdict"] != "accepted"
            ):
                raise RuntimeError("independent Schur dimension evidence drifted")

            legacy_prefix = f"{source['case_id']}__{schur_method}"
            legacy_bases = np.asarray(
                stage_e_archive[legacy_prefix + "__bases"], dtype=float
            )
            legacy_residuals = np.asarray(
                stage_e_archive[legacy_prefix + "__invariance_residuals"],
                dtype=float,
            )
            projector_residuals = _normalized_projector_residuals(
                cocycle, phases, rho, legacy_bases
            )
            common = _attempt_common(
                run_id=run_id,
                case=case,
                source=source,
                target=target,
                stage_e_row=schur_stage_e,
                independent_row=independent,
                h1_hash=h1_hash,
                stage_c_hash=stage_c_hash,
                stage_e_npz_hash=stage_e_npz_hash,
                independent_hash=independent_hash,
                cache_hash=cache_hash,
                commit=commit,
            )
            schur_accepted = bool(
                pair["selection_residual"] <= SELECTION_LIMIT
                and np.max(pair["equation_residuals"]) <= INVARIANCE_LIMIT
                and np.max(pair["subspace_residuals"]) <= INVARIANCE_LIMIT
                and pair["raw_ranks"].min() == 2
                and abs(target) > 1.0 + HYPERBOLIC_TOLERANCE
            )
            schur_reason = ""
            if not schur_accepted:
                schur_reason = "latent_complex_pair_failed_h3_subspace_gate"
            attempts.append(
                {
                    **common,
                    "method": schur_method,
                    "attempt_index": 1,
                    "initialization": "global_complex_eigenfield_realification",
                    "iteration_cap": 0,
                    "iterations_executed": 0,
                    "bundle_dimension": 2,
                    "classification": "real_2d_complex_pair_invariant_subspace",
                    "global_selection_residual": pair["selection_residual"],
                    "raw_equation_residual_max": float(
                        np.max(pair["equation_residuals"])
                    ),
                    "gauge_consistent_subspace_residual_max": float(
                        np.max(pair["subspace_residuals"])
                    ),
                    "legacy_normalized_frame_residual_max": float(
                        np.max(legacy_residuals)
                    ),
                    "algorithm_invariance_residual_max": float(
                        np.max(pair["subspace_residuals"])
                    ),
                    "raw_local_condition_max": float(
                        np.max(
                            pair["raw_singular_values"][:, 0]
                            / pair["raw_singular_values"][:, 1]
                        )
                    ),
                    "converged": schur_accepted,
                    "h3_status": "accepted" if schur_accepted else "bounded_fail",
                    "failure_reason": schur_reason,
                    "runtime_seconds": pair_runtime,
                }
            )

            for phase_index, phase in enumerate(phases):
                singular = pair["raw_singular_values"][phase_index]
                local_singular = pair["local_map_singular_values"][phase_index]
                diagnostics.append(
                    {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_id,
                        "case_id": case_id,
                        "source_case_id": source["case_id"],
                        "phase_index": phase_index,
                        "phase_rad": phase,
                        "raw_local_rank": pair["raw_ranks"][phase_index],
                        "raw_singular_value_max": singular[0],
                        "raw_singular_value_min": singular[1],
                        "raw_local_condition": singular[0] / singular[1],
                        "raw_equation_residual": pair["equation_residuals"][
                            phase_index
                        ],
                        "gauge_consistent_subspace_residual": pair[
                            "subspace_residuals"
                        ][phase_index],
                        "local_map_singular_value_max": local_singular[0],
                        "local_map_singular_value_min": local_singular[1],
                        "local_area_multiplier_sqrt": math.sqrt(
                            abs(np.linalg.det(pair["local_maps"][phase_index]))
                        ),
                        "stage_e_normalized_frame_residual": legacy_residuals[
                            phase_index
                        ],
                        "normalized_projector_interpolation_residual": (
                            projector_residuals[phase_index]
                        ),
                        "source_git_commit": commit,
                    }
                )

            case_prefix = _sanitize(case_id)
            arrays[case_prefix + "__phases"] = phases
            arrays[case_prefix + "__states"] = states
            arrays[case_prefix + "__target_spectrum"] = np.asarray(
                [target, np.conj(target)]
            )
            arrays[case_prefix + "__raw_frames"] = pair["raw_frames"]
            arrays[case_prefix + "__shifted_raw_frames"] = pair[
                "shifted_raw_frames"
            ]
            arrays[case_prefix + "__orthonormal_bases"] = pair["bases"]
            arrays[case_prefix + "__shifted_orthonormal_bases"] = pair[
                "shifted_bases"
            ]
            arrays[case_prefix + "__raw_equation_residuals"] = pair[
                "equation_residuals"
            ]
            arrays[case_prefix + "__subspace_residuals"] = pair[
                "subspace_residuals"
            ]
            arrays[case_prefix + "__local_reduced_maps"] = pair["local_maps"]

            qr_results: list[tuple[dict[str, Any], Any]] = []
            initializations = (
                ("local_svd", None),
                ("schur_seed", pair["bases"]),
                (
                    "deterministic_random",
                    _deterministic_random_bases(
                        phases.size, seed=1000 + int(case["member_id"])
                    ),
                ),
            )
            for attempt_index, (initialization, initial_bases) in enumerate(
                initializations, start=1
            ):
                started = time.perf_counter()
                result = qr_svd_cocycle_bundle_iteration(
                    cocycle,
                    phases,
                    rho,
                    branch="unstable",
                    bundle_dimension=2,
                    max_iterations=int(case["max_iterations"]),
                    angle_tolerance_deg=QR_ANGLE_TOLERANCE_DEG,
                    initial_bases=initial_bases,
                )
                runtime = time.perf_counter() - started
                qr_accepted = bool(
                    result.bundle_dimension == 2
                    and result.converged
                    and result.max_invariance_residual <= INVARIANCE_LIMIT
                )
                reasons: list[str] = []
                if not result.converged:
                    reasons.append("qr_iteration_not_converged_at_500")
                if result.max_invariance_residual > INVARIANCE_LIMIT:
                    reasons.append("algorithm_invariance_residual_gt_1e-6")
                qr_common = _attempt_common(
                    run_id=run_id,
                    case=case,
                    source=source,
                    target=target,
                    stage_e_row=qr_stage_e,
                    independent_row=independent,
                    h1_hash=h1_hash,
                    stage_c_hash=stage_c_hash,
                    stage_e_npz_hash=stage_e_npz_hash,
                    independent_hash=independent_hash,
                    cache_hash=cache_hash,
                    commit=commit,
                )
                attempt_row = {
                    **qr_common,
                    "method": qr_method,
                    "attempt_index": attempt_index,
                    "initialization": initialization,
                    "iteration_cap": int(case["max_iterations"]),
                    "iterations_executed": result.iterations,
                    "bundle_dimension": result.bundle_dimension,
                    "classification": result.classification,
                    "global_selection_residual": result.selection_residual,
                    "raw_equation_residual_max": float("nan"),
                    "gauge_consistent_subspace_residual_max": float("nan"),
                    "legacy_normalized_frame_residual_max": float(
                        qr_stage_e["max_invariance_residual"]
                    ),
                    "algorithm_invariance_residual_max": (
                        result.max_invariance_residual
                    ),
                    "raw_local_condition_max": float("nan"),
                    "converged": result.converged,
                    "h3_status": "accepted" if qr_accepted else "bounded_fail",
                    "failure_reason": ";".join(reasons),
                    "runtime_seconds": runtime,
                }
                attempts.append(attempt_row)
                qr_results.append((attempt_row, result))
                attempt_prefix = (
                    f"{case_prefix}__qr_attempt_{attempt_index}_{initialization}"
                )
                arrays[attempt_prefix + "__bases"] = result.bases
                arrays[attempt_prefix + "__invariance_residuals"] = (
                    result.invariance_residuals
                )
                arrays[attempt_prefix + "__convergence_history"] = (
                    result.convergence_history
                )

            accepted_qr = [
                item for item in qr_results if item[0]["h3_status"] == "accepted"
            ]
            best_qr = min(
                accepted_qr or qr_results,
                key=lambda item: float(item[0]["algorithm_invariance_residual_max"]),
            )
            method_bases: dict[str, tuple[np.ndarray | None, str, str]] = {
                schur_method: (
                    pair["bases"] if schur_accepted else None,
                    "accepted" if schur_accepted else "bounded_fail",
                    schur_stage_e["research_status"],
                ),
                qr_method: (
                    best_qr[1].bases if accepted_qr else None,
                    "accepted" if accepted_qr else "bounded_fail",
                    qr_stage_e["research_status"],
                ),
            }

            system = SYSTEMS[source["system"]]
            duration_days = float(source["mapping_time"])
            duration = duration_days / system.time_unit_days
            evaluation_times = np.linspace(
                0.0, duration, int(case["time_samples"])
            )
            max_step = 0.005 if source["system"] == "sun_earth" else 0.01
            base_solution = integrate_states_and_stms(
                states,
                (0.0, duration),
                system.mu,
                t_eval=evaluation_times,
                max_step=max_step,
            )
            if not base_solution.success:
                raise RuntimeError(base_solution.message)
            base_values = base_solution.y.T.reshape(
                evaluation_times.size, states.shape[0], 42
            )
            base_history = base_values[:, :, :6]
            state_transition_history = base_values[:, :, 6:].reshape(
                evaluation_times.size, states.shape[0], 6, 6
            )
            arrays[case_prefix + "__times_nd"] = evaluation_times
            arrays[case_prefix + "__base_states"] = base_history
            angles = np.asarray(arrays["angles_rad"], dtype=float)
            coefficients = np.vstack((np.cos(angles), np.sin(angles)))
            for method, (bases, h3_status, stage_e_status) in method_bases.items():
                if bases is None:
                    for epsilon in PERTURBATIONS:
                        row = _manifold_row_common(
                            run_id=run_id,
                            case=case,
                            source=source,
                            method=method,
                            epsilon=epsilon,
                            duration=duration,
                            duration_days=duration_days,
                            target_abs=abs(target),
                            selection_residual=pair["selection_residual"],
                            subspace_residual=float(
                                np.max(pair["subspace_residuals"])
                            ),
                            stage_e_status=stage_e_status,
                            h3_status=h3_status,
                            h1_hash=h1_hash,
                            stage_e_npz_hash=stage_e_npz_hash,
                            cache_hash=cache_hash,
                            commit=commit,
                        )
                        row.update(
                            {
                                "manifold_generated": False,
                                "initial_sheet_rank_min": 0,
                                "antipodal_direction_error_max": float("nan"),
                                "direction_norm_min": float("nan"),
                                "direction_norm_max": float("nan"),
                                "manifold_jacobi_drift": float("nan"),
                                "initial_linear_growth_ratio_mean": float("nan"),
                                "initial_linear_growth_ratio_max_deviation": float(
                                    "nan"
                                ),
                                "final_linear_growth_ratio_mean": float("nan"),
                                "final_linear_growth_ratio_max_deviation": float(
                                    "nan"
                                ),
                                "final_growth_factor_mean": float("nan"),
                                "final_growth_factor_geometric_mean": float("nan"),
                                "final_growth_factor_min": float("nan"),
                                "final_growth_factor_max": float("nan"),
                                "runtime_seconds": 0.0,
                                "status": "bounded_fail",
                                "failure_reason": (
                                    "upstream_2d_frame_not_converged_after_initial_plus_2_retries;"
                                    "manifold_not_generated"
                                ),
                            }
                        )
                        manifolds.append(row)
                    continue

                directions = np.einsum(
                    "ndk,ka->nad", np.asarray(bases, dtype=float), coefficients
                )
                ranks = np.asarray(
                    [np.linalg.matrix_rank(sheet) for sheet in directions],
                    dtype=int,
                )
                norms = np.linalg.norm(directions, axis=2)
                antipodal = float(
                    np.max(
                        np.linalg.norm(
                            directions[:, : ANGULAR_SAMPLES // 2]
                            + directions[:, ANGULAR_SAMPLES // 2 :],
                            axis=2,
                        )
                    )
                )
                arrays[_key(case_id, method) + "__directions"] = directions
                for epsilon in PERTURBATIONS:
                    started = time.perf_counter()
                    initial = (
                        states[:, None, :] + epsilon * directions
                    ).reshape(-1, 6)
                    solution = integrate_states_cr3bp(
                        initial,
                        (0.0, duration),
                        system.mu,
                        t_eval=evaluation_times,
                        max_step=max_step,
                    )
                    if not solution.success:
                        raise RuntimeError(solution.message)
                    history = solution.y.T.reshape(
                        evaluation_times.size,
                        states.shape[0],
                        ANGULAR_SAMPLES,
                        6,
                    )
                    separation = np.linalg.norm(
                        history - base_history[:, :, None, :], axis=3
                    )
                    linear = np.einsum(
                        "tnij,naj->tnai",
                        state_transition_history,
                        epsilon * directions,
                    )
                    linear_separation = np.linalg.norm(linear, axis=3)
                    ratios = separation[1:] / np.maximum(
                        linear_separation[1:], np.finfo(float).tiny
                    )
                    jacobi = jacobi_constant(
                        history.reshape(-1, 6), system.mu
                    ).reshape(
                        evaluation_times.size,
                        states.shape[0],
                        ANGULAR_SAMPLES,
                    )
                    jacobi_drift = float(
                        np.max(np.abs(jacobi - jacobi[0][None, :, :]))
                    )
                    growth = separation[-1] / epsilon
                    geometric_growth = float(
                        np.exp(
                            np.mean(
                                np.log(
                                    np.maximum(growth, np.finfo(float).tiny)
                                )
                            )
                        )
                    )
                    first_ratio_mean = float(np.mean(ratios[0]))
                    first_ratio_max_deviation = float(
                        np.max(np.abs(ratios[0] - 1.0))
                    )
                    final_ratio_mean = float(np.mean(ratios[-1]))
                    final_ratio_max_deviation = float(
                        np.max(np.abs(ratios[-1] - 1.0))
                    )
                    accepted = bool(
                        ranks.min() == 2
                        and jacobi_drift <= JACOBI_LIMIT
                        and abs(first_ratio_mean - 1.0)
                        <= INITIAL_LINEAR_RATIO_TOLERANCE
                        and geometric_growth > 1.0
                    )
                    reasons: list[str] = []
                    if ranks.min() != 2:
                        reasons.append("angular_sheet_rank_not_two")
                    if jacobi_drift > JACOBI_LIMIT:
                        reasons.append("jacobi_drift_gt_1e-10")
                    if (
                        abs(first_ratio_mean - 1.0)
                        > INITIAL_LINEAR_RATIO_TOLERANCE
                    ):
                        reasons.append("initial_linear_ratio_outside_5pct")
                    if geometric_growth <= 1.0:
                        reasons.append("forward_geometric_growth_not_unstable")
                    row = _manifold_row_common(
                        run_id=run_id,
                        case=case,
                        source=source,
                        method=method,
                        epsilon=epsilon,
                        duration=duration,
                        duration_days=duration_days,
                        target_abs=abs(target),
                        selection_residual=pair["selection_residual"],
                        subspace_residual=float(
                            np.max(pair["subspace_residuals"])
                        ),
                        stage_e_status=stage_e_status,
                        h3_status=h3_status,
                        h1_hash=h1_hash,
                        stage_e_npz_hash=stage_e_npz_hash,
                        cache_hash=cache_hash,
                        commit=commit,
                    )
                    row.update(
                        {
                            "manifold_generated": True,
                            "initial_sheet_rank_min": int(ranks.min()),
                            "antipodal_direction_error_max": antipodal,
                            "direction_norm_min": float(np.min(norms)),
                            "direction_norm_max": float(np.max(norms)),
                            "manifold_jacobi_drift": jacobi_drift,
                            "initial_linear_growth_ratio_mean": first_ratio_mean,
                            "initial_linear_growth_ratio_max_deviation": (
                                first_ratio_max_deviation
                            ),
                            "final_linear_growth_ratio_mean": final_ratio_mean,
                            "final_linear_growth_ratio_max_deviation": (
                                final_ratio_max_deviation
                            ),
                            "final_growth_factor_mean": float(np.mean(growth)),
                            "final_growth_factor_geometric_mean": geometric_growth,
                            "final_growth_factor_min": float(np.min(growth)),
                            "final_growth_factor_max": float(np.max(growth)),
                            "runtime_seconds": time.perf_counter() - started,
                            "status": "accepted" if accepted else "bounded_fail",
                            "failure_reason": ";".join(reasons),
                        }
                    )
                    manifolds.append(row)
                    prefix = (
                        f"{_key(case_id, method)}__eps_{epsilon:.0e}"
                    ).replace("-", "m").replace("+", "p")
                    arrays[prefix + "__manifold_states"] = history
                    arrays[prefix + "__linear_separation"] = linear_separation

            completed_cases.append(case_id)
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "running",
                    "completed_cases": completed_cases,
                    "total_cases": len(CASES),
                    "elapsed_seconds": time.perf_counter() - campaign_started,
                    "max_wall_seconds": max_wall_seconds,
                }
            )
            print(
                f"H3 Route-H {case_index}/{len(CASES)} {case_id} "
                f"|lambda|={abs(target):.9f} "
                f"subspace={np.max(pair['subspace_residuals']):.3e} "
                f"qr={'accepted' if accepted_qr else 'bounded_fail'}",
                flush=True,
            )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(ATTEMPTS_CSV, ATTEMPT_FIELDS, attempts)
    _write_csv(DIAGNOSTICS_CSV, DIAGNOSTIC_FIELDS, diagnostics)
    _write_csv(MANIFOLD_CSV, MANIFOLD_FIELDS, manifolds)
    np.savez_compressed(RESULTS_NPZ, **arrays)
    schur_manifolds = [
        row for row in manifolds if row["method"] == METHODS[0]
    ]
    qr_cases = {
        row["case_id"]
        for row in attempts
        if row["method"] == METHODS[1] and row["h3_status"] != "accepted"
    }
    accepted_cases = {
        row["case_id"]
        for row in schur_manifolds
        if row["status"] == "accepted"
    }
    no_one_dimensional = all(
        int(row["bundle_dimension"]) == 2 for row in attempts
    ) and all(int(row["bundle_dimension"]) == 2 for row in manifolds)
    gate = bool(
        len(accepted_cases) == len(CASES)
        and all(row["status"] == "accepted" for row in schur_manifolds)
        and no_one_dimensional
    )
    elapsed = time.perf_counter() - campaign_started
    summary = {
        "schema_version": "submission_candidate_route_h_2d_summary_v1",
        "run_id": run_id,
        "status": "complete",
        "cases": len(CASES),
        "method_attempt_rows": len(attempts),
        "diagnostic_rows": len(diagnostics),
        "manifold_rows": len(manifolds),
        "manifold_status_counts": dict(
            Counter(str(row["status"]) for row in manifolds)
        ),
        "accepted_schur_manifold_rows": sum(
            row["status"] == "accepted" for row in schur_manifolds
        ),
        "cases_with_accepted_2d_schur_object": len(accepted_cases),
        "qr_bounded_failure_cases": len(qr_cases),
        "never_one_dimensional": no_one_dimensional,
        "stage_e_schur_failures_preserved": all(
            row["stage_e_research_status"] == "fail"
            for row in attempts
            if row["method"] == METHODS[0]
        ),
        "h3_gate_status": "pass" if gate else "fail",
        "elapsed_seconds": elapsed,
        "max_wall_seconds": max_wall_seconds,
        "h1_registry_sha256": h1_hash,
        "stage_c_registry_sha256": stage_c_hash,
        "stage_e_npz_sha256": stage_e_npz_hash,
        "independent_csv_sha256": independent_hash,
        "source_git_commit": commit,
    }
    SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_checkpoint({**summary, "completed_cases": completed_cases})
    _write_environment(commit, run_id)
    _write_audit(attempts, manifolds, summary)
    _write_failure_evidence(attempts, manifolds)
    _write_artifact_hashes()
    print(
        "STAGE-H3 ROUTE-H 2D MANIFOLD WRITE PASS "
        f"cases={len(CASES)} rows={len(manifolds)} "
        f"gate={summary['h3_gate_status']} elapsed={elapsed:.3f}s",
        flush=True,
    )


def check_outputs() -> None:
    preregistration.check_outputs()
    attempts = _read_csv(ATTEMPTS_CSV)
    diagnostics = _read_csv(DIAGNOSTICS_CSV)
    manifolds = _read_csv(MANIFOLD_CSV)
    if len(attempts) != len(CASES) * 4:
        raise RuntimeError("H3 method-attempt row count drifted")
    if len(diagnostics) != len(CASES) * 45:
        raise RuntimeError("H3 phase-diagnostic row count drifted")
    if len(manifolds) != len(CASES) * len(METHODS) * len(PERTURBATIONS):
        raise RuntimeError("H3 manifold grid drifted")
    if {row["case_id"] for row in attempts} != set(CASES):
        raise RuntimeError("H3 attempt case coverage drifted")
    if {row["method"] for row in attempts} != set(METHODS):
        raise RuntimeError("H3 method coverage drifted")
    if any(int(row["bundle_dimension"]) != 2 for row in attempts + manifolds):
        raise RuntimeError("H3 introduced a forbidden one-dimensional result")

    schur = [row for row in attempts if row["method"] == METHODS[0]]
    qr = [row for row in attempts if row["method"] == METHODS[1]]
    if len(schur) != 2 or any(row["h3_status"] != "accepted" for row in schur):
        raise RuntimeError("H3 latent Schur pair no longer passes")
    if any(row["stage_e_research_status"] != "fail" for row in schur):
        raise RuntimeError("H3 no longer preserves frozen Stage-E Schur failures")
    if any(float(row["raw_equation_residual_max"]) > INVARIANCE_LIMIT for row in schur):
        raise RuntimeError("H3 raw eigenfield equation residual regressed")
    if any(
        float(row["gauge_consistent_subspace_residual_max"]) > INVARIANCE_LIMIT
        for row in schur
    ):
        raise RuntimeError("H3 gauge-consistent subspace residual regressed")
    if len(qr) != 6:
        raise RuntimeError("H3 must preserve initial plus two QR retries per case")
    if any(row["h3_status"] != "bounded_fail" for row in qr):
        raise RuntimeError("stored H3 QR outcome unexpectedly changed")
    if {row["initialization"] for row in qr} != {
        "local_svd",
        "schur_seed",
        "deterministic_random",
    }:
        raise RuntimeError("H3 QR retry initialization grid drifted")
    if any(int(row["iterations_executed"]) != 500 for row in qr):
        raise RuntimeError("H3 QR attempts did not reach the frozen cap")

    accepted = [row for row in manifolds if row["status"] == "accepted"]
    bounded = [row for row in manifolds if row["status"] == "bounded_fail"]
    if len(accepted) != 4 or len(bounded) != 4:
        raise RuntimeError("H3 accepted/bounded manifold split drifted")
    if any(row["method"] != METHODS[0] for row in accepted):
        raise RuntimeError("H3 accepted rows are not the Schur sheets")
    for row in accepted:
        if row["manifold_generated"] != "true":
            raise RuntimeError("accepted H3 sheet is missing its manifold")
        if int(row["initial_sheet_rank_min"]) != 2:
            raise RuntimeError("accepted H3 sheet lost rank")
        if float(row["manifold_jacobi_drift"]) > JACOBI_LIMIT:
            raise RuntimeError("accepted H3 sheet violates Jacobi gate")
        if (
            abs(float(row["initial_linear_growth_ratio_mean"]) - 1.0)
            > INITIAL_LINEAR_RATIO_TOLERANCE
        ):
            raise RuntimeError("accepted H3 sheet violates linearity gate")
        if float(row["final_growth_factor_geometric_mean"]) <= 1.0:
            raise RuntimeError("accepted H3 sheet is not forward unstable")
    if any(row["manifold_generated"] != "false" for row in bounded):
        raise RuntimeError("H3 generated a sheet from a failed QR frame")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["h3_gate_status"] != "pass":
        raise RuntimeError("stored H3 gate is not passing")
    if summary["cases_with_accepted_2d_schur_object"] != 2:
        raise RuntimeError("H3 accepted case count drifted")
    if summary["qr_bounded_failure_cases"] != 2:
        raise RuntimeError("H3 QR bounded-failure count drifted")
    if not summary["never_one_dimensional"]:
        raise RuntimeError("H3 one-dimensional prohibition drifted")

    with np.load(RESULTS_NPZ, allow_pickle=False) as archive:
        for case_id in CASES:
            prefix = _sanitize(case_id)
            if archive[prefix + "__orthonormal_bases"].shape != (45, 6, 2):
                raise RuntimeError("H3 basis archive shape drifted")
            if archive[prefix + "__raw_frames"].shape != (45, 6, 2):
                raise RuntimeError("H3 raw-frame archive shape drifted")
            if archive[prefix + "__base_states"].shape != (41, 45, 6):
                raise RuntimeError("H3 base-state archive shape drifted")
            for epsilon in PERTURBATIONS:
                key = (
                    f"{_key(case_id, METHODS[0])}__eps_{epsilon:.0e}"
                ).replace("-", "m").replace("+", "p")
                if archive[key + "__manifold_states"].shape != (
                    41,
                    45,
                    ANGULAR_SAMPLES,
                    6,
                ):
                    raise RuntimeError("H3 manifold archive shape drifted")

    hash_rows = _read_csv(ARTIFACT_HASHES)
    if len(hash_rows) != 9:
        raise RuntimeError("H3 artifact-hash manifest row count drifted")
    for row in hash_rows:
        path = ROOT / row["artifact"]
        if not fingerprint_matches(
            path,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(f"H3 artifact fingerprint mismatch: {path}")
    audit = AUDIT.read_text(encoding="utf-8")
    for marker in (
        "Stage-E method_comparison.csv remains unchanged",
        "does not relabel the object",
        "does not change the frozen Chapter 4 holdout",
    ):
        if marker not in audit:
            raise RuntimeError(f"H3 audit boundary marker missing: {marker}")
    print(
        "STAGE-H3 ROUTE-H 2D MANIFOLD CHECK PASS "
        f"cases={len(CASES)} rows={len(manifolds)} gate=pass",
        flush=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-wall-seconds", type=float, default=3600.0)
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
