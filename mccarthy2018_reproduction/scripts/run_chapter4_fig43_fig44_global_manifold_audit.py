"""Audit the fixed-time full-torus manifolds for Figures 4.3 and 4.4."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.chapter4_reproduction_lock import (  # noqa: E402
    load_chapter4_reproduction_lock,
)
from qp_orbits.cr3bp import integrate_cr3bp, jacobi_constant  # noqa: E402
from qp_orbits.torus_stability import (  # noqa: E402
    corrected_l1_constant_energy_halo_unstable_manifold_snapshots,
)


DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CSV_PATH = DATA / "chapter4_fig43_fig44_global_manifold_audit.csv"
NPZ_PATH = DATA / "chapter4_fig43_fig44_global_manifold_audit.npz"
DOC_PATH = DOCS / "chapter4_fig43_fig44_global_manifold_audit.md"

SNAPSHOTS_DAYS = (7.79, 9.75, 11.39, 13.02)
CURVE_SAMPLES = 9
PHASE_SAMPLES = 121
HISTORY_SAMPLES = 161
REPRODUCTION_LOCK = load_chapter4_reproduction_lock(ROOT)
PERTURBATION_SCALE = REPRODUCTION_LOCK.epsilon_by_family["halo"]
MAX_STEP = 0.01
REPRESENTATIVE_CURVE_INDEX = CURVE_SAMPLES // 2

TIME_ERROR_LIMIT_DAYS = 1.0e-10
SOURCE_RESIDUAL_LIMIT = 1.0e-8
DG_DETERMINANT_ERROR_LIMIT = 5.0e-9
EIGEN_RELATIVE_IMAGINARY_LIMIT = 1.0e-10
SOURCE_JACOBI_SPAN_LIMIT = 1.0e-6
JACOBI_DRIFT_LIMIT = 1.0e-10
LOCAL_LINEAR_REFERENCE_MULTIPLIER = 100.0
LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT = 1.0e-3
INDEPENDENT_ERROR_LIMIT = 1.0e-9


def _indices_for_times(evaluation_times: np.ndarray, requested_times: np.ndarray) -> np.ndarray:
    """Locate times deliberately inserted into a sorted evaluation grid."""

    indices = np.searchsorted(evaluation_times, requested_times)
    if np.any(indices >= evaluation_times.size):
        raise RuntimeError("Independent audit evaluation time is missing")
    if float(np.max(np.abs(evaluation_times[indices] - requested_times), initial=0.0)) > 1.0e-12:
        raise RuntimeError("Independent audit evaluation time is missing")
    return indices


def _independent_representative_audit(snapshots, mu: float) -> dict[str, np.ndarray]:
    """Reintegrate one curve node outside the batched propagation path."""

    absolute_snapshot_times = np.concatenate(
        [elapsed + snapshots.phase_times for elapsed in snapshots.snapshot_times]
    )
    evaluation_times = np.unique(
        np.r_[snapshots.history_times, absolute_snapshot_times]
    )
    solution = integrate_cr3bp(
        snapshots.history_states[0, REPRESENTATIVE_CURVE_INDEX],
        (0.0, float(evaluation_times[-1])),
        mu,
        t_eval=evaluation_times,
        max_step=MAX_STEP,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    independent_states = solution.y.T
    history_indices = _indices_for_times(evaluation_times, snapshots.history_times)
    snapshot_indices = _indices_for_times(
        evaluation_times,
        absolute_snapshot_times,
    ).reshape(snapshots.snapshot_times.size, snapshots.phase_times.size)
    independent_history = independent_states[history_indices]
    independent_snapshots = independent_states[snapshot_indices]
    batched_history = snapshots.history_states[:, REPRESENTATIVE_CURVE_INDEX]
    batched_snapshots = snapshots.snapshot_states[:, :, REPRESENTATIVE_CURVE_INDEX]
    return {
        "evaluation_times": evaluation_times,
        "independent_states": independent_states,
        "independent_history": independent_history,
        "independent_snapshots": independent_snapshots,
        "batched_history": batched_history,
        "batched_snapshots": batched_snapshots,
        "history_max_abs_error": np.max(
            np.abs(batched_history - independent_history), axis=1
        ),
        "snapshot_max_abs_error": np.max(
            np.abs(batched_snapshots - independent_snapshots), axis=(1, 2)
        ),
    }


def _combined_per_curve_jacobi_drift(snapshots, mu: float) -> np.ndarray:
    """Measure each perturbed trajectory across both stored data products."""

    history_jacobi = jacobi_constant(
        snapshots.history_states.reshape(-1, 6), mu
    ).reshape(snapshots.history_states.shape[:-1])
    snapshot_jacobi = jacobi_constant(
        snapshots.snapshot_states.reshape(-1, 6), mu
    ).reshape(snapshots.snapshot_states.shape[:-1])
    curve_count = snapshots.snapshot_states.shape[2]
    return np.asarray(
        [
            np.ptp(
                np.r_[
                    history_jacobi[:, curve_index],
                    snapshot_jacobi[:, :, curve_index].reshape(-1),
                ]
            )
            for curve_index in range(curve_count)
        ],
        dtype=float,
    )


def _xyz_range(values: np.ndarray) -> tuple[float, float, float, float, float, float]:
    points = np.asarray(values, dtype=float).reshape(-1, 3)
    return (
        float(np.min(points[:, 0])),
        float(np.max(points[:, 0])),
        float(np.min(points[:, 1])),
        float(np.max(points[:, 1])),
        float(np.min(points[:, 2])),
        float(np.max(points[:, 2])),
    )


def _csv_value(value: object) -> object:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.16g}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    system = SYSTEMS["earth_moon"]
    plus_x, minus_x = corrected_l1_constant_energy_halo_unstable_manifold_snapshots(
        system.mu,
        time_unit_days=system.time_unit_days,
        snapshot_times_days=SNAPSHOTS_DAYS,
        samples=CURVE_SAMPLES,
        phase_samples=PHASE_SAMPLES,
        history_samples=HISTORY_SAMPLES,
        perturbation_scale=PERTURBATION_SCALE,
        max_step=MAX_STEP,
    )

    branch_data: list[dict[str, object]] = []
    for figure_id, branch, snapshots in (
        ("4.3", "plus_x", plus_x),
        ("4.4", "minus_x", minus_x),
    ):
        actual_days = snapshots.snapshot_times * system.time_unit_days
        source_residual = float(np.max(snapshots.dg.correction.final_residual_norms))
        determinant_error = abs(float(snapshots.dg.determinant) - 1.0)
        eigenvalue = complex(snapshots.eigenvalue)
        relative_imaginary = abs(eigenvalue.imag) / max(1.0, abs(eigenvalue.real))
        source_jacobi = jacobi_constant(
            snapshots.dg.correction.corrected_states, system.mu
        )
        source_jacobi_span = float(np.ptp(source_jacobi))
        per_curve_jacobi_drift = _combined_per_curve_jacobi_drift(
            snapshots, system.mu
        )
        jacobi_drift_max = float(np.max(per_curve_jacobi_drift))
        independent = _independent_representative_audit(snapshots, system.mu)
        initial_separation_by_curve = snapshots.history_state_separation_norms[0]
        initial_mean_separation = float(
            np.mean(initial_separation_by_curve)
        )
        surface_ranges = np.asarray(
            [_xyz_range(surface) for surface in snapshots.snapshot_surfaces]
        )
        history_ranges = np.asarray(
            [
                _xyz_range(snapshots.history_surface_until(elapsed))
                for elapsed in snapshots.snapshot_times
            ]
        )
        if branch == "plus_x":
            configuration_metrics = surface_ranges[:, 1]
            monotonic_steps = np.r_[True, np.diff(configuration_metrics) >= -1.0e-12]
            final_reach_pass = bool(configuration_metrics[-1] >= 1.02)
            configuration_requirement = "surface_x_max nondecreasing and final >= 1.02"
        else:
            configuration_metrics = surface_ranges[:, 0]
            monotonic_steps = np.r_[True, np.diff(configuration_metrics) <= 1.0e-12]
            final_reach_pass = bool(configuration_metrics[-1] <= 0.72)
            configuration_requirement = "surface_x_min nonincreasing and final <= 0.72"
        monotonic_pass = bool(np.all(monotonic_steps))
        configuration_reach_pass = monotonic_pass and final_reach_pass

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

        finite_arrays = (
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
            source_jacobi,
            per_curve_jacobi_drift,
            surface_ranges,
            history_ranges,
            independent["independent_states"],
            np.asarray(
                [
                    source_residual,
                    determinant_error,
                    relative_imaginary,
                    source_jacobi_span,
                    jacobi_drift_max,
                ]
            ),
        )
        finite_pass = bool(all(np.all(np.isfinite(values)) for values in finite_arrays))
        shape_pass = bool(
            snapshots.snapshot_times.size == 4
            and snapshots.phase_times.size >= PHASE_SAMPLES
            and snapshots.snapshot_states.shape[2] == CURVE_SAMPLES
        )

        rows: list[dict[str, object]] = []
        pointwise_growth_ratio_panels: list[np.ndarray] = []
        for panel_index, requested_days in enumerate(SNAPSHOTS_DAYS):
            actual = float(actual_days[panel_index])
            time_error = actual - requested_days
            snapshot_mean_separation = float(
                np.mean(snapshots.snapshot_state_separation_norms[panel_index])
            )
            measured_growth = snapshot_mean_separation / initial_mean_separation
            expected_separation = (
                snapshots.linear_snapshot_state_separation_norms[panel_index]
            )
            expected_growth = float(
                np.mean(expected_separation) / initial_mean_separation
            )
            pointwise_growth_ratios = (
                snapshots.snapshot_state_separation_norms[panel_index]
                / expected_separation
            )
            pointwise_growth_ratio_panels.append(pointwise_growth_ratios)
            growth_ratio = float(np.mean(pointwise_growth_ratios))
            aggregate_growth_ratio = measured_growth / expected_growth
            history_stop = int(
                np.searchsorted(
                    snapshots.history_times,
                    snapshots.snapshot_times[panel_index],
                    side="right",
                )
            )
            independent_error = max(
                float(np.max(independent["history_max_abs_error"][:history_stop])),
                float(independent["snapshot_max_abs_error"][panel_index]),
            )
            numerical_pass = bool(
                abs(time_error) <= TIME_ERROR_LIMIT_DAYS
                and source_residual <= SOURCE_RESIDUAL_LIMIT
                and determinant_error <= DG_DETERMINANT_ERROR_LIMIT
                and relative_imaginary <= EIGEN_RELATIVE_IMAGINARY_LIMIT
                and source_jacobi_span <= SOURCE_JACOBI_SPAN_LIMIT
                and jacobi_drift_max <= JACOBI_DRIFT_LIMIT
                and local_linearization_pass
                and independent_error <= INDEPENDENT_ERROR_LIMIT
                and shape_pass
                and finite_pass
            )
            surface_range = surface_ranges[panel_index]
            history_range = history_ranges[panel_index]
            rows.append(
                {
                    "figure_id": figure_id,
                    "branch": branch,
                    "panel_index": panel_index + 1,
                    "requested_snapshot_days": requested_days,
                    "actual_snapshot_days": actual,
                    "snapshot_time_error_days": time_error,
                    "snapshot_count": snapshots.snapshot_times.size,
                    "phase_samples": snapshots.phase_times.size,
                    "curve_samples": snapshots.snapshot_states.shape[2],
                    "perturbation_scale": snapshots.perturbation_scale,
                    "source_mapping_time_days": snapshots.dg.mapping_time
                    * system.time_unit_days,
                    "source_curve_residual": source_residual,
                    "dg_determinant": snapshots.dg.determinant,
                    "dg_determinant_error_from_one": determinant_error,
                    "unstable_eigenvalue_real": eigenvalue.real,
                    "unstable_eigenvalue_imag": eigenvalue.imag,
                    "unstable_eigenvalue_relative_imaginary": relative_imaginary,
                    "source_curve_energy_span": source_jacobi_span,
                    "source_jacobi_span": source_jacobi_span,
                    "jacobi_drift_max": jacobi_drift_max,
                    "combined_history_snapshot_jacobi_drift_max": jacobi_drift_max,
                    "initial_mean_separation_nd": initial_mean_separation,
                    "snapshot_mean_separation_nd": snapshot_mean_separation,
                    "measured_growth": measured_growth,
                    "expected_growth": expected_growth,
                    "growth_ratio": growth_ratio,
                    "growth_ratio_min": float(np.min(pointwise_growth_ratios)),
                    "growth_ratio_max": float(np.max(pointwise_growth_ratios)),
                    "aggregate_growth_ratio": aggregate_growth_ratio,
                    "linear_reference_method": "base_trajectory_STM_first_order",
                    "far_field_linearization_status": "diagnostic_only",
                    "local_linearization_definition": (
                        "history linear STM separation <= 100*epsilon"
                    ),
                    "local_linearization_sample_count": (
                        local_linearization_sample_count
                    ),
                    "local_linearization_max_relative_error": (
                        local_linearization_max_relative_error
                    ),
                    "local_linearization_gate": (
                        "pass" if local_linearization_pass else "fail"
                    ),
                    "surface_x_min": surface_range[0],
                    "surface_x_max": surface_range[1],
                    "surface_y_min": surface_range[2],
                    "surface_y_max": surface_range[3],
                    "surface_z_min": surface_range[4],
                    "surface_z_max": surface_range[5],
                    "history_x_min": history_range[0],
                    "history_x_max": history_range[1],
                    "history_y_min": history_range[2],
                    "history_y_max": history_range[3],
                    "history_z_min": history_range[4],
                    "history_z_max": history_range[5],
                    "representative_curve_index": REPRESENTATIVE_CURVE_INDEX,
                    "batched_vs_independent_max_abs_error": independent_error,
                    "finite_acceptance": finite_pass,
                    "shape_acceptance": shape_pass,
                    "uses_proxy_background": False,
                    "numerical_acceptance": "pass" if numerical_pass else "fail",
                    "configuration_metric": (
                        "surface_x_max" if branch == "plus_x" else "surface_x_min"
                    ),
                    "configuration_metric_value": configuration_metrics[panel_index],
                    "configuration_monotonic_step_acceptance": (
                        "pass" if monotonic_steps[panel_index] else "fail"
                    ),
                    "configuration_monotonic_acceptance": (
                        "pass" if monotonic_pass else "fail"
                    ),
                    "configuration_final_reach_acceptance": (
                        "pass" if final_reach_pass else "fail"
                    ),
                    "configuration_reach_acceptance": (
                        "pass" if configuration_reach_pass else "fail"
                    ),
                    "configuration_reach_requirement": configuration_requirement,
                    "overall_acceptance": (
                        "pass"
                        if numerical_pass and configuration_reach_pass
                        else "fail"
                    ),
                    "overall_acceptance_scope": (
                        "project_numerical_and_configuration_only"
                    ),
                    "paper_projection_acceptance": (
                        REPRODUCTION_LOCK.paper_projection_acceptance
                    ),
                    "paper_3d_equivalence": False,
                    "epsilon_selection_status": REPRODUCTION_LOCK.epsilon_selection_status,
                    "paper_geometry_boundary": (
                        "epsilon and paper camera are development-locked, but the "
                        "programmatic frozen projection holdout passes "
                        f"{REPRODUCTION_LOCK.holdout_passes}/"
                        f"{REPRODUCTION_LOCK.holdout_rows}; "
                        f"paper projection is {REPRODUCTION_LOCK.paper_projection_acceptance} "
                        "and paper 3D equivalence is false"
                    ),
                    "projection_fit_lock_sha256": REPRODUCTION_LOCK.fit_lock_sha256,
                    "projection_holdout_sha256": REPRODUCTION_LOCK.holdout_csv_sha256,
                    "projection_holdout_run_id": REPRODUCTION_LOCK.holdout_run_id,
                    "acceptance": (
                        "pass"
                        if numerical_pass and configuration_reach_pass
                        else "fail"
                    ),
                }
            )
        branch_data.append(
            {
                "figure_id": figure_id,
                "branch": branch,
                "snapshots": snapshots,
                "rows": rows,
                "source_jacobi": source_jacobi,
                "per_curve_jacobi_drift": per_curve_jacobi_drift,
                "surface_ranges": surface_ranges,
                "history_ranges": history_ranges,
                "initial_separation_by_curve": initial_separation_by_curve,
                "pointwise_growth_ratio_panels": np.asarray(
                    pointwise_growth_ratio_panels
                ),
                "local_linear_mask": local_linear_mask,
                "independent": independent,
            }
        )

    rows = [row for branch in branch_data for row in branch["rows"]]

    npz_values: dict[str, np.ndarray] = {
        "schema_version": np.asarray(["chapter4_fig43_fig44_fixed_time_audit_v2"]),
        "figure_ids": np.asarray(["4.3", "4.4"]),
        "branches": np.asarray(["plus_x", "minus_x"]),
        "snapshot_times_days": np.asarray(SNAPSHOTS_DAYS),
        "representative_curve_index": np.asarray([REPRESENTATIVE_CURVE_INDEX]),
        "perturbation_scale": np.asarray([PERTURBATION_SCALE]),
        "paper_projection_acceptance": np.asarray(
            [REPRODUCTION_LOCK.paper_projection_acceptance]
        ),
        "paper_3d_equivalence": np.asarray([False]),
        "epsilon_selection_status": np.asarray(
            [REPRODUCTION_LOCK.epsilon_selection_status]
        ),
        "projection_fit_lock_sha256": np.asarray(
            [REPRODUCTION_LOCK.fit_lock_sha256]
        ),
        "projection_holdout_sha256": np.asarray(
            [REPRODUCTION_LOCK.holdout_csv_sha256]
        ),
        "projection_holdout_run_id": np.asarray(
            [REPRODUCTION_LOCK.holdout_run_id]
        ),
        "time_unit_days": np.asarray([system.time_unit_days]),
        "snapshot_time_error_limit_days": np.asarray([TIME_ERROR_LIMIT_DAYS]),
        "source_residual_limit": np.asarray([SOURCE_RESIDUAL_LIMIT]),
        "dg_determinant_error_limit": np.asarray([DG_DETERMINANT_ERROR_LIMIT]),
        "eigen_relative_imaginary_limit": np.asarray(
            [EIGEN_RELATIVE_IMAGINARY_LIMIT]
        ),
        "source_jacobi_span_limit": np.asarray([SOURCE_JACOBI_SPAN_LIMIT]),
        "jacobi_drift_limit": np.asarray([JACOBI_DRIFT_LIMIT]),
        "local_linear_reference_multiplier": np.asarray(
            [LOCAL_LINEAR_REFERENCE_MULTIPLIER]
        ),
        "local_linearization_relative_error_limit": np.asarray(
            [LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT]
        ),
        "independent_error_limit": np.asarray([INDEPENDENT_ERROR_LIMIT]),
    }
    for branch in branch_data:
        prefix = str(branch["branch"])
        snapshots = branch["snapshots"]
        independent = branch["independent"]
        npz_values.update(
            {
                f"{prefix}_snapshot_times_nd": snapshots.snapshot_times,
                f"{prefix}_phase_times_nd": snapshots.phase_times,
                f"{prefix}_history_times_nd": snapshots.history_times,
                f"{prefix}_base_torus_states": snapshots.base_torus_states,
                f"{prefix}_base_history_states": snapshots.base_history_states,
                f"{prefix}_history_states": snapshots.history_states,
                f"{prefix}_base_snapshot_states": snapshots.base_snapshot_states,
                f"{prefix}_snapshot_states": snapshots.snapshot_states,
                f"{prefix}_perturbation_directions": snapshots.perturbation_directions,
                f"{prefix}_linear_history_state_separation_norms": snapshots.linear_history_state_separation_norms,
                f"{prefix}_linear_snapshot_state_separation_norms": snapshots.linear_snapshot_state_separation_norms,
                f"{prefix}_linear_history_position_separation_norms": snapshots.linear_history_position_separation_norms,
                f"{prefix}_linear_snapshot_position_separation_norms": snapshots.linear_snapshot_position_separation_norms,
                f"{prefix}_source_states": snapshots.dg.correction.corrected_states,
                f"{prefix}_source_residual_norms": snapshots.dg.correction.final_residual_norms,
                f"{prefix}_dg_map_jacobian": snapshots.dg.map_jacobian,
                f"{prefix}_dg_eigenvalues": snapshots.dg.eigenvalues,
                f"{prefix}_dg_eigenvectors": snapshots.dg.eigenvectors,
                f"{prefix}_dg_mapping_time_nd": np.asarray(
                    [snapshots.dg.mapping_time]
                ),
                f"{prefix}_dg_determinant": np.asarray([snapshots.dg.determinant]),
                f"{prefix}_source_jacobi": branch["source_jacobi"],
                f"{prefix}_initial_separation_by_curve": branch[
                    "initial_separation_by_curve"
                ],
                f"{prefix}_per_curve_combined_jacobi_drift": branch[
                    "per_curve_jacobi_drift"
                ],
                f"{prefix}_surface_xyz_ranges": branch["surface_ranges"],
                f"{prefix}_history_xyz_ranges": branch["history_ranges"],
                f"{prefix}_independent_evaluation_times_nd": independent[
                    "evaluation_times"
                ],
                f"{prefix}_independent_representative_states": independent[
                    "independent_states"
                ],
                f"{prefix}_batched_representative_history_states": independent[
                    "batched_history"
                ],
                f"{prefix}_independent_representative_history_states": independent[
                    "independent_history"
                ],
                f"{prefix}_batched_representative_snapshot_states": independent[
                    "batched_snapshots"
                ],
                f"{prefix}_independent_representative_snapshot_states": independent[
                    "independent_snapshots"
                ],
                f"{prefix}_panel_growth_ratios": np.asarray(
                    [row["growth_ratio"] for row in branch["rows"]]
                ),
                f"{prefix}_pointwise_growth_ratio_panels": branch[
                    "pointwise_growth_ratio_panels"
                ],
                f"{prefix}_local_linear_mask": branch["local_linear_mask"],
                f"{prefix}_panel_batched_vs_independent_max_abs_errors": np.asarray(
                    [
                        row["batched_vs_independent_max_abs_error"]
                        for row in branch["rows"]
                    ]
                ),
            }
        )
    np.savez_compressed(NPZ_PATH, **npz_values)
    provenance = {
        "artifact_fingerprint_version": "1",
        "npz_schema_version": "chapter4_fig43_fig44_fixed_time_audit_v2",
        "npz_sha256": _sha256(NPZ_PATH),
        "generator_sha256": _sha256(Path(__file__).resolve()),
        "core_torus_stability_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "torus_stability.py"
        ),
    }
    for row in rows:
        row.update(provenance)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(
            {field: _csv_value(value) for field, value in row.items()} for row in rows
        )

    accepted = sum(row["acceptance"] == "pass" for row in rows)
    numerical_pass = all(row["numerical_acceptance"] == "pass" for row in rows)
    configuration_pass = all(
        row["configuration_reach_acceptance"] == "pass" for row in rows
    )
    table_rows = "\n".join(
        "| {figure_id} | {requested_snapshot_days:.2f} | "
        "[{surface_x_min:.6f}, {surface_x_max:.6f}] | "
        "[{surface_y_min:.6f}, {surface_y_max:.6f}] | "
        "[{surface_z_min:.6f}, {surface_z_max:.6f}] | "
        "{growth_ratio:.6f} | {batched_vs_independent_max_abs_error:.3e} | "
        "{numerical_acceptance} | {configuration_reach_acceptance} |".format(**row)
        for row in rows
    )
    DOC_PATH.write_text(
        f"""# Chapter 4 Figures 4.3-4.4 fixed-time global manifold audit

