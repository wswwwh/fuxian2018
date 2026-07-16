#!/usr/bin/env python3
"""Run the bounded QR/SVD failure-classification campaign."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable

import mpmath as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.invariant_bundles import (  # noqa: E402
    _align_to_reference,
    _initial_svd_bases,
    _orthonormalize,
    _principal_angles_deg,
    align_bundle_phase,
    assemble_discrete_cocycle_operator,
    bundle_invariance_metrics,
    periodic_interpolation_matrix,
    phase_principal_angles_deg,
    resample_bundle,
)

RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "qr_svd_failure_classification.json"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
METHOD_CSV = RESEARCH / "results" / "csv" / "method_comparison.csv"
METHOD_NPZ = RESEARCH / "results" / "npz" / "method_comparison.npz"
COCYCLE_DIR = RESEARCH / "results" / "npz" / "cocycles"
INDEPENDENT_CSV = RESEARCH / "results" / "csv" / "independent_schur_backend_comparison.csv"
SUMMARY_CSV = RESEARCH / "results" / "csv" / "qr_svd_failure_classification.csv"
EXPERIMENT_CSV = RESEARCH / "results" / "csv" / "qr_svd_failure_experiments.csv"
NPZ_OUTPUT = RESEARCH / "results" / "npz" / "qr_svd_failure_experiments.npz"
DOC_OUTPUT = RESEARCH / "docs" / "qr_svd_failure_analysis.md"
LOG_OUTPUT = RESEARCH / "results" / "logs" / "qr_svd_failure_classification.log"
FAILURE_EVIDENCE = RESEARCH / "results" / "logs" / "qr_svd_failure_evidence.md"
HASH_OUTPUT = RESEARCH / "results" / "logs" / "qr_svd_failure_artifact_hashes.csv"
SCHEMA = "qr_svd_failure_classification_v1"
EXPERIMENT_SCHEMA = "qr_svd_failure_experiments_v1"
SCHUR_METHOD = "ordered_partial_real_schur_tracking"
QR_METHOD = "qr_svd_shifted_cocycle_iteration"

EXPERIMENT_FIELDS = [
    "schema_version", "run_id", "case_id", "initialization", "resolution_id",
    "resolution_kind", "spectral_samples", "iteration_cap", "iterations_executed",
    "bundle_dimension", "converged", "selection_residual_deg",
    "max_invariance_residual", "mean_invariance_residual",
    "phase_principal_angle_max_deg", "phase_principal_angle_mean_deg",
    "sign_or_subspace_flips", "tail_angle_mean_deg", "tail_angle_std_deg",
    "tail_relative_range", "research_status", "runtime_seconds",
    "source_map_status", "source_gate_status", "cocycle_sha256", "source_git_commit",
]

SUMMARY_FIELDS = [
    "schema_version", "run_id", "case_id", "member_id", "source_gate_status",
    "baseline_bundle_dimension", "independent_schur_dimension",
    "independent_schur_classification", "target_spectrum", "target_modulus",
    "relative_imaginary_part", "unstable_eigenvalue_count", "near_unit_eigenvalue_count",
    "nearest_nonselected_complex_gap_relative", "nearest_nonselected_modulus_gap_relative",
    "target_to_dominant_modulus_ratio", "branch_selection_correct",
    "initializations_tested", "iteration_caps_tested", "resolutions_tested",
    "best_native_initialization", "best_native_iteration_cap",
    "best_native_research_status", "best_native_max_invariance_residual",
    "best_native_selection_residual_deg", "native_local_svd_residual_200",
    "native_local_svd_residual_1000", "native_local_svd_plateau_ratio",
    "native_schur_seed_status", "native_random_status",
    "fourier_lift_best_status", "resolution_status_agreement",
    "phase_alignment_discontinuity_observed", "iteration_stagnation_observed",
    "initialization_sensitivity_observed", "source_state_boundary_observed",
    "high_precision_decimal_digits", "high_precision_scope",
    "high_precision_max_invariance_residual", "double_to_high_precision_residual_ratio",
    "final_label", "classification_rationale", "negative_result_retained",
    "registry_sha256", "source_git_commit",
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


def git_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        text=True, capture_output=True,
    ).stdout.strip()


def find_cocycle(case_id: str, expected_hash: str) -> Path:
    matched = [
        path for path in COCYCLE_DIR.glob(f"{case_id}_*.npz")
        if sha256(path) == expected_hash.upper()
    ]
    if len(matched) != 1:
        raise RuntimeError(f"expected one hashed cocycle for {case_id}, found {len(matched)}")
    return matched[0]


def deterministic_random_basis(case_id: str, samples: int, rank: int, phases: np.ndarray, namespace: str) -> np.ndarray:
    seed = int.from_bytes(hashlib.sha256(f"{namespace}:{case_id}:{samples}".encode()).digest()[:8], "little")
    generator = np.random.default_rng(seed)
    bases = _orthonormalize(generator.standard_normal((samples, 6, rank)))
    return align_bundle_phase(bases, phases)[0]


def research_status(converged: bool, max_residual: float, config: dict[str, Any]) -> str:
    if converged and max_residual <= float(config["pass_max_invariance_residual"]):
        return "accepted"
    if max_residual <= float(config["boundary_max_invariance_residual"]):
        return "boundary"
    return "fail"


def trajectory_snapshots(
    matrices: np.ndarray,
    phases: np.ndarray,
    rho: float,
    initial_bases: np.ndarray,
    caps: list[int],
    angle_tolerance: float,
    plateau_window: int,
) -> tuple[dict[int, dict[str, Any]], np.ndarray]:
    bases = _orthonormalize(initial_bases)
    shifted_to_base = periodic_interpolation_matrix(phases + rho, phases)
    history: list[float] = []
    flips = 0
    snapshots: dict[int, dict[str, Any]] = {}
    started = time.perf_counter()
    converged_at: int | None = None
    for iteration in range(1, max(caps) + 1):
        transported = np.einsum("nij,njk->nik", matrices, bases)
        transported = _orthonormalize(transported)
        transported, count = align_bundle_phase(transported, phases + rho)
        flips += count
        candidate = np.einsum("ij,jdk->idk", shifted_to_base, transported)
        candidate = _orthonormalize(candidate)
        candidate, count = _align_to_reference(candidate, bases)
        flips += count
        candidate, count = align_bundle_phase(candidate, phases)
        flips += count
        angle = max(
            float(np.max(_principal_angles_deg(bases[index], candidate[index])))
            for index in range(bases.shape[0])
        )
        history.append(angle)
        bases = candidate
        if angle <= angle_tolerance:
            converged_at = iteration
        if iteration in caps or converged_at is not None:
            local_maps, residuals = bundle_invariance_metrics(matrices, phases, rho, bases)
            phase_angles = phase_principal_angles_deg(bases, phases)
            tail = np.asarray(history[-plateau_window:], dtype=float)
            snapshot = {
                "basis": bases.copy(),
                "local_maps": local_maps,
                "residuals": residuals,
                "phase_angles": phase_angles,
                "iterations": iteration,
                "converged": converged_at is not None,
                "selection_residual": history[-1],
                "flips": flips,
                "tail_mean": float(np.mean(tail)),
                "tail_std": float(np.std(tail)),
                "tail_relative_range": float(np.ptp(tail) / max(abs(np.mean(tail)), np.finfo(float).tiny)),
                "runtime": time.perf_counter() - started,
            }
            if iteration in caps:
                snapshots[iteration] = snapshot
            if converged_at is not None:
                for cap in caps:
                    if cap >= iteration and cap not in snapshots:
                        snapshots[cap] = snapshot
                break
    if set(snapshots) != set(caps):
        raise RuntimeError(f"missing cap snapshots: {set(caps) - set(snapshots)}")
    return snapshots, np.asarray(history, dtype=float)


def fourier_lift_cocycle(matrices: np.ndarray, phases: np.ndarray, samples: int) -> tuple[np.ndarray, np.ndarray]:
    evaluation = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    weights = periodic_interpolation_matrix(phases, evaluation)
    lifted = np.einsum("ij,jab->iab", weights, matrices)
    return lifted, evaluation


def spectral_diagnostics(operator: np.ndarray, target: np.ndarray, hyperbolic_tolerance: float) -> dict[str, Any]:
    spectrum = np.linalg.eigvals(operator)
    selected_indices: set[int] = set()
    for value in np.asarray(target, dtype=complex).reshape(-1):
        available = [index for index in range(spectrum.size) if index not in selected_indices]
        chosen = min(available, key=lambda index: abs(spectrum[index] - value))
        selected_indices.add(chosen)
    other = np.delete(spectrum, sorted(selected_indices))
    target_values = np.asarray(target, dtype=complex).reshape(-1)
    target_modulus = float(np.mean(np.abs(target_values)))
    complex_gap = min(float(np.min(np.abs(other - value))) for value in target_values) / max(target_modulus, np.finfo(float).tiny)
    modulus_gap = float(np.min(np.abs(np.abs(other) - target_modulus))) / max(target_modulus, np.finfo(float).tiny)
    return {
        "target_modulus": target_modulus,
        "unstable_count": int(np.count_nonzero(np.abs(spectrum) > 1.0 + hyperbolic_tolerance)),
        "near_unit_count": int(np.count_nonzero(np.abs(np.abs(spectrum) - 1.0) <= 1.0e-2)),
        "complex_gap": complex_gap,
        "modulus_gap": modulus_gap,
        "target_to_dominant_ratio": target_modulus / float(np.max(np.abs(spectrum))),
        "branch_correct": bool(np.all(np.abs(target_values) > 1.0 + hyperbolic_tolerance)),
    }


def mp_orthonormalize(columns: list[list[mp.mpf]]) -> list[list[mp.mpf]]:
    rows = len(columns)
    rank = len(columns[0])
    result = [[mp.mpf("0") for _ in range(rank)] for _ in range(rows)]
    for column in range(rank):
        vector = [columns[row][column] for row in range(rows)]
        for prior in range(column):
            projection = sum(result[row][prior] * vector[row] for row in range(rows))
            vector = [vector[row] - projection * result[row][prior] for row in range(rows)]
        norm = mp.sqrt(sum(value * value for value in vector))
        if norm == 0:
            raise RuntimeError("high-precision basis lost rank")
        for row in range(rows):
            result[row][column] = vector[row] / norm
    return result


def high_precision_residual(
    matrices: np.ndarray,
    phases: np.ndarray,
    rho: float,
    bases: np.ndarray,
    digits: int,
) -> float:
    with mp.workdps(digits):
        n, state_dim, rank = bases.shape
        phase_mp = [mp.mpf(repr(float(value))) for value in phases]
        rho_mp = mp.mpf(repr(float(rho)))
        harmonic_count = (n - 1) // 2
        weights: list[list[mp.mpf]] = []
        for eval_phase in [value + rho_mp for value in phase_mp]:
            row: list[mp.mpf] = []
            for source_phase in phase_mp:
                delta = eval_phase - source_phase
                value = mp.mpf("1")
                for harmonic in range(1, harmonic_count + 1):
                    value += 2 * mp.cos(harmonic * delta)
                row.append(value / n)
            weights.append(row)
        shifted: list[list[list[mp.mpf]]] = []
        for i in range(n):
            columns = [[mp.mpf("0") for _ in range(rank)] for _ in range(state_dim)]
            for row in range(state_dim):
                for column in range(rank):
                    columns[row][column] = sum(
                        weights[i][j] * mp.mpf(repr(float(bases[j, row, column])))
                        for j in range(n)
                    )
            shifted.append(mp_orthonormalize(columns))
        maximum = mp.mpf("0")
        for i in range(n):
            transported = [[mp.mpf("0") for _ in range(rank)] for _ in range(state_dim)]
            for row in range(state_dim):
                for column in range(rank):
                    transported[row][column] = sum(
                        mp.mpf(repr(float(matrices[i, row, inner])))
                        * mp.mpf(repr(float(bases[i, inner, column])))
                        for inner in range(state_dim)
                    )
            reduced = [[mp.mpf("0") for _ in range(rank)] for _ in range(rank)]
            for left in range(rank):
                for right in range(rank):
                    reduced[left][right] = sum(
                        shifted[i][row][left] * transported[row][right]
                        for row in range(state_dim)
                    )
            defect_sq = mp.mpf("0")
            transported_sq = mp.mpf("0")
            for row in range(state_dim):
                for column in range(rank):
                    projected = sum(
                        shifted[i][row][inner] * reduced[inner][column]
                        for inner in range(rank)
                    )
                    defect_sq += (transported[row][column] - projected) ** 2
                    transported_sq += transported[row][column] ** 2
            maximum = max(maximum, mp.sqrt(defect_sq) / max(mp.sqrt(transported_sq), mp.mpf("1e-100")))
        return float(maximum)


def format_spectrum(values: np.ndarray) -> str:
    return ";".join(f"{value.real:.17g}{value.imag:+.17g}j" for value in np.asarray(values).reshape(-1))


def status_rank(status: str) -> int:
    return {"accepted": 0, "boundary": 1, "fail": 2}[status]


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    started = time.perf_counter()
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    commit = git_commit()
    registry_hash = sha256(REGISTRY)
    registry_rows = {row["case_id"]: row for row in read_csv(REGISTRY)}
    method_rows = read_csv(METHOD_CSV)
    baseline = {
        row["case_id"]: row for row in method_rows
        if row["method"] == QR_METHOD and row["case_id"] in config["failure_cases"]
    }
    schur_rows = {
        row["case_id"]: row for row in method_rows
        if row["method"] == SCHUR_METHOD and row["case_id"] in config["failure_cases"]
    }
    independent_rows = {
        row["case_id"]: row for row in read_csv(INDEPENDENT_CSV)
        if row["case_id"] in config["failure_cases"]
    }
    if set(baseline) != set(config["failure_cases"]) or any(row["research_status"] == "accepted" for row in baseline.values()):
        raise RuntimeError("the frozen QR/SVD failure set is not exactly the predeclared five cases")

    experiment_rows: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([EXPERIMENT_SCHEMA]),
        "run_id": np.asarray([run_id]),
        "registry_sha256": np.asarray([registry_hash]),
        "source_git_commit": np.asarray([commit]),
    }
    native_inputs: dict[str, tuple[np.ndarray, np.ndarray, float]] = {}
    target_spectra: dict[str, np.ndarray] = {}
    log: list[str] = [
        f"start_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"run_id={run_id}", f"config_sha256={sha256(CONFIG)}",
        f"registry_sha256={registry_hash}", f"source_git_commit={commit}",
    ]
    with np.load(METHOD_NPZ, allow_pickle=False) as archive:
        for case_index, case_id in enumerate(config["failure_cases"], start=1):
            if time.perf_counter() - started > float(config["wall_time_cap_seconds"]):
                raise RuntimeError("QR/SVD failure campaign reached its wall-time cap")
            cocycle_path = find_cocycle(case_id, baseline[case_id]["cocycle_cache_sha256"])
            with np.load(cocycle_path, allow_pickle=False) as cocycle_archive:
                native_matrices = np.asarray(cocycle_archive["stms"], dtype=float)
                native_phases = np.asarray(cocycle_archive["phases"], dtype=float)
                rho = float(cocycle_archive["rho"][0])
            native_inputs[case_id] = (native_matrices, native_phases, rho)
            schur_basis_native = np.asarray(archive[f"{case_id}__{SCHUR_METHOD}__bases"], dtype=float)
            target_spectrum = np.asarray(archive[f"{case_id}__{SCHUR_METHOD}__selected_spectrum"], dtype=complex)
            target_spectra[case_id] = target_spectrum
            rank = schur_basis_native.shape[2]
            log.append(f"case_start index={case_index}/5 case={case_id} dimension={rank}")
            for resolution in config["spectral_resolutions"]:
                samples = int(resolution["samples"])
                if resolution["id"] == "native_n45":
                    matrices, phases = native_matrices, native_phases
                    schur_basis = schur_basis_native
                else:
                    matrices, phases = fourier_lift_cocycle(native_matrices, native_phases, samples)
                    schur_basis = resample_bundle(native_phases, schur_basis_native, phases)
                initial_bases = {
                    "local_svd": _initial_svd_bases(matrices, rank, "unstable"),
                    "schur_seed": schur_basis,
                    "deterministic_random": deterministic_random_basis(
                        case_id, samples, rank, phases, config["random_seed_namespace"]
                    ),
                }
                for initialization in config["initializations"]:
                    trajectory_started = time.perf_counter()
                    snapshots, history = trajectory_snapshots(
                        matrices, phases, rho, initial_bases[initialization],
                        [int(value) for value in config["iteration_caps"]],
                        float(config["angle_tolerance_deg"]), int(config["plateau_window"]),
                    )
                    prefix = f"{case_id}__{resolution['id']}__{initialization}"
                    arrays[prefix + "__convergence_history_deg"] = history
                    for cap in config["iteration_caps"]:
                        snapshot = snapshots[int(cap)]
                        residuals = snapshot["residuals"]
                        phase_angles = snapshot["phase_angles"]
                        status = research_status(
                            bool(snapshot["converged"]), float(np.max(residuals)), config
                        )
                        cap_prefix = prefix + f"__cap{cap}"
                        arrays[cap_prefix + "__basis"] = snapshot["basis"]
                        arrays[cap_prefix + "__invariance_residuals"] = residuals
                        arrays[cap_prefix + "__phase_principal_angles_deg"] = phase_angles
                        experiment_rows.append({
                            "schema_version": EXPERIMENT_SCHEMA,
                            "run_id": run_id,
                            "case_id": case_id,
                            "initialization": initialization,
                            "resolution_id": resolution["id"],
                            "resolution_kind": resolution["kind"],
                            "spectral_samples": samples,
                            "iteration_cap": cap,
                            "iterations_executed": snapshot["iterations"],
                            "bundle_dimension": rank,
                            "converged": str(snapshot["converged"]).lower(),
                            "selection_residual_deg": snapshot["selection_residual"],
                            "max_invariance_residual": float(np.max(residuals)),
                            "mean_invariance_residual": float(np.mean(residuals)),
                            "phase_principal_angle_max_deg": float(np.max(phase_angles)),
                            "phase_principal_angle_mean_deg": float(np.mean(phase_angles)),
                            "sign_or_subspace_flips": snapshot["flips"],
                            "tail_angle_mean_deg": snapshot["tail_mean"],
                            "tail_angle_std_deg": snapshot["tail_std"],
                            "tail_relative_range": snapshot["tail_relative_range"],
                            "research_status": status,
                            "runtime_seconds": snapshot["runtime"],
                            "source_map_status": baseline[case_id]["source_map_status"],
                            "source_gate_status": registry_rows[case_id]["source_gate_status"],
                            "cocycle_sha256": sha256(cocycle_path),
                            "source_git_commit": commit,
                        })
                    log.append(
                        f"trajectory case={case_id} resolution={resolution['id']} init={initialization} "
                        f"iterations={len(history)} final_angle_deg={history[-1]:.9g} "
                        f"elapsed_seconds={time.perf_counter() - trajectory_started:.6f}"
                    )

    summary_rows: list[dict[str, Any]] = []
    high_precision_values: dict[str, float] = {}
    for case_id in config["failure_cases"]:
        case_rows = [row for row in experiment_rows if row["case_id"] == case_id]
        native = [row for row in case_rows if row["resolution_id"] == "native_n45"]
        lifted = [row for row in case_rows if row["resolution_id"] == "fourier_lift_n67"]
        best_native = min(native, key=lambda row: (status_rank(row["research_status"]), float(row["max_invariance_residual"])))
        best_lifted = min(lifted, key=lambda row: (status_rank(row["research_status"]), float(row["max_invariance_residual"])))
        best_key = (
            f"{case_id}__native_n45__{best_native['initialization']}__cap{best_native['iteration_cap']}__basis"
        )
        matrices, phases, rho = native_inputs[case_id]
        hp_residual = high_precision_residual(
            matrices, phases, rho, arrays[best_key], int(config["high_precision_decimal_digits"])
        )
        high_precision_values[case_id] = hp_residual
        diagnostics = spectral_diagnostics(
            assemble_discrete_cocycle_operator(matrices, phases, rho),
            target_spectra[case_id], float(config["hyperbolic_tolerance"]),
        )
        local_200 = next(row for row in native if row["initialization"] == "local_svd" and int(row["iteration_cap"]) == 200)
        local_1000 = next(row for row in native if row["initialization"] == "local_svd" and int(row["iteration_cap"]) == 1000)
        schur_best = min(
            (row for row in native if row["initialization"] == "schur_seed"),
            key=lambda row: (status_rank(row["research_status"]), float(row["max_invariance_residual"])),
        )
        random_best = min(
            (row for row in native if row["initialization"] == "deterministic_random"),
            key=lambda row: (status_rank(row["research_status"]), float(row["max_invariance_residual"])),
        )
        status_set = {row["research_status"] for row in native}
        initialization_sensitive = len(status_set) > 1
        plateau_ratio = float(local_1000["max_invariance_residual"]) / max(
            float(local_200["max_invariance_residual"]), np.finfo(float).tiny
        )
        stagnation = (
            local_1000["converged"] == "false"
            and abs(plateau_ratio - 1.0) <= float(config["plateau_relative_change_tolerance"])
        )
        phase_discontinuity = any(float(row["phase_principal_angle_max_deg"]) > 45.0 for row in native)
        source_boundary = "boundary" in registry_rows[case_id]["source_gate_status"] or "fail" in registry_rows[case_id]["source_gate_status"]
        dimension = int(independent_rows[case_id]["independent_selected_block_dimension"])
        any_native_accepted = any(row["research_status"] == "accepted" for row in native)
        if dimension == 2 and any_native_accepted:
            final_label = "accepted_2d_real_subspace"
            rationale = "The independent Schur target is two-dimensional and at least one bounded native QR/SVD run accepted the same real subspace."
        elif dimension == 2:
            final_label = "no_accepted_1d_bundle"
            rationale = (
                "Independent Schur fixes the target as a two-dimensional complex-pair subspace; no bounded native QR/SVD run accepted it, "
                "and a one-dimensional real reinterpretation is prohibited."
            )
        elif initialization_sensitive and schur_best["research_status"] == "accepted":
            final_label = "method_initialization_sensitive"
            rationale = (
                "The one-dimensional legacy control accepts from the Schur seed but not uniformly from local-SVD/random starts under the same frozen thresholds."
            )
        elif best_native["research_status"] == "boundary" and best_lifted["research_status"] == "accepted":
            final_label = "interpolation_resolution_boundary"
            rationale = "The diagnostic Fourier lift changed the bounded outcome from boundary to accepted."
        elif stagnation:
            final_label = "iteration_stagnation"
            rationale = "The local-SVD trajectory did not converge and its residual changed by less than the preset plateau tolerance from 200 to 1000 iterations."
        elif diagnostics["modulus_gap"] < 1.0e-3:
            final_label = "insufficient_spectral_gap"
            rationale = "The selected multiplier has a preset-small modulus separation from nonselected spectrum."
        elif source_boundary:
            final_label = "source_state_boundary"
            rationale = "The source registry remains boundary/failed and the bounded numerical diagnostics did not isolate a stronger method-only cause."
        else:
            final_label = "unresolved"
            rationale = "The bounded experiments exclude a simple cap-only repair but do not isolate one accepted cause label."
        if final_label not in config["allowed_final_labels"]:
            raise RuntimeError(f"invalid final label {final_label}")
        summary_rows.append({
            "schema_version": SCHEMA,
            "run_id": run_id,
            "case_id": case_id,
            "member_id": registry_rows[case_id]["member_id"],
            "source_gate_status": registry_rows[case_id]["source_gate_status"],
            "baseline_bundle_dimension": baseline[case_id]["bundle_dimension"],
            "independent_schur_dimension": dimension,
            "independent_schur_classification": independent_rows[case_id]["independent_classification"],
            "target_spectrum": format_spectrum(target_spectra[case_id]),
            "target_modulus": diagnostics["target_modulus"],
            "relative_imaginary_part": independent_rows[case_id]["independent_relative_imaginary_part"],
            "unstable_eigenvalue_count": diagnostics["unstable_count"],
            "near_unit_eigenvalue_count": diagnostics["near_unit_count"],
            "nearest_nonselected_complex_gap_relative": diagnostics["complex_gap"],
            "nearest_nonselected_modulus_gap_relative": diagnostics["modulus_gap"],
            "target_to_dominant_modulus_ratio": diagnostics["target_to_dominant_ratio"],
            "branch_selection_correct": str(diagnostics["branch_correct"]).lower(),
            "initializations_tested": 3,
            "iteration_caps_tested": "200;500;1000",
            "resolutions_tested": "native_n45;fourier_lift_n67",
            "best_native_initialization": best_native["initialization"],
            "best_native_iteration_cap": best_native["iteration_cap"],
            "best_native_research_status": best_native["research_status"],
            "best_native_max_invariance_residual": best_native["max_invariance_residual"],
            "best_native_selection_residual_deg": best_native["selection_residual_deg"],
            "native_local_svd_residual_200": local_200["max_invariance_residual"],
            "native_local_svd_residual_1000": local_1000["max_invariance_residual"],
            "native_local_svd_plateau_ratio": plateau_ratio,
            "native_schur_seed_status": schur_best["research_status"],
            "native_random_status": random_best["research_status"],
            "fourier_lift_best_status": best_lifted["research_status"],
            "resolution_status_agreement": str(best_native["research_status"] == best_lifted["research_status"]).lower(),
            "phase_alignment_discontinuity_observed": str(phase_discontinuity).lower(),
            "iteration_stagnation_observed": str(stagnation).lower(),
            "initialization_sensitivity_observed": str(initialization_sensitive).lower(),
            "source_state_boundary_observed": str(source_boundary).lower(),
            "high_precision_decimal_digits": config["high_precision_decimal_digits"],
            "high_precision_scope": config["high_precision_scope"],
            "high_precision_max_invariance_residual": hp_residual,
            "double_to_high_precision_residual_ratio": float(best_native["max_invariance_residual"]) / max(hp_residual, np.finfo(float).tiny),
            "final_label": final_label,
            "classification_rationale": rationale,
            "negative_result_retained": "true",
            "registry_sha256": registry_hash,
            "source_git_commit": commit,
        })
        log.append(
            f"classification case={case_id} label={final_label} best_native={best_native['research_status']} "
            f"best_residual={best_native['max_invariance_residual']} hp_residual={hp_residual:.17g}"
        )

    arrays["high_precision_case_ids"] = np.asarray(config["failure_cases"])
    arrays["high_precision_max_invariance_residuals"] = np.asarray(
        [high_precision_values[case] for case in config["failure_cases"]]
    )
    write_csv(EXPERIMENT_CSV, experiment_rows, EXPERIMENT_FIELDS)
    write_csv(SUMMARY_CSV, summary_rows, SUMMARY_FIELDS)
    NPZ_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_OUTPUT, **arrays)

    label_counts: dict[str, int] = {}
    for row in summary_rows:
        label_counts[row["final_label"]] = label_counts.get(row["final_label"], 0) + 1
    doc = [
        "# QR/SVD five-case failure analysis", "",
        "## Bounded design", "",
        "The frozen five failures were tested with exactly three initializations, caps 200/500/1000, and two spectral "
        "representations (native N45 plus a clearly labelled N67 Fourier lift). A trajectory was advanced once to its "
        "largest cap and snapshotted at the lower caps; no cap exceeded 1000. The pass/boundary thresholds remained "
        "1e-6/1e-3. An 80-decimal-digit residual recomputation checked whether the best native residual was a binary64 "
        "evaluation artifact; it was not presented as a full arbitrary-precision QR trajectory.", "",
        f"Total bounded rows: {len(experiment_rows)}; final labels: `{json.dumps(label_counts, sort_keys=True)}`.", "",
        "## Per-case classification", "",
        "| case | independent target | best native | local-SVD residual 200 -> 1000 | N67 best | high-precision residual | label |",
        "|---|---|---|---:|---|---:|---|",
    ]
    for row in summary_rows:
        doc.append(
            f"| {row['case_id']} | {row['independent_schur_dimension']}D, rel-imag={float(row['relative_imaginary_part']):.3e} | "
            f"{row['best_native_research_status']} ({row['best_native_initialization']}) | "
            f"{float(row['native_local_svd_residual_200']):.3e} -> {float(row['native_local_svd_residual_1000']):.3e} | "
            f"{row['fourier_lift_best_status']} | {float(row['high_precision_max_invariance_residual']):.3e} | "
            f"`{row['final_label']}` |"
        )
    doc.extend([
        "", "## Diagnostic conclusions", "",
        "- The four physical corrected-rho cases retain their independently verified two-dimensional complex-pair "
        "classification. None may be rewritten as a one-dimensional real bundle, regardless of iteration count.",
        "- The legacy seed-rho member is reported separately. Its Schur-seeded behavior diagnoses initialization "
        "sensitivity; it does not validate the physical corrected-rho case.",
        "- The N67 results are interpolation diagnostics, not newly integrated source trajectories. Resolution changes "
        "therefore cannot promote any reproduction or source gate.",
        "- Phase discontinuity, spectral separation, source-gate status, branch selection, cap stagnation, initialization, "
        "and high-precision residual evaluation are all retained as explicit columns rather than folded into pass rate.",
        "", "## Truth boundary", "",
        "The campaign classifies failures; it does not repair them by deleting rows, increasing caps beyond the declared "
        "limit, changing physical rho, or relaxing thresholds. Chapter 4 remains frozen at `paper_projection=fail` and "
        "`paper_3d=false`.",
    ])
    DOC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUTPUT.write_text("\n".join(doc) + "\n", encoding="utf-8")

    FAILURE_EVIDENCE.write_text(
        "# QR/SVD negative-result evidence\n\n"
        "The baseline failure set is exactly five rows: Route H physical members 17, 32, 54, and 68, plus the "
        "member-68 legacy seed-rho control. All 90 bounded experiment rows are preserved in "
        "`qr_svd_failure_experiments.csv`, including nonconvergence, large phase angles, and residuals above threshold.\n\n"
        "No failed trajectory was removed. No cap above 1000, fourth initialization, third resolution, parameter change, "
        "or threshold relaxation was used. The N67 cocycle is explicitly a Fourier lift of the frozen N45 matrices; "
        "it is not misrepresented as an independently reintegrated physical source. Windows `numpy.longdouble` is "
        "binary64 on this machine, so the high-precision check used mpmath at 80 decimal digits for residual arithmetic "
        "and is explicitly scoped as a residual recomputation rather than a full QR trajectory.\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    log.extend([
        f"experiment_rows={len(experiment_rows)}", f"summary_rows={len(summary_rows)}",
        f"label_counts={json.dumps(label_counts, sort_keys=True)}",
        f"elapsed_seconds={elapsed:.6f}",
        f"complete_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
    ])
    LOG_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_OUTPUT.write_text("\n".join(log) + "\n", encoding="utf-8")

    hash_paths = [
        CONFIG, Path(__file__), REGISTRY, METHOD_CSV, METHOD_NPZ, INDEPENDENT_CSV,
        SUMMARY_CSV, EXPERIMENT_CSV, NPZ_OUTPUT, DOC_OUTPUT, LOG_OUTPUT, FAILURE_EVIDENCE,
    ]
    write_csv(HASH_OUTPUT, [
        {"artifact": str(path.relative_to(ROOT)).replace("\\", "/"), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in hash_paths
    ], ["artifact", "bytes", "sha256"])
    print(
        f"QR/SVD failure classification PASS cases={len(summary_rows)} rows={len(experiment_rows)} "
        f"labels={json.dumps(label_counts, sort_keys=True)} elapsed={elapsed:.3f}s"
    )


if __name__ == "__main__":
    main()
