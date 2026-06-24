"""Figure 3.5: constant-energy quasi-halo torus family."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import integrate_cr3bp
from qp_orbits.linear_modes import center_modes
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l1_constant_energy_halo_high_order_corrections,
    corrected_l1_constant_energy_halo_pseudo_arclength_corrections,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.5"
SOURCE_PAGE = 68
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "All panels use corrected fixed-JC tori from the staged N=9, N=15, and N=21 branches."


def style_torus_axis(ax, equilibrium_x: float, label: str) -> None:
    ax.scatter([equilibrium_x], [0.0], [0.0], color="#cc4c25", s=9)
    ax.text(equilibrium_x + 0.004, 0.008, 0.0, r"$L_1$", fontsize=14)
    ax.set_xlim(0.810, 0.875)
    ax.set_ylim(-0.130, 0.130)
    ax.set_zlim(-0.115, 0.115)
    ax.set_xlabel("X [nd]", labelpad=-7)
    ax.set_ylabel("Y [nd]", labelpad=-4)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.set_xticks([0.82, 0.84, 0.86])
    ax.set_yticks([-0.1, -0.05, 0.0, 0.05, 0.1])
    ax.set_zticks([-0.10, -0.05, 0.0, 0.05, 0.10])
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=24, azim=-124)
    ax.set_box_aspect((0.75, 1.7, 1.45))
    ax.text2D(0.47, -0.10, label, transform=ax.transAxes, fontsize=12)
    ax.annotate(
        "To Earth",
        xy=(0.09, 0.09),
        xytext=(0.28, 0.18),
        xycoords="axes fraction",
        fontsize=11,
        rotation=-27,
        arrowprops={"arrowstyle": "-|>", "lw": 1.5, "color": "black"},
    )


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    modes = center_modes(system.mu, point="L1")
    low_order = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
        system.mu,
        members=27,
    )
    n15 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=27,
        samples=15,
        max_iterations=48,
        tolerance=5.0e-10,
    )
    n21 = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=15,
        samples=21,
        max_iterations=48,
        tolerance=2.0e-10,
    )
    branches = (low_order, n15, n15, n21)
    target_times = (12.03, 12.09, 12.26, 12.40)
    selected = [
        min(
            branch,
            key=lambda correction: abs(
                correction.mapping_time * system.time_unit_days - target_time
            ),
        )
        for branch, target_time in zip(branches, target_times)
    ]
    family = [
        sweep_corrected_curve_correction(correction, time_samples=28)
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
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        surface, _ = resample_corrected_torus_surface(member, phase_samples=96)
        ax.plot_surface(
            surface[:, :, 0],
            surface[:, :, 1],
            surface[:, :, 2],
            color="#b8b8b8",
            edgecolor="none",
            linewidth=0,
            antialiased=False,
            shade=True,
            alpha=1.0,
            rcount=surface.shape[0],
            ccount=surface.shape[1],
        )
        ax.plot(
            central_orbit[:, 0],
            central_orbit[:, 1],
            central_orbit[:, 2],
            color="#1f77b4",
            linewidth=1.0,
        )
        style_torus_axis(ax, modes.equilibrium_state[0], label)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