- Audited panel rows: `{len(rows)}`
- Accepted panel rows: `{accepted}`
- Configuration: `K=4`, `M={PHASE_SAMPLES}`, `N={CURVE_SAMPLES}`, shared `epsilon={PERTURBATION_SCALE:.1e}`
- Paper snapshot times: `{SNAPSHOTS_DAYS}` days
- Internal numerical acceptance: `{'pass' if numerical_pass else 'fail'}`
- Configuration-reach diagnostic: `{'pass' if configuration_pass else 'fail'}`
- Paper projection acceptance: `{REPRODUCTION_LOCK.paper_projection_acceptance}`
- Paper 3D equivalence: `false`
- Epsilon selection status: `{REPRODUCTION_LOCK.epsilon_selection_status}`
- Frozen holdout: `{REPRODUCTION_LOCK.holdout_passes}/{REPRODUCTION_LOCK.holdout_rows}` panels passed (`{REPRODUCTION_LOCK.paper_projection_status}`)
- Proxy background: `false`
- Machine-readable arrays: `{NPZ_PATH.relative_to(ROOT).as_posix()}`

| Figure | day | fixed-time surface x | fixed-time surface y | fixed-time surface z | nonlinear/STM ratio | independent error | numerical | configuration reach |
|---|---:|---:|---:|---:|---:|---:|---|---|
{table_rows}

