"""Audit the fixed-time full-torus sources for Figures 4.5 and 4.6."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import sys
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.torus_stability import (  # noqa: E402
    CorrectedTorusManifoldSnapshots,
    corrected_l1_constant_energy_vertical_unstable_manifold_snapshots,
)


SNAPSHOTS_DAYS = (8.05, 10.08, 11.77, 13.46)
PHASE_SAMPLES = 121
EXPECTED_CURVE_SAMPLES = 33
PERTURBATION_SCALE = 4.5e-7
MAX_STEP = 0.01

SNAPSHOT_TIME_ERROR_LIMIT_DAYS = 1.0e-10
SOURCE_RESIDUAL_LIMIT = 1.0e-8
DETERMINANT_ERROR_LIMIT = 5.0e-9
RELATIVE_IMAGINARY_LIMIT = 1.0e-10
SOURCE_JACOBI_SPAN_LIMIT = 1.0e-6
JACOBI_DRIFT_LIMIT = 1.0e-10
LOCAL_LINEAR_REFERENCE_MULTIPLIER = 100.0
LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT = 1.0e-3
BATCHED_INDEPENDENT_ERROR_LIMIT = 1.0e-9


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _exact_indices(grid: np.ndarray, requested: np.ndarray) -> np.ndarray:
    indices = np.searchsorted(grid, requested)
    if np.any(indices >= grid.size):
        raise RuntimeError("requested comparison time is outside the stored grid")
    if float(np.max(np.abs(grid[indices] - requested), initial=0.0)) > 1.0e-12:
        raise RuntimeError("requested comparison time is missing from the stored grid")
    return indices


def _representative_independent_comparison(
    snapshots: CorrectedTorusManifoldSnapshots,
    mu: float,
) -> dict[str, np.ndarray | int]:
    """Compare the batched propagation with one predeclared central curve node."""

    curve_samples = snapshots.snapshot_states.shape[2]
    representative_index = curve_samples // 2
    snapshot_evaluation_times = np.concatenate(
        [elapsed + snapshots.phase_times for elapsed in snapshots.snapshot_times]
    )
    comparison_times = np.unique(
        np.r_[snapshots.history_times, snapshot_evaluation_times]
    )
    history_indices = _exact_indices(comparison_times, snapshots.history_times)
    snapshot_indices = _exact_indices(
        comparison_times,
        snapshot_evaluation_times,
    ).reshape(snapshots.snapshot_times.size, snapshots.phase_times.size)

    batched_states = np.full((comparison_times.size, 6), np.nan, dtype=float)
    batched_states[history_indices] = snapshots.history_states[
        :, representative_index, :
    ]
    for panel_index, indices in enumerate(snapshot_indices):
        batched_states[indices] = snapshots.snapshot_states[
            panel_index, :, representative_index, :
        ]
    if not np.all(np.isfinite(batched_states)):
        raise RuntimeError("the representative batched-state comparison grid is incomplete")

    initial_state = (
        snapshots.dg.correction.corrected_states[representative_index]
        + snapshots.perturbation_sign
        * snapshots.perturbation_scale
        * snapshots.perturbation_directions[representative_index]
    )
    independent = integrate_cr3bp(
        initial_state,
        (0.0, float(comparison_times[-1])),
        mu,
        t_eval=comparison_times,
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=MAX_STEP,
    )
    if not independent.success:
        raise RuntimeError(independent.message)
    independent_states = independent.y.T
    absolute_errors = np.abs(batched_states - independent_states)

    panel_max_errors = np.empty(snapshots.snapshot_times.size, dtype=float)
    for panel_index, elapsed in enumerate(snapshots.snapshot_times):
        history_stop = int(
            np.searchsorted(snapshots.history_times, elapsed, side="right")
        )
        panel_indices = np.unique(
            np.r_[history_indices[:history_stop], snapshot_indices[panel_index]]
        )
        panel_max_errors[panel_index] = float(
            np.max(absolute_errors[panel_indices])
        )

    return {
        "representative_curve_index": representative_index,
        "comparison_times": comparison_times,
        "history_indices": history_indices,
        "snapshot_indices": snapshot_indices,
        "batched_states": batched_states,
        "independent_states": independent_states,
        "absolute_errors": absolute_errors,
        "panel_max_errors": panel_max_errors,
    }


def _xyz_range(states: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    positions = np.asarray(states)[..., :3].reshape(-1, 3)
    return np.min(positions, axis=0), np.max(positions, axis=0)


def _combined_jacobi_drift_by_curve(
    snapshots: CorrectedTorusManifoldSnapshots,
    panel_index: int,
    mu: float,
) -> float:
    elapsed = float(snapshots.snapshot_times[panel_index])
    history_stop = int(
        np.searchsorted(snapshots.history_times, elapsed, side="right")
    )
    combined = np.concatenate(
        [
            snapshots.history_states[:history_stop],
            snapshots.snapshot_states[panel_index],
        ],
        axis=0,
    )
    jacobi = jacobi_constant(combined.reshape(-1, 6), mu).reshape(
        combined.shape[:2]
    )
    return float(np.max(np.ptp(jacobi, axis=0)))


def _branch_is_finite(snapshots: CorrectedTorusManifoldSnapshots) -> bool:
    arrays = (
        snapshots.dg.correction.corrected_states,
        snapshots.dg.correction.final_residual_norms,
        snapshots.phase_times,
        snapshots.history_times,
        snapshots.base_torus_states,
        snapshots.base_history_states,
        snapshots.history_states,
        snapshots.base_snapshot_states,
        snapshots.snapshot_states,
        snapshots.perturbation_directions,
        snapshots.linear_history_state_separation_norms,
        snapshots.linear_snapshot_state_separation_norms,
        snapshots.linear_history_position_separation_norms,
        snapshots.linear_snapshot_position_separation_norms,
    )
    return all(np.all(np.isfinite(values)) for values in arrays)


def _branch_metrics(
    *,
    figure_id: str,
    branch_name: str,
    snapshots: CorrectedTorusManifoldSnapshots,
    system: Any,
) -> tuple[list[dict[str, object]], dict[str, np.ndarray | int | bool | float]]:
    source_states = snapshots.dg.correction.corrected_states
    source_jacobi = jacobi_constant(source_states, system.mu)
    source_residual = float(
        np.max(snapshots.dg.correction.final_residual_norms)
    )
    determinant_error = float(abs(snapshots.dg.determinant - 1.0))
    eigenvalue_abs = float(abs(snapshots.eigenvalue))
    relative_imaginary = float(abs(snapshots.eigenvalue.imag) / eigenvalue_abs)
    source_jacobi_span = float(np.ptp(source_jacobi))
    representative = _representative_independent_comparison(
        snapshots,
        system.mu,
    )
    representative_errors = np.asarray(representative["panel_max_errors"])
    finite = _branch_is_finite(snapshots) and all(
        np.all(np.isfinite(np.asarray(representative[key])))
        for key in (
            "comparison_times",
            "batched_states",
            "independent_states",
            "absolute_errors",
            "panel_max_errors",
        )
    )

    snapshot_minima = np.empty((snapshots.snapshot_times.size, 3), dtype=float)
    snapshot_maxima = np.empty_like(snapshot_minima)
    history_minima = np.empty_like(snapshot_minima)
    history_maxima = np.empty_like(snapshot_minima)
    jacobi_drifts = np.empty(snapshots.snapshot_times.size, dtype=float)
    measured_growth = np.empty(snapshots.snapshot_times.size, dtype=float)
    expected_growth = np.empty_like(measured_growth)
    growth_ratios = np.empty_like(measured_growth)
    initial_curve_separation = snapshots.history_state_separation_norms[0]
    initial_mean_separation = float(np.mean(initial_curve_separation))
    local_linear_mask = (
        snapshots.linear_history_state_separation_norms
        <= LOCAL_LINEAR_REFERENCE_MULTIPLIER * snapshots.perturbation_scale
    )
    local_linearization_sample_count = int(np.count_nonzero(local_linear_mask))
    local_linearization_max_relative_error = float(
        np.max(
            np.abs(snapshots.history_linearization_ratios[local_linear_mask] - 1.0)
        )
    )
    local_linearization_pass = bool(
        local_linearization_sample_count >= snapshots.snapshot_states.shape[2]
        and local_linearization_max_relative_error
        <= LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT
    )

    for panel_index, elapsed in enumerate(snapshots.snapshot_times):
        snapshot_minima[panel_index], snapshot_maxima[panel_index] = _xyz_range(
            snapshots.snapshot_states[panel_index]
        )
        history_stop = int(
            np.searchsorted(snapshots.history_times, elapsed, side="right")
        )
        history_minima[panel_index], history_maxima[panel_index] = _xyz_range(
            snapshots.history_states[:history_stop]
        )
        jacobi_drifts[panel_index] = _combined_jacobi_drift_by_curve(
            snapshots,
            panel_index,
            system.mu,
        )
        measured_growth[panel_index] = float(
            np.mean(snapshots.snapshot_state_separation_norms[panel_index])
            / initial_mean_separation
        )
        expected_growth[panel_index] = float(
            np.mean(snapshots.linear_snapshot_state_separation_norms[panel_index])
            / initial_mean_separation
        )
        expected_separations = (
            snapshots.linear_snapshot_state_separation_norms[panel_index]
        )
        growth_ratios[panel_index] = float(
            np.mean(
                snapshots.snapshot_state_separation_norms[panel_index]
                / expected_separations
            )
        )

    if figure_id == "4.5":
        endpoint_gate = bool(snapshot_maxima[-1, 0] >= 1.15)
        monotonic_gate = bool(np.all(np.diff(snapshot_maxima[:, 0]) >= -1.0e-12))
        configuration_definition = (
            "final snapshot_x_max >= 1.15 and x_max is nondecreasing"
        )
    elif figure_id == "4.6":
        endpoint_gate = bool(snapshot_minima[-1, 0] <= 0.30)
        monotonic_gate = bool(np.all(np.diff(snapshot_minima[:, 0]) <= 1.0e-12))
        configuration_definition = (
            "final snapshot_x_min <= 0.30 and x_min is nonincreasing"
        )
    else:
        raise ValueError(f"unsupported vertical-manifold figure {figure_id}")
    configuration_reach_acceptance = endpoint_gate and monotonic_gate

    rows: list[dict[str, object]] = []
    for panel_index, requested_days in enumerate(SNAPSHOTS_DAYS):
        actual_days = float(
            snapshots.snapshot_times[panel_index] * system.time_unit_days
        )
        time_error_days = actual_days - requested_days
        history_stop = int(
            np.searchsorted(
                snapshots.history_times,
                snapshots.snapshot_times[panel_index],
                side="right",
            )
        )
        numeric_gates = {
            "snapshot_time_gate": abs(time_error_days)
            <= SNAPSHOT_TIME_ERROR_LIMIT_DAYS,
            "source_residual_gate": source_residual <= SOURCE_RESIDUAL_LIMIT,
            "determinant_gate": determinant_error <= DETERMINANT_ERROR_LIMIT,
            "relative_imaginary_gate": relative_imaginary
            <= RELATIVE_IMAGINARY_LIMIT,
            "source_jacobi_span_gate": source_jacobi_span
            <= SOURCE_JACOBI_SPAN_LIMIT,
            "jacobi_drift_gate": jacobi_drifts[panel_index]
            <= JACOBI_DRIFT_LIMIT,
            "local_linearization_gate": local_linearization_pass,
            "batched_independent_gate": representative_errors[panel_index]
            <= BATCHED_INDEPENDENT_ERROR_LIMIT,
            "shape_gate": (
                snapshots.snapshot_times.size == len(SNAPSHOTS_DAYS)
                and snapshots.phase_times.size >= PHASE_SAMPLES
                and snapshots.snapshot_states.shape[2]
                == EXPECTED_CURVE_SAMPLES
            ),
            "finite_gate": finite,
            "no_proxy_gate": True,
        }
        numerical_acceptance = all(numeric_gates.values())
        overall_acceptance = numerical_acceptance and configuration_reach_acceptance
        pointwise_ratios = snapshots.snapshot_linearization_ratios[panel_index]
        row: dict[str, object] = {
            "figure_id": figure_id,
            "panel_index": panel_index + 1,
            "branch": branch_name,
            "requested_snapshot_days": requested_days,
            "actual_snapshot_days": actual_days,
            "snapshot_time_error_days": time_error_days,
            "snapshot_count": int(snapshots.snapshot_times.size),
            "phase_samples": int(snapshots.phase_times.size),
            "curve_samples": int(snapshots.snapshot_states.shape[2]),
            "fixed_time_surface_points": int(
                snapshots.phase_times.size * snapshots.snapshot_states.shape[2]
            ),
            "history_samples_through_panel": history_stop,
            "source_mapping_time_days": float(
                snapshots.dg.mapping_time * system.time_unit_days
            ),
            "perturbation_scale": float(snapshots.perturbation_scale),
            "source_curve_residual": source_residual,
            "dg_determinant": float(snapshots.dg.determinant),
            "determinant_error_from_one": determinant_error,
            "selected_eigenvalue_real": float(snapshots.eigenvalue.real),
            "selected_eigenvalue_imag": float(snapshots.eigenvalue.imag),
            "selected_eigenvalue_abs": eigenvalue_abs,
            "selected_eigenvalue_relative_imaginary": relative_imaginary,
            "source_curve_energy_span": source_jacobi_span,
            "source_jacobi_span": source_jacobi_span,
            "initial_mean_separation_nd": initial_mean_separation,
            "snapshot_mean_separation_nd": float(
                np.mean(
                    snapshots.snapshot_state_separation_norms[panel_index]
                )
            ),
            "measured_growth": measured_growth[panel_index],
            "expected_growth": expected_growth[panel_index],
            "growth_ratio": growth_ratios[panel_index],
            "growth_ratio_min": float(np.min(pointwise_ratios)),
            "growth_ratio_max": float(np.max(pointwise_ratios)),
            "linear_reference_method": "base_trajectory_STM_first_order",
            "far_field_linearization_status": "diagnostic_only",
            "local_linearization_definition": (
                "history linear STM separation <= 100*epsilon"
            ),
            "local_linearization_sample_count": local_linearization_sample_count,
            "local_linearization_max_relative_error": (
                local_linearization_max_relative_error
            ),
            "jacobi_drift_max": jacobi_drifts[panel_index],
            "representative_curve_index": int(
                representative["representative_curve_index"]
            ),
            "batched_vs_independent_state_max_abs_error": representative_errors[
                panel_index
            ],
            "snapshot_x_min": snapshot_minima[panel_index, 0],
            "snapshot_x_max": snapshot_maxima[panel_index, 0],
            "snapshot_y_min": snapshot_minima[panel_index, 1],
            "snapshot_y_max": snapshot_maxima[panel_index, 1],
            "snapshot_z_min": snapshot_minima[panel_index, 2],
            "snapshot_z_max": snapshot_maxima[panel_index, 2],
            "history_x_min": history_minima[panel_index, 0],
            "history_x_max": history_maxima[panel_index, 0],
            "history_y_min": history_minima[panel_index, 1],
            "history_y_max": history_maxima[panel_index, 1],
            "history_z_min": history_minima[panel_index, 2],
            "history_z_max": history_maxima[panel_index, 2],
            "all_finite": str(finite).lower(),
            "uses_proxy_background": "false",
            **{
                name: "pass" if passed else "fail"
                for name, passed in numeric_gates.items()
            },
            "numerical_acceptance": "pass" if numerical_acceptance else "fail",
            "configuration_reach_definition": configuration_definition,
            "configuration_endpoint_gate": "pass" if endpoint_gate else "fail",
            "configuration_monotonic_gate": "pass" if monotonic_gate else "fail",
            "configuration_reach_acceptance": (
                "pass" if configuration_reach_acceptance else "fail"
            ),
            "overall_acceptance": "pass" if overall_acceptance else "fail",
            "overall_acceptance_scope": (
                "project_numerical_and_configuration_only"
            ),
            "paper_projection_acceptance": "not_run",
            "paper_3d_equivalence": "false",
            "epsilon_selection_status": (
                "project_visualization_parameter_uncalibrated"
            ),
            "paper_geometry_boundary": (
                "configuration reach is epsilon-dependent and locked-camera "
                "projection acceptance is not run; paper 3D equivalence is false"
            ),
            "acceptance": "pass" if overall_acceptance else "fail",
        }
        rows.append(row)

    archive: dict[str, np.ndarray | int | bool | float] = {
        "snapshot_minima": snapshot_minima,
        "snapshot_maxima": snapshot_maxima,
        "history_minima": history_minima,
        "history_maxima": history_maxima,
        "jacobi_drift_by_panel": jacobi_drifts,
        "measured_growth_by_panel": measured_growth,
        "expected_growth_by_panel": expected_growth,
        "growth_ratio_by_panel": growth_ratios,
        "representative_error_by_panel": representative_errors,
        "configuration_endpoint_gate": endpoint_gate,
        "configuration_monotonic_gate": monotonic_gate,
        "configuration_reach_acceptance": configuration_reach_acceptance,
        "local_linear_mask": local_linear_mask,
        "local_linearization_sample_count": local_linearization_sample_count,
        "local_linearization_max_relative_error": (
            local_linearization_max_relative_error
        ),
        "source_residual": source_residual,
        "determinant_error_from_one": determinant_error,
        "selected_eigenvalue_relative_imaginary": relative_imaginary,
        "source_jacobi_span": source_jacobi_span,
        **representative,
    }
    return rows, archive


def _archive_arrays(
    prefix: str,
    snapshots: CorrectedTorusManifoldSnapshots,
    metrics: dict[str, np.ndarray | int | bool | float],
) -> dict[str, np.ndarray]:
    arrays = {
        f"{prefix}_source_states": snapshots.dg.correction.corrected_states,
        f"{prefix}_source_residual_norms": snapshots.dg.correction.final_residual_norms,
        f"{prefix}_source_jacobi": jacobi_constant(
            snapshots.dg.correction.corrected_states,
            SYSTEMS["earth_moon"].mu,
        ),
        f"{prefix}_dg_eigenvalues": snapshots.dg.eigenvalues,
        f"{prefix}_perturbation_directions": snapshots.perturbation_directions,
        f"{prefix}_phase_times_nd": snapshots.phase_times,
        f"{prefix}_history_times_nd": snapshots.history_times,
        f"{prefix}_snapshot_times_nd": snapshots.snapshot_times,
        f"{prefix}_base_torus_states": snapshots.base_torus_states,
        f"{prefix}_base_history_states": snapshots.base_history_states,
        f"{prefix}_history_states": snapshots.history_states,
        f"{prefix}_base_snapshot_states": snapshots.base_snapshot_states,
        f"{prefix}_snapshot_states": snapshots.snapshot_states,
        f"{prefix}_linear_history_state_separation_norms": snapshots.linear_history_state_separation_norms,
        f"{prefix}_linear_snapshot_state_separation_norms": snapshots.linear_snapshot_state_separation_norms,
        f"{prefix}_linear_history_position_separation_norms": snapshots.linear_history_position_separation_norms,
        f"{prefix}_linear_snapshot_position_separation_norms": snapshots.linear_snapshot_position_separation_norms,
    }
    for name, values in metrics.items():
        arrays[f"{prefix}_{name}"] = np.asarray(values)
    return arrays


def main() -> None:
    system = SYSTEMS["earth_moon"]
    plus_x, minus_x = (
        corrected_l1_constant_energy_vertical_unstable_manifold_snapshots(
            system.mu,
            time_unit_days=system.time_unit_days,
            snapshot_times_days=SNAPSHOTS_DAYS,
            phase_samples=PHASE_SAMPLES,
            perturbation_scale=PERTURBATION_SCALE,
            max_step=MAX_STEP,
        )
    )

    rows: list[dict[str, object]] = []
    archives: dict[str, np.ndarray] = {}
    for figure_id, branch_name, prefix, snapshots in (
        ("4.5", "plus_x", "plus_x", plus_x),
        ("4.6", "minus_x", "minus_x", minus_x),
    ):
        branch_rows, branch_archive = _branch_metrics(
            figure_id=figure_id,
            branch_name=branch_name,
            snapshots=snapshots,
            system=system,
        )
        rows.extend(branch_rows)
        archives.update(_archive_arrays(prefix, snapshots, branch_archive))

    data = (
        ROOT
        / "data"
        / "computed"
        / "chapter4_fig45_fig48_vertical_manifold_audit.csv"
    )
    archive_path = (
        ROOT
        / "data"
        / "computed"
        / "chapter4_fig45_fig48_vertical_manifold_audit.npz"
    )
    np.savez_compressed(
        archive_path,
        schema_version=np.asarray("fixed_time_vertical_manifold_audit_v2"),
        snapshot_times_days=np.asarray(SNAPSHOTS_DAYS),
        time_unit_days=np.asarray(system.time_unit_days),
        phase_samples=np.asarray(PHASE_SAMPLES),
        expected_curve_samples=np.asarray(EXPECTED_CURVE_SAMPLES),
        perturbation_scale=np.asarray(PERTURBATION_SCALE),
        snapshot_time_error_limit_days=np.asarray(
            SNAPSHOT_TIME_ERROR_LIMIT_DAYS
        ),
        source_residual_limit=np.asarray(SOURCE_RESIDUAL_LIMIT),
        determinant_error_limit=np.asarray(DETERMINANT_ERROR_LIMIT),
        relative_imaginary_limit=np.asarray(RELATIVE_IMAGINARY_LIMIT),
        source_jacobi_span_limit=np.asarray(SOURCE_JACOBI_SPAN_LIMIT),
        jacobi_drift_limit=np.asarray(JACOBI_DRIFT_LIMIT),
        local_linear_reference_multiplier=np.asarray(
            LOCAL_LINEAR_REFERENCE_MULTIPLIER
        ),
        local_linearization_relative_error_limit=np.asarray(
            LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT
        ),
        batched_independent_error_limit=np.asarray(
            BATCHED_INDEPENDENT_ERROR_LIMIT
        ),
        paper_projection_acceptance=np.asarray("not_run"),
        paper_3d_equivalence=np.asarray(False),
        epsilon_selection_status=np.asarray(
            "project_visualization_parameter_uncalibrated"
        ),
        **archives,
    )
    provenance = {
        "artifact_fingerprint_version": "1",
        "npz_schema_version": "fixed_time_vertical_manifold_audit_v2",
        "npz_sha256": _sha256(archive_path),
        "generator_sha256": _sha256(Path(__file__).resolve()),
        "core_torus_stability_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "torus_stability.py"
        ),
    }
    for row in rows:
        row.update(provenance)
    with data.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed = sum(row["acceptance"] == "pass" for row in rows)
    plus_rows = [row for row in rows if row["figure_id"] == "4.5"]
    minus_rows = [row for row in rows if row["figure_id"] == "4.6"]
    report = ROOT / "docs" / "chapter4_fig45_fig48_vertical_manifold_audit.md"
    report.write_text(
        f"""# Chapter 4 Figures 4.5-4.6 fixed-time quasi-vertical manifold audit

