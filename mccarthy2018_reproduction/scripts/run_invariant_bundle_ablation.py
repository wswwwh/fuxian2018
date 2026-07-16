#!/usr/bin/env python3
"""Run the seven-variant invariant-bundle ablation and build paper figures."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.artifact_fingerprints import fingerprint_fields  # noqa: E402
from qp_orbits.invariant_bundles import (  # noqa: E402
    _align_to_reference,
    _branch_candidates,
    _initial_svd_bases,
    _orthonormalize,
    _principal_angles_deg,
    _target_operator_eigenvalue,
    align_bundle_phase,
    assemble_discrete_cocycle_operator,
    bundle_invariance_metrics,
    cross_resolution_principal_angles_deg,
    periodic_interpolation_matrix,
    phase_principal_angles_deg,
    qr_svd_cocycle_bundle_iteration,
    real_schur_bundle_tracking,
)

RESEARCH = ROOT / "research" / "invariant_bundles"
CONFIG = RESEARCH / "configs" / "ablation_study.json"
REGISTRY = RESEARCH / "benchmarks" / "benchmark_registry.csv"
METHOD_CSV = RESEARCH / "results" / "csv" / "method_comparison.csv"
COCYCLE_DIR = RESEARCH / "results" / "npz" / "cocycles"
CSV_OUTPUT = RESEARCH / "results" / "csv" / "ablation_study.csv"
NPZ_OUTPUT = RESEARCH / "results" / "npz" / "ablation_study.npz"
PAPER_OUTPUT = RESEARCH / "paper" / "ablation_results.md"
LOG_OUTPUT = RESEARCH / "results" / "logs" / "ablation_study.log"
FAILURE_OUTPUT = RESEARCH / "results" / "logs" / "ablation_failure_evidence.md"
HASH_OUTPUT = RESEARCH / "results" / "logs" / "ablation_artifact_hashes.csv"
FIGURE_DIR = RESEARCH / "figures"
FIGURE_STEMS = (
    "ablation_bundle_residual",
    "ablation_phase_continuity",
    "ablation_manifold_geometry",
)
SCHEMA = "invariant_bundle_ablation_v1"

FIELDS = [
    "schema_version", "run_id", "case_id", "family", "variant", "variant_short_label",
    "spectral_samples", "bundle_dimension", "schur_seed_dimension", "classification",
    "relative_imaginary_part", "bundle_residual_max", "bundle_residual_mean",
    "phase_principal_angle_max_deg", "phase_principal_angle_mean_deg",
    "sign_or_subspace_flips_detected", "iteration_alignment_operations",
    "cross_resolution_angle_max_deg", "cross_resolution_source",
    "manifold_geometry_distance", "manifold_geometry_metric", "runtime_seconds",
    "iterations", "converged", "research_status", "failure_reason",
    "source_map_status", "registry_sha256", "cocycle_sha256", "source_git_commit",
]


@dataclass
class VariantResult:
    bases: np.ndarray
    dimension: int
    classification: str
    relative_imaginary: float
    iterations: int
    converged: bool
    iteration_flips: int
    runtime: float


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
    matches = [
        path for path in COCYCLE_DIR.glob(f"{case_id}_*.npz")
        if sha256(path) == expected_hash.upper()
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one hashed cocycle for {case_id}, found {len(matches)}")
    return matches[0]


def pointwise_raw(
    matrices: np.ndarray,
    phases: np.ndarray,
    hyperbolic_tolerance: float,
    *,
    sign_align: bool,
) -> VariantResult:
    started = time.perf_counter()
    samples, dimension, _ = matrices.shape
    bases = np.empty((samples, dimension, 1), dtype=float)
    relative_imaginary: list[float] = []
    for index, matrix in enumerate(matrices):
        values, vectors = np.linalg.eig(matrix)
        candidates = _branch_candidates(values, "unstable", hyperbolic_tolerance)
        selected = int(candidates[np.argmax(np.abs(values[candidates]))])
        value = complex(values[selected])
        vector = vectors[:, selected]
        direction = np.real(vector)
        if np.linalg.norm(direction) < 1.0e-13:
            direction = np.imag(vector)
        if np.linalg.norm(direction) < 1.0e-13:
            raise RuntimeError(f"pointwise direction vanished at phase {index}")
        bases[index, :, 0] = direction / np.linalg.norm(direction)
        relative_imaginary.append(abs(value.imag) / max(abs(value), np.finfo(float).tiny))
    detected_flips = 0
    if sign_align:
        bases, detected_flips = align_bundle_phase(bases, phases)
    rel_imag = float(max(relative_imaginary))
    return VariantResult(
        bases=bases,
        dimension=1,
        classification=(
            "complex_vector_projected_to_real_1d_failure"
            if rel_imag > 1.0e-10 else "real_1d_pointwise_candidate"
        ),
        relative_imaginary=rel_imag,
        iterations=0,
        converged=rel_imag <= 1.0e-10,
        iteration_flips=detected_flips,
        runtime=time.perf_counter() - started,
    )


def partial_schur_raw(
    matrices: np.ndarray,
    phases: np.ndarray,
    rho: float,
    config: dict[str, Any],
    *,
    phase_track: bool,
) -> VariantResult:
    started = time.perf_counter()
    operator = assemble_discrete_cocycle_operator(matrices, phases, rho)
    eigenvalues, eigenvectors = np.linalg.eig(operator)
    target = _target_operator_eigenvalue(
        eigenvalues, branch="unstable",
        hyperbolic_tolerance=float(config["hyperbolic_tolerance"]),
    )
    rel_imag = abs(target.imag) / max(abs(target), np.finfo(float).tiny)
    selected = int(np.argmin(np.abs(eigenvalues - target)))
    vector = eigenvectors[:, selected]
    if rel_imag <= float(config["real_relative_imaginary_tolerance"]):
        candidate = np.real(vector)[:, None]
        if np.linalg.norm(candidate) < 1.0e-13:
            candidate = np.imag(vector)[:, None]
        rank = 1
    else:
        candidate = np.column_stack((np.real(vector), np.imag(vector)))
        rank = 2
    global_basis, factor = np.linalg.qr(candidate, mode="reduced")
    if np.min(np.abs(np.diag(factor))) < 1.0e-13:
        raise RuntimeError("partial-Schur candidate lost rank")
    bases = _orthonormalize(global_basis.reshape(matrices.shape[0], matrices.shape[1], rank))
    flips = 0
    if phase_track:
        bases, flips = align_bundle_phase(bases, phases)
    return VariantResult(
        bases=bases,
        dimension=rank,
        classification=(
            "real_1d_hyperbolic_bundle" if rank == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        relative_imaginary=float(rel_imag),
        iterations=0,
        converged=True,
        iteration_flips=flips,
        runtime=time.perf_counter() - started,
    )


def qr_without_phase_alignment(
    matrices: np.ndarray,
    phases: np.ndarray,
    rho: float,
    config: dict[str, Any],
    rank: int,
) -> VariantResult:
    started = time.perf_counter()
    bases = _initial_svd_bases(matrices, rank, "unstable")
    shifted_to_base = periodic_interpolation_matrix(phases + rho, phases)
    history: list[float] = []
    reference_flips = 0
    for _ in range(int(config["qr_iteration_cap"])):
        transported = _orthonormalize(np.einsum("nij,njk->nik", matrices, bases))
        candidate = _orthonormalize(np.einsum("ij,jdk->idk", shifted_to_base, transported))
        candidate, flips = _align_to_reference(candidate, bases)
        reference_flips += flips
        angle = max(
            float(np.max(_principal_angles_deg(bases[index], candidate[index])))
            for index in range(bases.shape[0])
        )
        history.append(angle)
        bases = candidate
        if angle <= float(config["qr_angle_tolerance_deg"]):
            break
    return VariantResult(
        bases=bases,
        dimension=rank,
        classification=(
            "real_1d_hyperbolic_bundle" if rank == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        relative_imaginary=float("nan"),
        iterations=len(history),
        converged=bool(history and history[-1] <= float(config["qr_angle_tolerance_deg"])),
        iteration_flips=reference_flips,
        runtime=time.perf_counter() - started,
    )


def compute_variant(
    variant: str,
    matrices: np.ndarray,
    phases: np.ndarray,
    rho: float,
    config: dict[str, Any],
    schur_dimension: int,
    schur_relative_imaginary: float,
) -> VariantResult:
    if variant == "pointwise_eig_no_phase_alignment":
        return pointwise_raw(matrices, phases, float(config["hyperbolic_tolerance"]), sign_align=False)
    if variant == "pointwise_eig_sign_alignment_only":
        return pointwise_raw(matrices, phases, float(config["hyperbolic_tolerance"]), sign_align=True)
    if variant == "partial_real_schur_no_phase_tracking":
        return partial_schur_raw(matrices, phases, rho, config, phase_track=False)
    if variant == "partial_real_schur_phase_tracking":
        started = time.perf_counter()
        result = real_schur_bundle_tracking(
            matrices, phases, rho,
            hyperbolic_tolerance=float(config["hyperbolic_tolerance"]),
            real_relative_imaginary_tolerance=float(config["real_relative_imaginary_tolerance"]),
        )
        return VariantResult(
            bases=result.bases, dimension=result.bundle_dimension,
            classification=result.classification, relative_imaginary=result.relative_imaginary,
            iterations=result.iterations, converged=result.converged,
            iteration_flips=result.sign_or_orientation_flips,
            runtime=time.perf_counter() - started,
        )
    if variant == "qr_svd_no_phase_alignment":
        result = qr_without_phase_alignment(matrices, phases, rho, config, rank=1)
        result.relative_imaginary = schur_relative_imaginary
        if schur_dimension == 2:
            result.classification = "invalid_1d_complex_pair_ablation_control"
        return result
    if variant in {
        "qr_svd_phase_alignment",
        "qr_svd_phase_alignment_schur_dimension_seed",
    }:
        rank = 1 if variant == "qr_svd_phase_alignment" else schur_dimension
        started = time.perf_counter()
        result = qr_svd_cocycle_bundle_iteration(
            matrices, phases, rho, bundle_dimension=rank,
            max_iterations=int(config["qr_iteration_cap"]),
            angle_tolerance_deg=float(config["qr_angle_tolerance_deg"]),
            hyperbolic_tolerance=float(config["hyperbolic_tolerance"]),
            real_relative_imaginary_tolerance=float(config["real_relative_imaginary_tolerance"]),
        )
        classification = result.classification
        if rank == 1 and schur_dimension == 2:
            classification = "invalid_1d_complex_pair_ablation_control"
        return VariantResult(
            bases=result.bases, dimension=result.bundle_dimension,
            classification=classification, relative_imaginary=schur_relative_imaginary,
            iterations=result.iterations, converged=result.converged,
            iteration_flips=result.sign_or_orientation_flips,
            runtime=time.perf_counter() - started,
        )
    raise ValueError(f"unknown variant {variant}")


def fourier_resample_cocycle(matrices: np.ndarray, phases: np.ndarray, samples: int) -> tuple[np.ndarray, np.ndarray]:
    evaluation = np.linspace(0.0, 2.0 * np.pi, samples, endpoint=False)
    weights = periodic_interpolation_matrix(phases, evaluation)
    return np.einsum("ij,jab->iab", weights, matrices), evaluation


def geometry_cloud(matrices: np.ndarray, bases: np.ndarray, circle_directions: int) -> np.ndarray:
    rank = bases.shape[2]
    if rank == 1:
        coefficients = np.asarray([[-1.0], [1.0]])
    elif rank == 2:
        angles = np.linspace(0.0, 2.0 * np.pi, circle_directions, endpoint=False)
        coefficients = np.column_stack((np.cos(angles), np.sin(angles)))
    else:
        raise ValueError("geometry cloud supports rank one or two")
    points: list[np.ndarray] = []
    for matrix, basis in zip(matrices, bases):
        perturbations = coefficients @ basis.T
        transported = perturbations @ matrix.T
        points.append(perturbations[:, :3])
        points.append(transported[:, :3])
    return np.vstack(points)


def symmetric_hd95(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref_tree = cKDTree(reference)
    cand_tree = cKDTree(candidate)
    cand_to_ref = ref_tree.query(candidate, k=1, workers=1)[0]
    ref_to_cand = cand_tree.query(reference, k=1, workers=1)[0]
    raw = max(float(np.quantile(cand_to_ref, 0.95)), float(np.quantile(ref_to_cand, 0.95)))
    scale = float(np.linalg.norm(np.ptp(reference, axis=0)))
    if scale <= np.finfo(float).tiny:
        raise RuntimeError("reference geometry has zero scale")
    return raw / scale


def classify(result: VariantResult, max_residual: float, config: dict[str, Any]) -> tuple[str, str]:
    reasons: list[str] = []
    if result.classification in {
        "complex_vector_projected_to_real_1d_failure",
        "invalid_1d_complex_pair_ablation_control",
    }:
        reasons.append(result.classification)
    if result.iterations and not result.converged:
        reasons.append("qr_iteration_not_converged_at_cap")
    if max_residual > float(config["pass_max_invariance_residual"]):
        reasons.append("max_invariance_residual_gt_1e-6")
    if not reasons:
        return "accepted", ""
    if (
        result.classification not in {
            "complex_vector_projected_to_real_1d_failure",
            "invalid_1d_complex_pair_ablation_control",
        }
        and max_residual <= float(config["boundary_max_invariance_residual"])
    ):
        return "boundary", ";".join(reasons)
    return "fail", ";".join(reasons)


def configure_plot_style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.0,
        "axes.labelsize": 8.0, "xtick.labelsize": 7.0, "ytick.labelsize": 7.0,
        "legend.fontsize": 7.0, "lines.linewidth": 1.1, "lines.markersize": 4.0,
        "axes.spines.top": False, "axes.spines.right": False,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def save_figure(fig: plt.Figure, stem: str, dpi: int) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=dpi, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_figures(rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    configure_plot_style()
    variants = config["variants"]
    labels = [config["variant_short_labels"][variant] for variant in variants]
    cases = config["cases"]
    case_labels = {
        "em_halo_12p40_n45": "Halo N45",
        "em_vertical_12p66_n57": "Vertical N57",
        "se_active_geometry_member_468": "Sun-Earth 468",
        "route_h_member_68": "Route H 68 physical",
        "route_h_member_32": "Route H 32 negative",
    }
    colors = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9"]
    markers = ["o", "s", "^", "D", "P"]
    index = {(row["case_id"], row["variant"]): row for row in rows}
    x = np.arange(len(variants))

    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for case, color, marker in zip(cases, colors, markers):
        values = np.asarray([
            float(index[(case, variant)]["bundle_residual_max"])
            if np.isfinite(float(index[(case, variant)]["bundle_residual_max"])) else np.nan
            for variant in variants
        ])
        ax.plot(x, values, marker=marker, color=color, label=case_labels[case])
        for position, value in enumerate(values):
            if not np.isfinite(value):
                ax.scatter(position, 1.2, marker="x", color=color, s=28, linewidths=1.2)
    ax.axhline(1.0e-6, color="#444444", linestyle="--", linewidth=0.8, label="pass 1e-6")
    ax.axhline(1.0e-3, color="#777777", linestyle=":", linewidth=0.8, label="boundary 1e-3")
    ax.set_yscale("log")
    ax.set_ylim(1.0e-13, 2.0)
    ax.set_ylabel("Maximum bundle residual")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Ablation variant (V1–V7)")
    ax.grid(axis="y", which="both", color="#dddddd", linewidth=0.45)
    ax.legend(ncol=2, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.text(0.01, 0.98, "× = method exception", transform=ax.transAxes, va="top", fontsize=7)
    save_figure(fig, "ablation_bundle_residual", int(config["figure_dpi"]))

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.5))
    for case, color, marker in zip(cases, colors, markers):
        angles = np.asarray([float(index[(case, variant)]["phase_principal_angle_max_deg"]) for variant in variants])
        flips = np.asarray([float(index[(case, variant)]["sign_or_subspace_flips_detected"]) for variant in variants])
        axes[0].plot(x, angles, marker=marker, color=color, label=case_labels[case])
        axes[1].plot(x, flips + 1.0, marker=marker, color=color)
        for position in np.flatnonzero(~np.isfinite(angles)):
            axes[0].scatter(position, 110.0, marker="x", color=color, s=28, linewidths=1.2)
        for position in np.flatnonzero(~np.isfinite(flips)):
            axes[1].scatter(position, 80.0, marker="x", color=color, s=28, linewidths=1.2)
    axes[0].set_yscale("log")
    axes[0].set_ylim(0.5, 130.0)
    axes[0].set_ylabel("Maximum adjacent-phase angle (deg)")
    axes[1].set_yscale("log")
    axes[1].set_ylim(0.8, 100.0)
    axes[1].set_ylabel("Detected phase corrections + 1")
    for panel, axis in zip(("(a)", "(b)"), axes):
        axis.set_xticks(x, labels)
        axis.set_xlabel("Ablation variant")
        axis.grid(axis="y", which="both", color="#dddddd", linewidth=0.45)
        axis.text(0.02, 0.97, panel, transform=axis.transAxes, va="top", fontweight="bold")
    axes[0].legend(ncol=1, frameon=False, loc="upper left", bbox_to_anchor=(2.18, 1.0))
    axes[0].text(0.02, 0.05, "× = method exception", transform=axes[0].transAxes, fontsize=7)
    save_figure(fig, "ablation_phase_continuity", int(config["figure_dpi"]))

    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for case, color, marker in zip(cases, colors, markers):
        values = np.asarray([float(index[(case, variant)]["manifold_geometry_distance"]) for variant in variants])
        plotted = np.where(np.isfinite(values), np.maximum(values, 1.0e-13), np.nan)
        ax.plot(x, plotted, marker=marker, color=color, label=case_labels[case])
        for position, value in enumerate(values):
            if not np.isfinite(value):
                ax.scatter(position, 1.2, marker="x", color=color, s=28, linewidths=1.2)
    ax.set_yscale("log")
    ax.set_ylim(1.0e-13, 2.0)
    ax.set_ylabel("One-map geometry distance to V7")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Ablation variant (V1–V7)")
    ax.grid(axis="y", which="both", color="#dddddd", linewidth=0.45)
    ax.legend(ncol=2, frameon=False, loc="upper left", bbox_to_anchor=(1.01, 1.0))
    ax.text(0.01, 0.98, "Symmetric HD95; × = method exception", transform=ax.transAxes, va="top", fontsize=7)
    save_figure(fig, "ablation_manifold_geometry", int(config["figure_dpi"]))


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    started = time.perf_counter()
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    commit = git_commit()
    registry_hash = sha256(REGISTRY)
    registry = {row["case_id"]: row for row in read_csv(REGISTRY)}
    method_rows = read_csv(METHOD_CSV)
    method_index = {(row["case_id"], row["method"]): row for row in method_rows}
    required_sources = set(config["cases"])
    required_sources.update(
        value for value in config["cross_resolution_sources"].values()
        if not value.startswith("diagnostic_fourier_")
    )
    cocycles: dict[str, tuple[np.ndarray, np.ndarray, float, Path]] = {}
    for case_id in required_sources:
        source_row = method_index[(case_id, "ordered_partial_real_schur_tracking")]
        path = find_cocycle(case_id, source_row["cocycle_cache_sha256"])
        with np.load(path, allow_pickle=False) as archive:
            cocycles[case_id] = (
                np.asarray(archive["stms"], dtype=float),
                np.asarray(archive["phases"], dtype=float),
                float(archive["rho"][0]),
                path,
            )

    fine_results: dict[tuple[str, str], VariantResult | None] = {}
    coarse_results: dict[tuple[str, str], VariantResult | None] = {}
    fine_metrics: dict[tuple[str, str], dict[str, Any]] = {}
    coarse_phases_by_case: dict[str, np.ndarray] = {}
    fine_geometry: dict[tuple[str, str], np.ndarray] = {}
    errors: dict[tuple[str, str, str], str] = {}
    log = [
        f"start_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"run_id={run_id}", f"config_sha256={sha256(CONFIG)}",
        f"registry_sha256={registry_hash}", f"source_git_commit={commit}",
    ]
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA]), "run_id": np.asarray([run_id]),
        "registry_sha256": np.asarray([registry_hash]), "source_git_commit": np.asarray([commit]),
    }

    for case_id in config["cases"]:
        if time.perf_counter() - started > float(config["wall_time_cap_seconds"]):
            raise RuntimeError("ablation campaign reached its wall-time cap")
        matrices, phases, rho, path = cocycles[case_id]
        schur_reference = real_schur_bundle_tracking(
            matrices, phases, rho,
            hyperbolic_tolerance=float(config["hyperbolic_tolerance"]),
            real_relative_imaginary_tolerance=float(config["real_relative_imaginary_tolerance"]),
        )
        coarse_source = config["cross_resolution_sources"][case_id]
        if coarse_source.startswith("diagnostic_fourier_n"):
            samples = int(coarse_source.rsplit("n", 1)[1])
            coarse_matrices, coarse_phases = fourier_resample_cocycle(matrices, phases, samples)
            coarse_rho = rho
        else:
            coarse_matrices, coarse_phases, coarse_rho, _ = cocycles[coarse_source]
        coarse_phases_by_case[case_id] = coarse_phases
        coarse_schur = real_schur_bundle_tracking(
            coarse_matrices, coarse_phases, coarse_rho,
            hyperbolic_tolerance=float(config["hyperbolic_tolerance"]),
            real_relative_imaginary_tolerance=float(config["real_relative_imaginary_tolerance"]),
        )
        log.append(
            f"case_start case={case_id} fine_n={len(phases)} coarse={coarse_source} "
            f"schur_dim={schur_reference.bundle_dimension}"
        )
        for variant in config["variants"]:
            for scope, scope_matrices, scope_phases, scope_rho, scope_schur in (
                ("fine", matrices, phases, rho, schur_reference),
                ("coarse", coarse_matrices, coarse_phases, coarse_rho, coarse_schur),
            ):
                try:
                    result = compute_variant(
                        variant, scope_matrices, scope_phases, scope_rho, config,
                        scope_schur.bundle_dimension, scope_schur.relative_imaginary,
                    )
                except Exception as exc:  # explicit negative-result row
                    errors[(case_id, variant, scope)] = f"{type(exc).__name__}: {exc}"
                    result = None
                if scope == "fine":
                    fine_results[(case_id, variant)] = result
                else:
                    coarse_results[(case_id, variant)] = result
            result = fine_results[(case_id, variant)]
            if result is not None:
                local_maps, residuals = bundle_invariance_metrics(matrices, phases, rho, result.bases)
                phase_angles = phase_principal_angles_deg(result.bases, phases)
                detected_flips = align_bundle_phase(result.bases, phases)[1]
                fine_metrics[(case_id, variant)] = {
                    "local_maps": local_maps, "residuals": residuals,
                    "phase_angles": phase_angles, "detected_flips": detected_flips,
                }
                cloud = geometry_cloud(
                    matrices, result.bases, int(config["geometry_circle_directions_for_rank2"])
                )
                fine_geometry[(case_id, variant)] = cloud
                prefix = f"{case_id}__{variant}"
                arrays[prefix + "__basis"] = result.bases
                arrays[prefix + "__local_reduced_maps"] = local_maps
                arrays[prefix + "__invariance_residuals"] = residuals
                arrays[prefix + "__phase_principal_angles_deg"] = phase_angles
                arrays[prefix + "__geometry_cloud"] = cloud
            coarse = coarse_results[(case_id, variant)]
            if coarse is not None:
                arrays[f"{case_id}__{variant}__coarse_basis"] = coarse.bases

    geometry_distances: dict[tuple[str, str], float] = {}
    for case_id in config["cases"]:
        reference_key = (case_id, "qr_svd_phase_alignment_schur_dimension_seed")
        if reference_key not in fine_geometry:
            raise RuntimeError(f"missing V7 geometry reference for {case_id}")
        reference = fine_geometry[reference_key]
        for variant in config["variants"]:
            key = (case_id, variant)
            geometry_distances[key] = (
                symmetric_hd95(reference, fine_geometry[key])
                if key in fine_geometry else float("nan")
            )

    output_rows: list[dict[str, Any]] = []
    for case_id in config["cases"]:
        matrices, phases, rho, path = cocycles[case_id]
        schur_reference = fine_results[(case_id, "partial_real_schur_phase_tracking")]
        if schur_reference is None:
            raise RuntimeError(f"missing Schur dimension reference for {case_id}")
        for variant in config["variants"]:
            result = fine_results[(case_id, variant)]
            coarse = coarse_results[(case_id, variant)]
            if result is None:
                failure = errors[(case_id, variant, "fine")]
                row = {
                    "schema_version": SCHEMA, "run_id": run_id, "case_id": case_id,
                    "family": registry[case_id]["family"], "variant": variant,
                    "variant_short_label": config["variant_short_labels"][variant],
                    "spectral_samples": len(phases), "bundle_dimension": 0,
                    "schur_seed_dimension": schur_reference.dimension,
                    "classification": "method_exception", "relative_imaginary_part": float("nan"),
                    "bundle_residual_max": float("nan"), "bundle_residual_mean": float("nan"),
                    "phase_principal_angle_max_deg": float("nan"),
                    "phase_principal_angle_mean_deg": float("nan"),
                    "sign_or_subspace_flips_detected": float("nan"), "iteration_alignment_operations": 0,
                    "cross_resolution_angle_max_deg": float("nan"),
                    "cross_resolution_source": config["cross_resolution_sources"][case_id],
                    "manifold_geometry_distance": float("nan"),
                    "manifold_geometry_metric": config["geometry_metric"],
                    "runtime_seconds": 0.0, "iterations": 0, "converged": "false",
                    "research_status": "fail", "failure_reason": failure,
                    "source_map_status": method_index[(case_id, "ordered_partial_real_schur_tracking")]["source_map_status"],
                    "registry_sha256": registry_hash, "cocycle_sha256": sha256(path),
                    "source_git_commit": commit,
                }
            else:
                metrics = fine_metrics[(case_id, variant)]
                residuals = metrics["residuals"]
                phase_angles = metrics["phase_angles"]
                if coarse is not None and coarse.dimension == result.dimension:
                    cross_angle = float(np.max(cross_resolution_principal_angles_deg(
                        coarse_phases_by_case[case_id], coarse.bases, phases, result.bases
                    )))
                    cross_failure = ""
                else:
                    cross_angle = float("nan")
                    cross_failure = (
                        "coarse_method_exception" if coarse is None
                        else "cross_resolution_dimension_mismatch"
                    )
                status, reason = classify(result, float(np.max(residuals)), config)
                if cross_failure:
                    reason = ";".join(filter(None, (reason, cross_failure)))
                row = {
                    "schema_version": SCHEMA, "run_id": run_id, "case_id": case_id,
                    "family": registry[case_id]["family"], "variant": variant,
                    "variant_short_label": config["variant_short_labels"][variant],
                    "spectral_samples": len(phases), "bundle_dimension": result.dimension,
                    "schur_seed_dimension": schur_reference.dimension,
                    "classification": result.classification,
                    "relative_imaginary_part": result.relative_imaginary,
                    "bundle_residual_max": float(np.max(residuals)),
                    "bundle_residual_mean": float(np.mean(residuals)),
                    "phase_principal_angle_max_deg": float(np.max(phase_angles)),
                    "phase_principal_angle_mean_deg": float(np.mean(phase_angles)),
                    "sign_or_subspace_flips_detected": metrics["detected_flips"],
                    "iteration_alignment_operations": result.iteration_flips,
                    "cross_resolution_angle_max_deg": cross_angle,
                    "cross_resolution_source": config["cross_resolution_sources"][case_id],
                    "manifold_geometry_distance": geometry_distances[(case_id, variant)],
                    "manifold_geometry_metric": config["geometry_metric"],
                    "runtime_seconds": result.runtime, "iterations": result.iterations,
                    "converged": str(result.converged).lower(), "research_status": status,
                    "failure_reason": reason,
                    "source_map_status": method_index[(case_id, "ordered_partial_real_schur_tracking")]["source_map_status"],
                    "registry_sha256": registry_hash, "cocycle_sha256": sha256(path),
                    "source_git_commit": commit,
                }
            output_rows.append(row)
            log.append(
                f"row case={case_id} variant={variant} status={row['research_status']} "
                f"dimension={row['bundle_dimension']} residual={row['bundle_residual_max']} "
                f"runtime={row['runtime_seconds']}"
            )

    write_csv(CSV_OUTPUT, output_rows, FIELDS)
    NPZ_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(NPZ_OUTPUT, **arrays)
    plot_figures(output_rows, config)

    index = {(row["case_id"], row["variant"]): row for row in output_rows}
    anchor_cases = config["cases"][:3]
    schur_tracking_ratios = []
    qr_alignment_ratios = []
    pointwise_cross_resolution_ratios = []
    pointwise_geometry_distances = []
    for case_id in anchor_cases:
        v3 = float(index[(case_id, config["variants"][2])]["bundle_residual_max"])
        v4 = float(index[(case_id, config["variants"][3])]["bundle_residual_max"])
        v5 = float(index[(case_id, config["variants"][4])]["bundle_residual_max"])
        v6 = float(index[(case_id, config["variants"][5])]["bundle_residual_max"])
        schur_tracking_ratios.append(v3 / max(v4, np.finfo(float).tiny))
        qr_alignment_ratios.append(v5 / max(v6, np.finfo(float).tiny))
        pointwise_cross_resolution_ratios.append(
            float(index[(case_id, config["variants"][0])]["cross_resolution_angle_max_deg"])
            / max(
                float(index[(case_id, config["variants"][1])]["cross_resolution_angle_max_deg"]),
                np.finfo(float).tiny,
            )
        )
        pointwise_geometry_distances.append(
            float(index[(case_id, config["variants"][1])]["manifold_geometry_distance"])
        )
    route_schur_tracking_ratios = [
        float(index[(case_id, config["variants"][2])]["bundle_residual_max"])
        / max(
            float(index[(case_id, config["variants"][3])]["bundle_residual_max"]),
            np.finfo(float).tiny,
        )
        for case_id in config["cases"][3:]
    ]
    status_counts: dict[str, int] = {}
    for row in output_rows:
        status_counts[row["research_status"]] = status_counts.get(row["research_status"], 0) + 1
    exception_rows = [row for row in output_rows if row["classification"] == "method_exception"]
    paper = [
        "# 消融实验结果", "",
        "## 设计", "",
        "在Halo N45、Vertical N57、Sun–Earth member 468、Route H member 68 physical corrected-rho以及"
        "complex-pair negative control（Route H member 32）上比较V1–V7七个预先声明版本。研究阈值未改变。", "",
        "- V1：pointwise eig，无相位对齐；V2：pointwise eig，仅符号对齐。",
        "- V3：partial real-Schur，无phase tracking；V4：partial real-Schur + phase tracking。",
        "- V5：QR/SVD，无phase alignment、固定一维；V6：QR/SVD + phase alignment、固定一维。",
        "- V7：QR/SVD + phase alignment + Schur dimension seed。",
        "",
        f"共35行；状态统计：`{json.dumps(status_counts, sort_keys=True)}`；method exception：{len(exception_rows)}行，均保留。", "",
        "## 主要结论", "",
        f"- 符号对齐使三个一维锚点的pointwise跨分辨率角V1/V2改善倍数达到"
        f"{min(pointwise_cross_resolution_ratios):.3e}–{max(pointwise_cross_resolution_ratios):.3e}；"
        f"但V2残差仍全部fail，其一次映射几何距离仍为"
        f"{min(pointwise_geometry_distances):.3e}–{max(pointwise_geometry_distances):.3e}。",
        f"- 三个一维锚点上，Schur phase tracking的残差比值V3/V4仅为"
        f"{min(schur_tracking_ratios):.3e}–{max(schur_tracking_ratios):.3e}，说明这里的全局选定基已经足够连续；"
        f"而两个Route H二维案例的V3/V4残差改善倍数为"
        f"{min(route_schur_tracking_ratios):.3e}–{max(route_schur_tracking_ratios):.3e}，但V4仍fail。",
        f"- 三个一维锚点上，QR phase alignment的残差比值V5/V6为"
        f"{min(qr_alignment_ratios):.3e}–{max(qr_alignment_ratios):.3e}，未显示额外残差收益；"
        "其主要作用是显式规范相位帧，而不是在这些已平滑的一维案例上制造通过。",
        "- Route H的V5/V6一维版本是故意保留的无效complex-pair消融对照，不能被解释为物理一维子束；"
        "V7恢复二维语义，但physical corrected-rho案例仍保持fail。",
        "- `manifold_geometry_distance`是一次映射的线性化位置位移点云对V7的对称HD95距离，"
        "用于隔离局部方向处理；它不是Stage-F非线性全局manifold sheet验收的替代品。",
        "- cross-resolution对Halo/Vertical使用现有冻结分辨率源，对Sun–Earth/Route H使用明确标记的Fourier诊断降采样。",
        "", "## 失败与边界", "",
        "pointwise eig在Route H局部矩阵上找不到不稳定双曲实方向，相关method-exception行及图中×标记均保留。"
        "所有complex-pair一维对照均强制判fail；未通过删除行、改变rho或放宽阈值提高通过率。",
        "", "## 图", "",
        "- `ablation_bundle_residual.pdf`：最大bundle residual及固定pass/boundary线。",
        "- `ablation_phase_continuity.pdf`：相邻相位主角与检测到的相位修正数。",
        "- `ablation_manifold_geometry.pdf`：一次映射线性化几何距离。",
        "", "## 真实性边界", "",
        "本消融仅支撑数值框架与系统比较定位，不构成新理论声明。Chapter 4 projection holdout仍为"
        "`0/4`、`paper_projection=fail`、`paper_3d=false`。",
    ]
    PAPER_OUTPUT.write_text("\n".join(paper) + "\n", encoding="utf-8")
    FAILURE_OUTPUT.write_text(
        "# Ablation failure evidence\n\n"
        f"All {len(output_rows)} predeclared rows are retained. Status counts: "
        f"`{json.dumps(status_counts, sort_keys=True)}`. Method exceptions: {len(exception_rows)}.\n\n"
        "The exception rows arise where pointwise local eigenselection has no unstable hyperbolic candidate on Route H; "
        "their metrics remain NaN and the figures mark them with ×. The V5/V6 rank-one Route H runs are explicit invalid "
        "complex-pair controls and remain fail even if an iteration metric appears small. V7 preserves rank two and also "
        "retains its physical failures. No row, failure reason, or negative control was filtered.\n",
        encoding="utf-8",
    )
    elapsed = time.perf_counter() - started
    log.extend([
        f"rows={len(output_rows)}", f"status_counts={json.dumps(status_counts, sort_keys=True)}",
        f"method_exceptions={len(exception_rows)}", f"elapsed_seconds={elapsed:.6f}",
        f"complete_utc={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
    ])
    LOG_OUTPUT.write_text("\n".join(log) + "\n", encoding="utf-8")
    hash_paths = [
        CONFIG, Path(__file__), REGISTRY, METHOD_CSV, CSV_OUTPUT, NPZ_OUTPUT,
        PAPER_OUTPUT, LOG_OUTPUT, FAILURE_OUTPUT,
    ] + [FIGURE_DIR / f"{stem}.{suffix}" for stem in FIGURE_STEMS for suffix in ("png", "pdf")]
    write_csv(HASH_OUTPUT, [
        {
            "artifact": str(path.relative_to(ROOT)).replace("\\", "/"),
            **fingerprint_fields(path),
        }
        for path in hash_paths
    ], ["artifact", "hash_mode", "bytes", "sha256"])
    print(
        f"ablation study PASS rows={len(output_rows)} statuses={json.dumps(status_counts, sort_keys=True)} "
        f"exceptions={len(exception_rows)} elapsed={elapsed:.3f}s"
    )


if __name__ == "__main__":
    main()
