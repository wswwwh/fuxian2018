"""Figure 3.10: period-2, period-3, and period-8 halo examples."""

from __future__ import annotations

import csv

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.periodic_orbits import (
    audit_spatial_multiple_shooting_orbit,
    period_q_halo_examples,
)
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.variational import integrate_state_and_stm, unpack_augmented


FIGURE_ID = "3.10"
SOURCE_PAGE = 72
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Floquet-seeded period-q branches corrected by STM multiple shooting."


def _complex_values(values: np.ndarray) -> str:
    return ";".join(f"{value.real:.16g}{value.imag:+.16g}j" for value in values)


def _float_values(values: np.ndarray) -> str:
    return ";".join(f"{float(value):.16g}" for value in values)


def _monodromy_for_orbit(orbit):
    solution = integrate_state_and_stm(
        orbit.initial_state,
        (0.0, orbit.period),
        orbit.mu,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    terminal_state, matrix = unpack_augmented(solution.y[:, -1])
    eigenvalues = np.linalg.eigvals(matrix)
    return terminal_state, matrix, eigenvalues


def write_period_q_validation(examples) -> None:
    output_dir = PROJECT_ROOT / "data" / "computed"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "period_q_halo_examples.csv"
    npz_path = output_dir / "period_q_halo_examples.npz"
    audit_csv_path = output_dir / "period_q_halo_closure_audit.csv"
    system = SYSTEMS["earth_moon"]

    fieldnames = [
        "resonance",
        "initial_state_x",
        "initial_state_y",
        "initial_state_z",
        "initial_state_xdot",
        "initial_state_ydot",
        "initial_state_zdot",
        "period_nd",
        "period_days",
        "jacobi",
        "bifurcation_initial_state_x",
        "bifurcation_initial_state_y",
        "bifurcation_initial_state_z",
        "bifurcation_initial_state_xdot",
        "bifurcation_initial_state_ydot",
        "bifurcation_initial_state_zdot",
        "bifurcation_period_nd",
        "bifurcation_jacobi",
        "floquet_multiplier_real",
        "floquet_multiplier_imag",
        "floquet_multiplier_abs",
        "resonance_angle_rad",
        "target_resonance_angle_rad",
        "resonance_angle_error_rad",
        "frequency_ratio",
        "bifurcation_periodicity_error",
        "bifurcation_monodromy_multipliers",
        "corrected_monodromy_multipliers",
        "corrected_max_multiplier_abs",
        "corrected_min_multiplier_abs",
        "multiple_shooting_residual_norm",
        "max_continuity_residual",
        "continuity_residual_norm",
        "terminal_symmetry_residual_norm",
        "orbit_closure_error",
        "trajectory_closure_error",
        "trajectory_jacobi_drift",
        "segments",
        "segment_duration_nd",
    ]
    audit_fieldnames = [
        "resonance",
        "period_nd",
        "half_period_nd",
        "segments",
        "segment_duration_nd",
        "segment_duration_consistency_error",
        "patch_to_patch_continuity_residual_norm",
        "max_patch_to_patch_continuity_residual",
        "terminal_symmetry_residual_norm",
        "multiple_shooting_residual_norm",
        "full_period_single_shoot_closure_error",
        "half_period_single_shoot_symmetry_error",
        "trajectory_sampling_closure_error",
        "trajectory_jacobi_drift",
        "full_period_single_shoot_jacobi_drift",
        "monodromy_multiplier_magnitudes",
        "max_monodromy_multiplier_abs",
        "min_monodromy_multiplier_abs",
        "per_segment_endpoint_errors",
        "diagnosis",
    ]

    npz_payload: dict[str, np.ndarray] = {
        "resonance": np.array([example.resonance for example in examples], dtype=int),
        "initial_states": np.vstack([example.corrected.orbit.initial_state for example in examples]),
        "periods_nd": np.array([example.corrected.orbit.period for example in examples], dtype=float),
        "jacobi": np.array([example.corrected.orbit.jacobi for example in examples], dtype=float),
        "resonance_angles_rad": np.array(
            [example.bifurcation.rotation_angle_rad for example in examples],
            dtype=float,
        ),
        "resonance_angle_errors_rad": np.array(
            [
                example.bifurcation.rotation_angle_rad - 2.0 * np.pi / example.resonance
                for example in examples
            ],
            dtype=float,
        ),
    }

    rows = []
    audit_rows = []
    for example in examples:
        corrected = example.corrected
        bifurcation = example.bifurcation
        audit = audit_spatial_multiple_shooting_orbit(
            corrected,
            trajectory=example.trajectory,
        )
        terminal_state = audit.full_period_terminal_state
        monodromy_matrix = audit.monodromy_matrix
        monodromy_eigenvalues = audit.monodromy_multipliers
        _, base_monodromy_matrix, base_monodromy_eigenvalues = _monodromy_for_orbit(
            bifurcation.orbit
        )
        target_angle = 2.0 * np.pi / example.resonance
        continuity_norm = audit.patch_to_patch_continuity_norm
        terminal_symmetry_norm = audit.terminal_symmetry_residual_norm
        closure_error = audit.full_period_single_shoot_closure_error
        trajectory_closure = audit.trajectory_sampling_closure_error

        if example.resonance == 8 and closure_error > 1.0:
            diagnosis = (
                "B: single-arc divergence on a highly unstable corrected half-period "
                "multiple-shooting orbit; period and reflection definitions are consistent"
            )
        elif closure_error < 1.0e-6:
            diagnosis = "single-shoot and multiple-shooting closure agree at validation scale"
        else:
            diagnosis = "single-shoot closure is weaker than patch-local closure"

        prefix = f"q{example.resonance}"
        npz_payload[f"{prefix}_trajectory"] = example.trajectory
        npz_payload[f"{prefix}_patch_states"] = corrected.patch_states
        npz_payload[f"{prefix}_continuity_errors"] = corrected.continuity_errors
        npz_payload[f"{prefix}_terminal_symmetry_error"] = corrected.terminal_symmetry_error
        npz_payload[f"{prefix}_per_segment_endpoint_errors"] = audit.per_segment_endpoint_errors
        npz_payload[f"{prefix}_monodromy_matrix"] = monodromy_matrix
        npz_payload[f"{prefix}_monodromy_multipliers"] = monodromy_eigenvalues
        npz_payload[f"{prefix}_bifurcation_monodromy_matrix"] = base_monodromy_matrix
        npz_payload[f"{prefix}_bifurcation_monodromy_multipliers"] = base_monodromy_eigenvalues

        row = {
            "resonance": example.resonance,
            "initial_state_x": corrected.orbit.initial_state[0],
            "initial_state_y": corrected.orbit.initial_state[1],
            "initial_state_z": corrected.orbit.initial_state[2],
            "initial_state_xdot": corrected.orbit.initial_state[3],
            "initial_state_ydot": corrected.orbit.initial_state[4],
            "initial_state_zdot": corrected.orbit.initial_state[5],
            "period_nd": corrected.orbit.period,
            "period_days": corrected.orbit.period * (system.time_unit_days or 1.0),
            "jacobi": corrected.orbit.jacobi,
            "bifurcation_initial_state_x": bifurcation.orbit.initial_state[0],
            "bifurcation_initial_state_y": bifurcation.orbit.initial_state[1],
            "bifurcation_initial_state_z": bifurcation.orbit.initial_state[2],
            "bifurcation_initial_state_xdot": bifurcation.orbit.initial_state[3],
            "bifurcation_initial_state_ydot": bifurcation.orbit.initial_state[4],
            "bifurcation_initial_state_zdot": bifurcation.orbit.initial_state[5],
            "bifurcation_period_nd": bifurcation.orbit.period,
            "bifurcation_jacobi": bifurcation.orbit.jacobi,
            "floquet_multiplier_real": bifurcation.eigenvalue.real,
            "floquet_multiplier_imag": bifurcation.eigenvalue.imag,
            "floquet_multiplier_abs": abs(bifurcation.eigenvalue),
            "resonance_angle_rad": bifurcation.rotation_angle_rad,
            "target_resonance_angle_rad": target_angle,
            "resonance_angle_error_rad": bifurcation.rotation_angle_rad - target_angle,
            "frequency_ratio": bifurcation.frequency_ratio,
            "bifurcation_periodicity_error": bifurcation.periodicity_error,
            "bifurcation_monodromy_multipliers": _complex_values(base_monodromy_eigenvalues),
            "corrected_monodromy_multipliers": _complex_values(monodromy_eigenvalues),
            "corrected_max_multiplier_abs": float(np.max(np.abs(monodromy_eigenvalues))),
            "corrected_min_multiplier_abs": float(np.min(np.abs(monodromy_eigenvalues))),
            "multiple_shooting_residual_norm": corrected.orbit.iterations[-1].residual_norm,
            "max_continuity_residual": float(np.max(corrected.continuity_errors)),
            "continuity_residual_norm": continuity_norm,
            "terminal_symmetry_residual_norm": terminal_symmetry_norm,
            "orbit_closure_error": closure_error,
            "trajectory_closure_error": trajectory_closure,
            "trajectory_jacobi_drift": audit.trajectory_jacobi_drift,
            "segments": corrected.patch_states.shape[0],
            "segment_duration_nd": corrected.segment_duration,
        }
        rows.append(row)
        audit_rows.append(
            {
                "resonance": example.resonance,
                "period_nd": corrected.orbit.period,
                "half_period_nd": corrected.orbit.half_period,
                "segments": corrected.patch_states.shape[0],
                "segment_duration_nd": corrected.segment_duration,
                "segment_duration_consistency_error": audit.segment_duration_consistency_error,
                "patch_to_patch_continuity_residual_norm": audit.patch_to_patch_continuity_norm,
                "max_patch_to_patch_continuity_residual": audit.patch_to_patch_continuity_max,
                "terminal_symmetry_residual_norm": audit.terminal_symmetry_residual_norm,
                "multiple_shooting_residual_norm": audit.multiple_shooting_residual_norm,
                "full_period_single_shoot_closure_error": audit.full_period_single_shoot_closure_error,
                "half_period_single_shoot_symmetry_error": audit.half_period_single_shoot_symmetry_error,
                "trajectory_sampling_closure_error": audit.trajectory_sampling_closure_error,
                "trajectory_jacobi_drift": audit.trajectory_jacobi_drift,
                "full_period_single_shoot_jacobi_drift": audit.full_period_single_shoot_jacobi_drift,
                "monodromy_multiplier_magnitudes": _float_values(audit.monodromy_multiplier_magnitudes),
                "max_monodromy_multiplier_abs": float(np.max(audit.monodromy_multiplier_magnitudes)),
                "min_monodromy_multiplier_abs": float(np.min(audit.monodromy_multiplier_magnitudes)),
                "per_segment_endpoint_errors": _float_values(audit.per_segment_endpoint_errors),
                "diagnosis": diagnosis,
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )
    with audit_csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=audit_fieldnames)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(
                {
                    key: f"{value:.16g}" if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )
    np.savez_compressed(npz_path, **npz_payload)
    print(f"Wrote {csv_path}")
    print(f"Wrote {audit_csv_path}")
    print(f"Wrote {npz_path}")


def style_axis(ax, label: str) -> None:
    points = compute_libration_points(SYSTEMS["earth_moon"].mu)
    moon_x = 1.0 - SYSTEMS["earth_moon"].mu
    ax.scatter([points["L1"].x], [0.0], [0.0], color="#cc4c25", s=10)
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=10)
    ax.text(points["L1"].x + 0.008, 0.003, 0.0, r"$L_1$", fontsize=8)
    ax.text(moon_x - 0.018, -0.012, -0.018, "Moon", fontsize=8)
    ax.set_xlim(0.70, 1.18)
    ax.set_ylim(-0.16, 0.16)
    ax.set_zlim(-0.20, 0.20)
    ax.set_xlabel("X [nd]", labelpad=-8)
    ax.set_ylabel("Y [nd]", labelpad=-7)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.tick_params(labelsize=7, pad=-3)
    ax.view_init(elev=18, azim=-60)
    ax.set_box_aspect((1.25, 0.92, 1.10))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_facecolor((1.0, 1.0, 1.0, 0.0))
        axis._axinfo["grid"]["color"] = (0.86, 0.86, 0.86, 0.55)
        axis._axinfo["grid"]["linewidth"] = 0.35
    ax.text2D(0.48, -0.10, label, transform=ax.transAxes, fontsize=11)


def main() -> None:
    apply_style()
    examples = {
        example.resonance: example
        for example in period_q_halo_examples(SYSTEMS["earth_moon"].mu)
    }
    write_period_q_validation(tuple(examples[resonance] for resonance in [2, 3, 8]))
    fig = plt.figure(figsize=(7.4, 6.2))
    axes = [
        fig.add_axes([0.05, 0.54, 0.40, 0.40], projection="3d"),
        fig.add_axes([0.54, 0.54, 0.40, 0.40], projection="3d"),
        fig.add_axes([0.18, 0.08, 0.43, 0.40], projection="3d"),
    ]
    for ax, resonance, label in zip(axes, [2, 3, 8], ["(a)", "(b)", "(c)"]):
        path = examples[resonance].trajectory
        ax.plot(path[:, 0], path[:, 1], path[:, 2], color="#168bd2", linewidth=1.05)
        style_axis(ax, label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