- Audited snapshot rows: `{len(rows)}`
- Accepted internal-dynamics rows: `{passed}/{len(rows)}`
- Fixed-time construction: `K=4`, `M={PHASE_SAMPLES}`, `N={EXPECTED_CURVE_SAMPLES}`
- Shared perturbation scale: `{PERTURBATION_SCALE:.6e}`
- Requested paper times: `{SNAPSHOTS_DAYS}` days
- Maximum source residual: `{max(float(row['source_curve_residual']) for row in rows):.6e}`
- DG determinant error: `{max(float(row['determinant_error_from_one']) for row in rows):.6e}`
- Selected-eigenvalue relative imaginary part: `{max(float(row['selected_eigenvalue_relative_imaginary']) for row in rows):.6e}`
- Source Jacobi span: `{max(float(row['source_jacobi_span']) for row in rows):.6e}`
- Maximum per-curve combined history/snapshot Jacobi drift: `{max(float(row['jacobi_drift_max']) for row in rows):.6e}`
- Far-field nonlinear/STM ratio range (diagnostic only): `{min(float(row['growth_ratio_min']) for row in rows):.6f}` to `{max(float(row['growth_ratio_max']) for row in rows):.6f}`
- Local STM maximum relative error: `{max(float(row['local_linearization_max_relative_error']) for row in rows):.6e}`
- Batched-vs-independent representative-state error: `{max(float(row['batched_vs_independent_state_max_abs_error']) for row in rows):.6e}`
- Figure 4.5 snapshot x-max sequence: `{[float(row['snapshot_x_max']) for row in plus_rows]}`
- Figure 4.6 snapshot x-min sequence: `{[float(row['snapshot_x_min']) for row in minus_rows]}`
- Figure 4.5 configuration-reach diagnostic: `{plus_rows[0]['configuration_reach_acceptance']}`
- Figure 4.6 configuration-reach diagnostic: `{minus_rows[0]['configuration_reach_acceptance']}`
- Proxy background: `false`
- Paper projection acceptance: `not_run`
- Paper 3D equivalence: `false`
- Epsilon selection status: `project_visualization_parameter_uncalibrated`
- Raw audit archive: `data/computed/{archive_path.name}`