## Numerical gates

- snapshot-time error `<= {TIME_ERROR_LIMIT_DAYS:.1e}` day;
- source residual `<= {SOURCE_RESIDUAL_LIMIT:.1e}`;
- `abs(det(DG)-1) <= {DG_DETERMINANT_ERROR_LIMIT:.1e}`;
- selected unstable eigenvalue relative imaginary part `<= {EIGEN_RELATIVE_IMAGINARY_LIMIT:.1e}`;
- source-curve Jacobi span `<= {SOURCE_JACOBI_SPAN_LIMIT:.1e}`;
- maximum per-curve Jacobi drift across combined history and snapshot samples `<= {JACOBI_DRIFT_LIMIT:.1e}`;
- exact first-order reference `epsilon * ||Phi(t,0)d||` from the base-trajectory
  STM, with the local-history maximum relative error `<=
  {LOCAL_LINEARIZATION_RELATIVE_ERROR_LIMIT:.1e}` while the predicted state
  separation is `<= {LOCAL_LINEAR_REFERENCE_MULTIPLIER:.0f}*epsilon`;
- far-field nonlinear/STM ratios are retained as diagnostics only because the
  globally propagated manifold is expected to leave the linear neighborhood;
- batched-versus-independent representative-state maximum absolute error `<= {INDEPENDENT_ERROR_LIMIT:.1e}`;
- `K=4`, `M>={PHASE_SAMPLES}`, `N={CURVE_SAMPLES}`, all stored values finite, proxy background false.

## Configuration reach and claim boundary

Figure 4.3 requires nondecreasing fixed-time full-surface `x_max` and final
`x_max >= 1.02`. Figure 4.4 requires nonincreasing full-surface `x_min` and
final `x_min <= 0.72`. The red surface at each paper time is the complete
fixed-time torus window `tau + phase`; the black trajectory history over
`[0, tau]` is audited separately and its full xyz ranges are retained in the
CSV and NPZ.

The numerical gates establish a proxy-free corrected-DG propagation. The
epsilon and paper camera are locked from development panels, but the separately
committed panel-(d) projection holdout failed `0/4`. Therefore these reach checks
remain project configuration diagnostics, paper projection acceptance is
`{REPRODUCTION_LOCK.paper_projection_acceptance}`, and 3D equivalence is false.
""",
        encoding="utf-8",
    )
    print(CSV_PATH)
    print(NPZ_PATH)
    print(DOC_PATH)
    print(f"accepted={accepted}/{len(rows)}")


if __name__ == "__main__":
    main()
