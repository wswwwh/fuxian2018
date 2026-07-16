"""Run the bounded Stage-D/E real invariant-bundle benchmark campaign."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import tracemalloc
from typing import Any, Iterable, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.invariant_bundles import (  # noqa: E402
    InvariantBundleResult,
    assemble_discrete_cocycle_operator,
    cross_resolution_principal_angles_deg,
    periodic_interpolation_matrix,
    qr_svd_cocycle_bundle_iteration,
    real_schur_bundle_tracking,
    traditional_pointwise_eigen_bundle,
)
from qp_orbits.quasi_torus import _stroboscopic_map_and_stms  # noqa: E402


RESEARCH = ROOT / "research" / "invariant_bundles"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
CONFIG_CASES = RESEARCH / "configs" / "benchmark_cases.yaml"
CONFIG_METHODS = RESEARCH / "configs" / "method_options.yaml"
RESULTS = RESEARCH / "results"
CSV_DIR = RESULTS / "csv"
NPZ_DIR = RESULTS / "npz"
COCYCLE_DIR = NPZ_DIR / "cocycles"
LOG_DIR = RESULTS / "logs"

METHOD_COMPARISON = CSV_DIR / "method_comparison.csv"
RESOLUTION_CONVERGENCE = CSV_DIR / "resolution_convergence.csv"
PHASE_CONTINUITY = CSV_DIR / "phase_continuity.csv"
MANIFOLD_CONVERGENCE = CSV_DIR / "manifold_convergence.csv"
RUNTIME_SCALING = CSV_DIR / "runtime_scaling.csv"
METHOD_NPZ = NPZ_DIR / "method_comparison.npz"
RESOLUTION_NPZ = NPZ_DIR / "resolution_convergence.npz"
PHASE_NPZ = NPZ_DIR / "phase_continuity.npz"
MANIFOLD_NPZ = NPZ_DIR / "manifold_convergence.npz"
RUNTIME_NPZ = NPZ_DIR / "runtime_scaling.npz"
CHECKPOINT = LOG_DIR / "benchmark_campaign_checkpoint.json"
RUN_SUMMARY = LOG_DIR / "benchmark_campaign_summary.json"

SCHEMA_VERSION = "invariant_bundle_method_comparison_v1"
MAX_CASES = 15
MAX_SPECTRAL_SAMPLES = 57
MAX_ITERATIONS = 200
MAX_WALL_SECONDS = 1800.0
PASS_INVARIANCE = 1.0e-6
BOUNDARY_INVARIANCE = 1.0e-3
PASS_SELECTION = 1.0e-8
REAL_RELATIVE_IMAGINARY = 1.0e-10
QR_ANGLE_TOLERANCE_DEG = 2.0e-6

METHODS = (
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
)
RESOLUTION_GROUPS = {
    "halo_12p40": (
        "em_halo_12p40_n21",
        "em_halo_12p40_n33",
        "em_halo_12p40_n45",
    ),
    "vertical_12p66": (
        "em_vertical_12p66_n33",
        "em_vertical_12p66_n45",
        "em_vertical_12p66_n57",
    ),
}

METHOD_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "family",
    "member_id",
    "system",
    "method",
    "spectral_samples",
    "bundle_dimension",
    "classification",
    "max_invariance_residual",
    "mean_invariance_residual",
    "selection_residual",
    "reciprocal_pair_error",
    "relative_imaginary_part",
    "phase_principal_angle_max_deg",
    "phase_principal_angle_mean_deg",
    "cross_resolution_principal_angle_max_deg",
    "bundle_multiplier_estimate",
    "lyapunov_estimate_per_day",
    "sign_or_subspace_flips",
    "iterations",
    "converged",
    "source_map_residual_recomputed",
    "source_map_status",
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio",
    "normalized_3d_manifold_distance",
    "manifold_status",
    "runtime_seconds",
    "peak_memory_mb_estimate",
    "research_status",
    "failure_reason",
    "registry_sha256",
    "cocycle_cache_sha256",
    "source_git_commit",
)

PHASE_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "method",
    "spectral_samples",
    "bundle_dimension",
    "phase_index",
    "phase_rad",
    "invariance_residual",
    "principal_angle_to_next_deg",
    "local_volume_multiplier",
    "registry_sha256",
    "source_git_commit",
)

RESOLUTION_FIELDS = (
    "schema_version",
    "run_id",
    "resolution_group",
    "method",
    "case_id",
    "spectral_samples",
    "reference_case_id",
    "reference_spectral_samples",
    "bundle_dimension",
    "principal_angle_mean_deg",
    "principal_angle_max_deg",
    "status",
    "failure_reason",
    "registry_sha256",
    "source_git_commit",
)

RUNTIME_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "family",
    "method",
    "spectral_samples",
    "dg_dimension",
    "runtime_seconds",
    "peak_memory_mb_estimate",
    "iterations",
    "research_status",
    "registry_sha256",
    "source_git_commit",
)

MANIFOLD_FIELDS = (
    "schema_version",
    "run_id",
    "case_id",
    "method",
    "spectral_samples",
    "bundle_dimension",
    "manifold_jacobi_drift",
    "initial_linear_growth_ratio",
    "normalized_3d_manifold_distance",
    "branch_sign_consistent",
    "status",
    "failure_reason",
    "registry_sha256",
    "source_git_commit",
)


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return f"{number:.16g}" if np.isfinite(number) else str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_csv(
    path: Path,
    fields: tuple[str, ...],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field, "")) for field in fields})


def _git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _run_id() -> str:
    digest = hashlib.sha256()
    for path in (
        REGISTRY,
        CONFIG_CASES,
        CONFIG_METHODS,
        ROOT / "src" / "qp_orbits" / "invariant_bundles.py",
        Path(__file__),
    ):
        digest.update(path.read_bytes())
    return digest.hexdigest().upper()[:20]


def _sanitize(value: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in value)


def _load_states(row: Mapping[str, str]) -> tuple[np.ndarray, np.ndarray]:
    artifact = ROOT / row["state_artifact"]
    if _sha256(artifact) != row["state_artifact_sha256"]:
        raise RuntimeError(f"state artifact hash drifted for {row['case_id']}")
    with np.load(artifact, allow_pickle=False) as archive:
        states = np.asarray(archive[row["state_key"]], dtype=float)
        inferred_phase_key = row["state_key"].replace("_states", "_phases")
        phases = (
            np.asarray(archive[inferred_phase_key], dtype=float)
            if inferred_phase_key != row["state_key"]
            and inferred_phase_key in archive.files
            else np.linspace(0.0, 2.0 * np.pi, states.shape[0], endpoint=False)
        )
    expected = int(row["spectral_samples"])
    if states.shape != (expected, 6) or phases.shape != (expected,):
        raise RuntimeError(f"state/phase shape drifted for {row['case_id']}")
    if expected > MAX_SPECTRAL_SAMPLES:
        raise RuntimeError(f"case {row['case_id']} exceeds the frozen resolution cap")
    return states, phases


def _cocycle_cache_key(
    row: Mapping[str, str],
    *,
    max_step: float,
) -> str:
    payload = json.dumps(
        {
            "schema": "invariant_bundle_cocycle_cache_v1",
            "case_id": row["case_id"],
            "state_sha256": row["state_artifact_sha256"],
            "state_key": row["state_key"],
            "mapping_time_days": row["mapping_time"],
            "rho": row["rho"],
            "mu": row["mu"],
            "max_step": max_step,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()[:20]


def _load_or_compute_cocycle(
    row: Mapping[str, str],
    *,
    refresh: bool,
) -> tuple[np.ndarray, np.ndarray, float, Path, bool]:
    states, phases = _load_states(row)
    system = SYSTEMS[row["system"]]
    mapping_time = float(row["mapping_time"]) / system.time_unit_days
    rho = float(row["rho"])
    max_step = 0.005 if row["system"] == "sun_earth" else 0.01
    key = _cocycle_cache_key(row, max_step=max_step)
    path = COCYCLE_DIR / f"{row['case_id']}_{key}.npz"
    if path.is_file() and not refresh:
        with np.load(path, allow_pickle=False) as archive:
            if str(archive["cache_key"][0]) != key:
                raise RuntimeError(f"cocycle cache key drifted for {row['case_id']}")
            stms = np.asarray(archive["stms"], dtype=float)
            stored_phases = np.asarray(archive["phases"], dtype=float)
            source_map_residual = float(archive["source_map_residual"][0])
        if stms.shape != (states.shape[0], 6, 6):
            raise RuntimeError(f"cocycle cache shape drifted for {row['case_id']}")
        np.testing.assert_allclose(stored_phases, phases, rtol=0.0, atol=0.0)
        return stms, phases, source_map_residual, path, True

    mapped, stms = _stroboscopic_map_and_stms(
        states,
        period=mapping_time,
        mu=system.mu,
        max_step=max_step,
    )
    target = periodic_interpolation_matrix(phases, phases + rho) @ states
    source_map_residual = float(np.max(np.linalg.norm(mapped - target, axis=1)))
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        schema_version=np.asarray(["invariant_bundle_cocycle_cache_v1"]),
        cache_key=np.asarray([key]),
        case_id=np.asarray([row["case_id"]]),
        phases=phases,
        states=states,
        mapped_states=mapped,
        stms=stms,
        mapping_time_nd=np.asarray([mapping_time]),
        mapping_time_days=np.asarray([float(row["mapping_time"])]),
        rho=np.asarray([rho]),
        mu=np.asarray([system.mu]),
        max_step=np.asarray([max_step]),
        source_map_residual=np.asarray([source_map_residual]),
        registry_sha256=np.asarray([_sha256(REGISTRY)]),
    )
    return stms, phases, source_map_residual, path, False


def _source_map_status(row: Mapping[str, str], residual: float) -> str:
    limit = max(5.0e-9, 20.0 * float(row["source_residual"]))
    return "pass" if residual <= limit else "fail"


def _reciprocal_pair_error(
    selected: np.ndarray,
    operator_spectrum: np.ndarray,
) -> float:
    values = np.asarray(selected, dtype=complex)
    if values.size == 0:
        return float("nan")
    errors = [float(np.min(np.abs(value * operator_spectrum - 1.0))) for value in values]
    return max(errors)


def _bundle_multiplier(result: InvariantBundleResult) -> float:
    determinants = np.abs(np.linalg.det(result.local_reduced_maps))
    determinants = np.maximum(determinants, np.finfo(float).tiny)
    return float(
        np.exp(np.mean(np.log(determinants)) / result.bundle_dimension)
    )


def _research_status(
    result: InvariantBundleResult,
    *,
    source_status: str,
) -> tuple[str, str]:
    reasons: list[str] = []
    if source_status != "pass":
        reasons.append("source_map_revalidation_failed")
    if result.classification == "complex_vector_projected_to_real_1d_failure":
        reasons.append("complex_vector_projected_to_real_1d")
    if result.method == "ordered_real_schur_tracking" and result.selection_residual > PASS_SELECTION:
        reasons.append("partial_schur_residual_gt_1e-8")
    if result.method == "qr_svd_shifted_cocycle_iteration" and not result.converged:
        reasons.append("qr_iteration_not_converged_at_cap")
    if result.max_invariance_residual > PASS_INVARIANCE:
        reasons.append("max_invariance_residual_gt_1e-6")
    if source_status == "pass" and not reasons:
        return "accepted", ""
    if (
        source_status == "pass"
        and result.classification != "complex_vector_projected_to_real_1d_failure"
        and result.max_invariance_residual <= BOUNDARY_INVARIANCE
    ):
        return "boundary", ";".join(reasons)
    return "fail", ";".join(reasons)


def _method_runner(
    method: str,
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    schur_dimension: int | None,
) -> InvariantBundleResult:
    if method == METHODS[0]:
        return traditional_pointwise_eigen_bundle(cocycle, phases, rho)
    if method == METHODS[1]:
        return real_schur_bundle_tracking(
            cocycle,
            phases,
            rho,
            real_relative_imaginary_tolerance=REAL_RELATIVE_IMAGINARY,
        )
    if method == METHODS[2]:
        return qr_svd_cocycle_bundle_iteration(
            cocycle,
            phases,
            rho,
            bundle_dimension=schur_dimension,
            max_iterations=MAX_ITERATIONS,
            angle_tolerance_deg=QR_ANGLE_TOLERANCE_DEG,
            real_relative_imaginary_tolerance=REAL_RELATIVE_IMAGINARY,
        )
    raise ValueError(f"unknown method: {method}")


def _empty_failure_row(
    row: Mapping[str, str],
    *,
    method: str,
    run_id: str,
    commit: str,
    registry_hash: str,
    cache_hash: str,
    source_map_residual: float,
    source_status: str,
    runtime: float,
    peak_memory_mb: float,
    error: Exception,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "case_id": row["case_id"],
        "family": row["family"],
        "member_id": row["member_id"],
        "system": row["system"],
        "method": method,
        "spectral_samples": int(row["spectral_samples"]),
        "bundle_dimension": 0,
        "classification": "method_exception",
        "max_invariance_residual": float("nan"),
        "mean_invariance_residual": float("nan"),
        "selection_residual": float("nan"),
        "reciprocal_pair_error": float("nan"),
        "relative_imaginary_part": float("nan"),
        "phase_principal_angle_max_deg": float("nan"),
        "phase_principal_angle_mean_deg": float("nan"),
        "cross_resolution_principal_angle_max_deg": float("nan"),
        "bundle_multiplier_estimate": float("nan"),
        "lyapunov_estimate_per_day": float("nan"),
        "sign_or_subspace_flips": 0,
        "iterations": 0,
        "converged": False,
        "source_map_residual_recomputed": source_map_residual,
        "source_map_status": source_status,
        "manifold_jacobi_drift": float("nan"),
        "initial_linear_growth_ratio": float("nan"),
        "normalized_3d_manifold_distance": float("nan"),
        "manifold_status": "not_run_stage_f",
        "runtime_seconds": runtime,
        "peak_memory_mb_estimate": peak_memory_mb,
        "research_status": "fail",
        "failure_reason": f"{type(error).__name__}: {error}",
        "registry_sha256": registry_hash,
        "cocycle_cache_sha256": cache_hash,
        "source_git_commit": commit,
    }


def _write_checkpoint(payload: Mapping[str, Any]) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_campaign(*, refresh_cocycle: bool, max_wall_seconds: float) -> None:
    if max_wall_seconds <= 0.0 or max_wall_seconds > MAX_WALL_SECONDS:
        raise ValueError(f"max-wall-seconds must be in (0, {MAX_WALL_SECONDS}]")
    rows = _read_csv(REGISTRY)
    if len(rows) != MAX_CASES:
        raise RuntimeError(f"registry must contain exactly {MAX_CASES} frozen cases")
    registry_hash = _sha256(REGISTRY)
    commit = _git_commit()
    run_id = _run_id()
    campaign_started = time.perf_counter()
    method_rows: list[dict[str, Any]] = []
    phase_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    method_results: dict[tuple[str, str], InvariantBundleResult] = {}
    phases_by_case: dict[str, np.ndarray] = {}
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "run_id": np.asarray([run_id]),
        "registry_sha256": np.asarray([registry_hash]),
        "source_git_commit": np.asarray([commit]),
    }
    completed_cases: list[str] = []
    cache_hits = 0
    for case_index, row in enumerate(rows, start=1):
        elapsed = time.perf_counter() - campaign_started
        if elapsed > max_wall_seconds:
            _write_checkpoint(
                {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "status": "wall_time_cap_reached",
                    "completed_cases": completed_cases,
                    "elapsed_seconds": elapsed,
                }
            )
            raise RuntimeError("benchmark campaign reached the frozen wall-time cap")
        cocycle, phases, source_map_residual, cache_path, cache_hit = (
            _load_or_compute_cocycle(row, refresh=refresh_cocycle)
        )
        cache_hits += int(cache_hit)
        phases_by_case[row["case_id"]] = phases
        cache_hash = _sha256(cache_path)
        source_status = _source_map_status(row, source_map_residual)
        operator_spectrum = np.linalg.eigvals(
            assemble_discrete_cocycle_operator(cocycle, phases, float(row["rho"]))
        )
        schur_dimension: int | None = None
        print(
            f"case {case_index}/{len(rows)} {row['case_id']} "
            f"N={row['spectral_samples']} source={source_status} cache={'hit' if cache_hit else 'write'}",
            flush=True,
        )
        for method in METHODS:
            started = time.perf_counter()
            tracemalloc.start()
            try:
                result = _method_runner(
                    method,
                    cocycle,
                    phases,
                    float(row["rho"]),
                    schur_dimension=schur_dimension,
                )
                _, peak = tracemalloc.get_traced_memory()
                runtime = time.perf_counter() - started
                tracemalloc.stop()
                estimated_bytes = (
                    result.bases.nbytes
                    + result.local_reduced_maps.nbytes
                    + result.invariance_residuals.nbytes
                    + result.phase_principal_angles_deg.nbytes
                )
                peak_memory_mb = max(peak, estimated_bytes) / (1024.0**2)
                if method == METHODS[1]:
                    schur_dimension = result.bundle_dimension
                multiplier = _bundle_multiplier(result)
                reciprocal = _reciprocal_pair_error(
                    result.selected_spectrum, operator_spectrum
                )
                research_status, failure_reason = _research_status(
                    result, source_status=source_status
                )
                output_method = (
                    "ordered_partial_real_schur_tracking"
                    if result.method == "ordered_real_schur_tracking"
                    else result.method
                )
                output_row = {
                    "schema_version": SCHEMA_VERSION,
                    "run_id": run_id,
                    "case_id": row["case_id"],
                    "family": row["family"],
                    "member_id": row["member_id"],
                    "system": row["system"],
                    "method": output_method,
                    "spectral_samples": int(row["spectral_samples"]),
                    "bundle_dimension": result.bundle_dimension,
                    "classification": result.classification,
                    "max_invariance_residual": result.max_invariance_residual,
                    "mean_invariance_residual": result.mean_invariance_residual,
                    "selection_residual": result.selection_residual,
                    "reciprocal_pair_error": reciprocal,
                    "relative_imaginary_part": result.relative_imaginary,
                    "phase_principal_angle_max_deg": result.max_phase_principal_angle_deg,
                    "phase_principal_angle_mean_deg": result.mean_phase_principal_angle_deg,
                    "cross_resolution_principal_angle_max_deg": float("nan"),
                    "bundle_multiplier_estimate": multiplier,
                    "lyapunov_estimate_per_day": math.log(multiplier)
                    / float(row["mapping_time"]),
                    "sign_or_subspace_flips": result.sign_or_orientation_flips,
                    "iterations": result.iterations,
                    "converged": result.converged,
                    "source_map_residual_recomputed": source_map_residual,
                    "source_map_status": source_status,
                    "manifold_jacobi_drift": float("nan"),
                    "initial_linear_growth_ratio": float("nan"),
                    "normalized_3d_manifold_distance": float("nan"),
                    "manifold_status": "not_run_stage_f",
                    "runtime_seconds": runtime,
                    "peak_memory_mb_estimate": peak_memory_mb,
                    "research_status": research_status,
                    "failure_reason": failure_reason,
                    "registry_sha256": registry_hash,
                    "cocycle_cache_sha256": cache_hash,
                    "source_git_commit": commit,
                }
                method_rows.append(output_row)
                method_results[(row["case_id"], output_method)] = result
                prefix = f"{_sanitize(row['case_id'])}__{_sanitize(output_method)}"
                arrays[prefix + "__bases"] = result.bases
                arrays[prefix + "__local_reduced_maps"] = result.local_reduced_maps
                arrays[prefix + "__invariance_residuals"] = result.invariance_residuals
                arrays[prefix + "__phase_principal_angles_deg"] = result.phase_principal_angles_deg
                arrays[prefix + "__selected_spectrum"] = result.selected_spectrum
                arrays[prefix + "__convergence_history"] = result.convergence_history
                local_determinants = np.abs(np.linalg.det(result.local_reduced_maps))
                local_multiplier = np.maximum(
                    local_determinants, np.finfo(float).tiny
                ) ** (1.0 / result.bundle_dimension)
                for phase_index, phase in enumerate(phases):
                    phase_rows.append(
                        {
                            "schema_version": SCHEMA_VERSION,
                            "run_id": run_id,
                            "case_id": row["case_id"],
                            "method": output_method,
                            "spectral_samples": int(row["spectral_samples"]),
                            "bundle_dimension": result.bundle_dimension,
                            "phase_index": phase_index,
                            "phase_rad": phase,
                            "invariance_residual": result.invariance_residuals[phase_index],
                            "principal_angle_to_next_deg": result.phase_principal_angles_deg[phase_index],
                            "local_volume_multiplier": local_multiplier[phase_index],
                            "registry_sha256": registry_hash,
                            "source_git_commit": commit,
                        }
                    )
                print(
                    f"  {output_method}: {research_status} dim={result.bundle_dimension} "
                    f"max_res={result.max_invariance_residual:.3e} time={runtime:.3f}s",
                    flush=True,
                )
            except Exception as error:
                _, peak = tracemalloc.get_traced_memory()
                runtime = time.perf_counter() - started
                tracemalloc.stop()
                method_rows.append(
                    _empty_failure_row(
                        row,
                        method=method,
                        run_id=run_id,
                        commit=commit,
                        registry_hash=registry_hash,
                        cache_hash=cache_hash,
                        source_map_residual=source_map_residual,
                        source_status=source_status,
                        runtime=runtime,
                        peak_memory_mb=peak / (1024.0**2),
                        error=error,
                    )
                )
                print(f"  {method}: fail {type(error).__name__}: {error}", flush=True)
        completed_cases.append(row["case_id"])
        _write_checkpoint(
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "status": "running",
                "completed_cases": completed_cases,
                "total_cases": len(rows),
                "elapsed_seconds": time.perf_counter() - campaign_started,
                "cache_hits": cache_hits,
                "max_wall_seconds": max_wall_seconds,
                "max_iterations": MAX_ITERATIONS,
            }
        )

    resolution_rows: list[dict[str, Any]] = []
    resolution_arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray(["invariant_bundle_resolution_convergence_v1"]),
        "run_id": np.asarray([run_id]),
        "registry_sha256": np.asarray([registry_hash]),
    }
    method_row_index = {
        (row["case_id"], row["method"]): row for row in method_rows
    }
    for group, cases in RESOLUTION_GROUPS.items():
        reference_case = cases[-1]
        reference_samples = int(
            next(row["spectral_samples"] for row in rows if row["case_id"] == reference_case)
        )
        for method in METHODS:
            output_method = (
                "ordered_partial_real_schur_tracking" if method == METHODS[1] else method
            )
            reference = method_results.get((reference_case, output_method))
            for case_id in cases:
                samples = int(
                    next(row["spectral_samples"] for row in rows if row["case_id"] == case_id)
                )
                result = method_results.get((case_id, output_method))
                failure_reason = ""
                status = "accepted"
                angles = np.asarray([], dtype=float)
                dimension = 0
                if result is None or reference is None:
                    status = "fail"
                    failure_reason = "method_result_missing"
                elif result.bundle_dimension != reference.bundle_dimension:
                    status = "fail"
                    failure_reason = "bundle_dimension_mismatch"
                    dimension = result.bundle_dimension
                else:
                    dimension = result.bundle_dimension
                    angles = cross_resolution_principal_angles_deg(
                        phases_by_case[case_id],
                        result.bases,
                        phases_by_case[reference_case],
                        reference.bases,
                    )
                    if float(np.max(angles)) > 5.0:
                        status = "boundary"
                        failure_reason = "cross_resolution_principal_angle_gt_5deg"
                    key = f"{_sanitize(group)}__{_sanitize(output_method)}__{_sanitize(case_id)}"
                    resolution_arrays[key + "__angles_deg"] = angles
                    method_row_index[(case_id, output_method)][
                        "cross_resolution_principal_angle_max_deg"
                    ] = float(np.max(angles))
                resolution_rows.append(
                    {
                        "schema_version": "invariant_bundle_resolution_convergence_v1",
                        "run_id": run_id,
                        "resolution_group": group,
                        "method": output_method,
                        "case_id": case_id,
                        "spectral_samples": samples,
                        "reference_case_id": reference_case,
                        "reference_spectral_samples": reference_samples,
                        "bundle_dimension": dimension,
                        "principal_angle_mean_deg": float(np.mean(angles)) if angles.size else float("nan"),
                        "principal_angle_max_deg": float(np.max(angles)) if angles.size else float("nan"),
                        "status": status,
                        "failure_reason": failure_reason,
                        "registry_sha256": registry_hash,
                        "source_git_commit": commit,
                    }
                )

    for method_row in method_rows:
        runtime_rows.append(
            {
                "schema_version": "invariant_bundle_runtime_scaling_v1",
                "run_id": run_id,
                "case_id": method_row["case_id"],
                "family": method_row["family"],
                "method": method_row["method"],
                "spectral_samples": method_row["spectral_samples"],
                "dg_dimension": 6 * int(method_row["spectral_samples"]),
                "runtime_seconds": method_row["runtime_seconds"],
                "peak_memory_mb_estimate": method_row["peak_memory_mb_estimate"],
                "iterations": method_row["iterations"],
                "research_status": method_row["research_status"],
                "registry_sha256": registry_hash,
                "source_git_commit": commit,
            }
        )
    manifold_rows = [
        {
            "schema_version": "invariant_bundle_manifold_convergence_v1",
            "run_id": run_id,
            "case_id": row["case_id"],
            "method": row["method"],
            "spectral_samples": row["spectral_samples"],
            "bundle_dimension": row["bundle_dimension"],
            "manifold_jacobi_drift": float("nan"),
            "initial_linear_growth_ratio": float("nan"),
            "normalized_3d_manifold_distance": float("nan"),
            "branch_sign_consistent": "not_run",
            "status": "not_run_stage_f",
            "failure_reason": "Stage F is intentionally separate from Stage D/E bundle construction.",
            "registry_sha256": registry_hash,
            "source_git_commit": commit,
        }
        for row in method_rows
    ]

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    NPZ_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(METHOD_COMPARISON, METHOD_FIELDS, method_rows)
    _write_csv(PHASE_CONTINUITY, PHASE_FIELDS, phase_rows)
    _write_csv(RESOLUTION_CONVERGENCE, RESOLUTION_FIELDS, resolution_rows)
    _write_csv(RUNTIME_SCALING, RUNTIME_FIELDS, runtime_rows)
    _write_csv(MANIFOLD_CONVERGENCE, MANIFOLD_FIELDS, manifold_rows)
    np.savez_compressed(METHOD_NPZ, **arrays)
    np.savez_compressed(PHASE_NPZ, **{
        key: value
        for key, value in arrays.items()
        if key.endswith("__invariance_residuals")
        or key.endswith("__phase_principal_angles_deg")
        or key in {"schema_version", "run_id", "registry_sha256", "source_git_commit"}
    })
    np.savez_compressed(RESOLUTION_NPZ, **resolution_arrays)
    np.savez_compressed(
        RUNTIME_NPZ,
        schema_version=np.asarray(["invariant_bundle_runtime_scaling_v1"]),
        run_id=np.asarray([run_id]),
        runtime_seconds=np.asarray([float(row["runtime_seconds"]) for row in runtime_rows]),
        peak_memory_mb_estimate=np.asarray(
            [float(row["peak_memory_mb_estimate"]) for row in runtime_rows]
        ),
        spectral_samples=np.asarray([int(row["spectral_samples"]) for row in runtime_rows]),
        method=np.asarray([row["method"] for row in runtime_rows]),
        case_id=np.asarray([row["case_id"] for row in runtime_rows]),
        registry_sha256=np.asarray([registry_hash]),
    )
    np.savez_compressed(
        MANIFOLD_NPZ,
        schema_version=np.asarray(["invariant_bundle_manifold_convergence_v1"]),
        run_id=np.asarray([run_id]),
        case_id=np.asarray([row["case_id"] for row in manifold_rows]),
        method=np.asarray([row["method"] for row in manifold_rows]),
        status=np.asarray([row["status"] for row in manifold_rows]),
        registry_sha256=np.asarray([registry_hash]),
    )
    elapsed = time.perf_counter() - campaign_started
    counts: dict[str, int] = {}
    for row in method_rows:
        counts[row["research_status"]] = counts.get(row["research_status"], 0) + 1
    summary = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "complete_stage_d_e_bundle_only",
        "cases": len(rows),
        "methods": len(METHODS),
        "method_rows": len(method_rows),
        "research_status_counts": counts,
        "cache_hits": cache_hits,
        "elapsed_seconds": elapsed,
        "max_wall_seconds": max_wall_seconds,
        "max_iterations": MAX_ITERATIONS,
        "registry_sha256": registry_hash,
        "source_git_commit": commit,
        "stage_f_status": "not_run",
    }
    RUN_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_checkpoint({**summary, "completed_cases": completed_cases})
    print(
        f"invariant-bundle benchmark WRITE PASS cases={len(rows)} rows={len(method_rows)} "
        f"statuses={counts} elapsed={elapsed:.3f}s stage_f=not_run",
        flush=True,
    )


def check_outputs() -> None:
    rows = _read_csv(REGISTRY)
    registry_hash = _sha256(REGISTRY)
    expected_rows = len(rows) * len(METHODS)
    required_csvs = (
        (METHOD_COMPARISON, expected_rows),
        (PHASE_CONTINUITY, None),
        (RESOLUTION_CONVERGENCE, 18),
        (MANIFOLD_CONVERGENCE, None),
        (RUNTIME_SCALING, expected_rows),
    )
    for path, expected_count in required_csvs:
        stored = _read_csv(path)
        if expected_count is not None and len(stored) != expected_count:
            raise RuntimeError(
                f"{_rel(path)} row count {len(stored)} != {expected_count}"
            )
        if not stored or any(row["registry_sha256"] != registry_hash for row in stored):
            raise RuntimeError(f"{_rel(path)} registry hash drifted")
        if path == MANIFOLD_CONVERGENCE:
            covered = {(row["case_id"], row["method"]) for row in stored}
            expected_covered = {
                (case["case_id"], method) for case in rows for method in METHODS
            }
            if not covered.issubset(expected_covered) or len(covered) < 21:
                raise RuntimeError(
                    "manifold convergence must cover at least the seven frozen Stage-F cases"
                )
    for path in (METHOD_NPZ, PHASE_NPZ, RESOLUTION_NPZ, MANIFOLD_NPZ, RUNTIME_NPZ):
        if not path.is_file():
            raise RuntimeError(f"missing {_rel(path)}")
        with np.load(path, allow_pickle=False) as archive:
            if "registry_sha256" not in archive.files:
                raise RuntimeError(f"{_rel(path)} lacks registry hash")
            if str(archive["registry_sha256"][0]) != registry_hash:
                raise RuntimeError(f"{_rel(path)} registry hash drifted")
    comparison = _read_csv(METHOD_COMPARISON)
    if {row["case_id"] for row in comparison} != {row["case_id"] for row in rows}:
        raise RuntimeError("method comparison does not cover the frozen registry")
    if {row["method"] for row in comparison} != set(METHODS):
        raise RuntimeError("method comparison does not cover all methods")
    print(
        f"invariant-bundle benchmark CHECK PASS cases={len(rows)} rows={expected_rows}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--refresh-cocycle", action="store_true")
    parser.add_argument(
        "--max-wall-seconds", type=float, default=MAX_WALL_SECONDS
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        check_outputs()
        return 0
    run_campaign(
        refresh_cocycle=args.refresh_cocycle,
        max_wall_seconds=args.max_wall_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