Each red surface is the full perturbed torus over one mapping-time phase window
at the paper's fixed elapsed time. The black-trajectory history is stored and
audited separately; it is not reused as the red surface. The numerical gate
requires snapshot-time error <= `{SNAPSHOT_TIME_ERROR_LIMIT_DAYS:.1e}` day,
source residual <= `{SOURCE_RESIDUAL_LIMIT:.1e}`, determinant error <=
`{DETERMINANT_ERROR_LIMIT:.1e}`, selected-eigenvalue relative imaginary part <=
`{RELATIVE_IMAGINARY_LIMIT:.1e}`, source Jacobi span <=
`{SOURCE_JACOBI_SPAN_LIMIT:.1e}`, per-curve combined history/snapshot Jacobi
drift <= `{JACOBI_DRIFT_LIMIT:.1e}`, and the local-history nonlinear separation
must agree with `epsilon*||Phi(t,0)d||` to relative error <=
`{LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT:.1e}` while the predicted state
separation is <= `{LOCAL_LINEAR_REFERENCE_MULTIPLIER:.0f}*epsilon`. Far-field
nonlinear/STM ratios are diagnostic only. The representative batched-vs-independent
state error must be <= `{BATCHED_INDEPENDENT_ERROR_LIMIT:.1e}`, with finite arrays, exact
`K=4`, `M>={PHASE_SAMPLES}`, `N={EXPECTED_CURVE_SAMPLES}`, and no proxy layer.

The configuration-reach diagnostic requires Figure 4.5's x-max sequence to be
nondecreasing and end at or beyond `1.15`, while Figure 4.6's x-min sequence
must be nonincreasing and end at or below `0.30`. This check describes only the
reach of the project's uncalibrated `epsilon={PERTURBATION_SCALE:.1e}` rendering
configuration; it is not paper-level physical acceptance. A locked-camera
projection acceptance audit has not yet been run, so paper-facing 3D equivalence
is false and epsilon calibration remains pending.

## Figure 4.8 follow-up

Figure 4.8 is not included in this acceptance count. It still requires migration
to the audited fixed-time Earthward branch, followed by a matched periodic-
vertical comparison and locked-camera projection-space audit.
""",
        encoding="utf-8",
    )
    print(data)
    print(archive_path)
    print(report)
    print(f"accepted={passed}/{len(rows)}")


if __name__ == "__main__":
    main()
