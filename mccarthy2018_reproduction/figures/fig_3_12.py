"""Figure 3.12: constant-frequency quasi-halo tori."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import integrate_cr3bp
from qp_orbits.libration_points import compute_libration_points
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l2_constant_frequency_halo_energy_corrections,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.12"
SOURCE_PAGE = 76
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected fixed-ratio tori at the four thesis Jacobi constants."


def style_axis(ax, label: str) -> None:
    system = SYSTEMS["earth_moon"]
    points = compute_libration_points(system.mu)
    moon_x = 1.0 - system.mu
    ax.scatter([points["L2"].x], [0.0], [0.0], color="#cc4c25", s=9)
    ax.scatter([moon_x], [0.0], [0.0], color="black", s=9)
    ax.text(points["L2"].x - 0.020, 0.006, 0.0, r"$L_2$", fontsize=9)
    ax.text(moon_x - 0.015, -0.010, 0.0, "Moon", fontsize=8)
    ax.set_xlim(0.92, 1.24)
    ax.set_ylim(-0.32, 0.32)
    ax.set_zlim(-0.27, 0.24)
    ax.set_xlabel("X [nd]", labelpad=-6)
    ax.set_ylabel("Y [nd]", labelpad=-5)
    ax.set_zlabel("Z [nd]", labelpad=-6)
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=24, azim=-132)
    ax.set_box_aspect((1.0, 1.65, 1.45))
    ax.text2D(0.47, -0.10, label, transform=ax.transAxes, fontsize=12)
    ax.annotate(
        "To Earth",
        xy=(0.10, 0.10),
        xytext=(0.28, 0.20),
        xycoords="axes fraction",
        arrowprops={"arrowstyle": "-|>", "lw": 1.4},
        fontsize=10,
        rotation=-28,
    )


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    corrections = corrected_l2_constant_frequency_halo_energy_corrections(system.mu)
    target_jacobi = (3.1182, 3.0876, 3.0364, 3.0011)
    selected = [
        min(corrections, key=lambda correction: abs(correction.target_jacobi - target))
        for target in target_jacobi
    ]
    family = [
        sweep_corrected_curve_correction(correction, time_samples=32)
        for correction in selected
    ]

    seed = selected[0].seed
    orbit_times = np.linspace(0.0, seed.orbit_period, 360)
    central_solution = integrate_cr3bp(
        seed.orbit_state,
        (0.0, seed.orbit_period),
        system.mu,
        t_eval=orbit_times,
        max_step=0.01,
    )
    if not central_solution.success:
        raise RuntimeError(central_solution.message)
    central_orbit = central_solution.y[:3].T

    fig = plt.figure(figsize=(8.2, 7.6), constrained_layout=True)
    labels = ["(a)", "(b)", "(c)", "(d)"]
    for idx, (member, label) in enumerate(zip(family, labels), start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d", computed_zorder=False)
        surface, _ = resample_corrected_torus_surface(member, phase_samples=112)
        ax.plot_surface(
            surface[:, :, 0],
            surface[:, :, 1],
            surface[:, :, 2],
            color="#b8b8b8",
            edgecolor="none",
            linewidth=0,
            antialiased=True,
            shade=False,
            alpha=1.0,
            rcount=surface.shape[0],
            ccount=surface.shape[1],
            zorder=1,
        )
        ax.plot(
            central_orbit[:, 0],
            central_orbit[:, 1],
            central_orbit[:, 2],
            color="#1f77b4",
            linewidth=1.2,
            zorder=10,
        )
        style_axis(ax, label)
    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
