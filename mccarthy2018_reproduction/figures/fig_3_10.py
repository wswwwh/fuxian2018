"""Figure 3.10: period-2, period-3, and period-8 halo examples."""

from __future__ import annotations

import csv

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.periodic_orbits import period_q_halo_examples
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.variational import integrate_state_and_stm, unpack_augmented


FIGURE_ID = "3.10"
SOURCE_PAGE = 72
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Floquet-seeded period-q branches corrected by STM multiple shooting."


def _complex_values(values: np.ndarray) -> str:
    return ";".join(f"{value.real:.16g}{value.imag:+.16g}j" for value in values)


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
    for example in examples:
        corrected = example.corrected
        bifurcation = example.bifurcation
        terminal_state, monodromy_matrix, monodromy_eigenvalues = _monodromy_for_orbit(
            corrected.orbit
        )
        _, base_monodromy_matrix, base_monodromy_eigenvalues = _monodromy_for_orbit(
            bifurcation.orbit
        )
        jacobi_values = jacobi_constant(example.trajectory, system.mu)
        target_angle = 2.0 * np.pi / example.resonance
        continuity_norm = float(np.linalg.norm(corrected.continuity_errors))
        terminal_symmetry_norm = float(np.linalg.norm(corrected.terminal_symmetry_error))
        closure_error = float(np.linalg.norm(terminal_state - corrected.orbit.initial_state))
        trajectory_closure = float(np.linalg.norm(example.trajectory[-1] - example.trajectory[0]))

        prefix = f"q{example.resonance}"
        npz_payload[f"{prefix}_trajectory"] = example.trajectory
        npz_payload[f"{prefix}_patch_states"] = corrected.patch_states
        npz_payload[f"{prefix}_continuity_errors"] = corrected.continuity_errors
        npz_payload[f"{prefix}_terminal_symmetry_error"] = corrected.terminal_symmetry_error
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
            "trajectory_jacobi_drift": float(np.ptp(jacobi_values)),
            "segments": corrected.patch_states.shape[0],
            "segment_duration_nd": corrected.segment_duration,
        }
        rows.append(row)

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
    np.savez_compressed(npz_path, **npz_payload)
    print(f"Wrote {csv_path}")
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
