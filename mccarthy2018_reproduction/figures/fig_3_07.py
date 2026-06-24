"""Figure 3.7: constant-energy quasi-vertical torus family."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import integrate_cr3bp
from qp_orbits.linear_modes import center_modes
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import (
    corrected_l1_constant_energy_vertical_staged_corrections,
    resample_corrected_torus_surface,
    sweep_corrected_curve_correction,
)


FIGURE_ID = "3.7"
SOURCE_PAGE = 70
REPRO_LEVEL = "physical-consistency"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected fixed-JC tori from the staged N=9, 15, 21, 27, and 33 quasi-vertical branch."


def style_axis(ax, equilibrium_x: float, label: str) -> None:
    ax.scatter([equilibrium_x], [0.0], [0.0], color="#cc4c25", s=9)
    ax.text(equilibrium_x + 0.004, 0.010, 0.012, r"$L_1$", fontsize=14)
    ax.set_xlim(0.815, 0.890)
    ax.set_ylim(-0.115, 0.115)
    ax.set_zlim(-0.115, 0.115)
    ax.set_xlabel("X [nd]", labelpad=-7)
    ax.set_ylabel("Y [nd]", labelpad=-4)
    ax.set_zlabel("Z [nd]", labelpad=-7)
    ax.set_xticks([0.82, 0.84, 0.86, 0.88])
    ax.set_yticks([-0.1, -0.05, 0.0, 0.05, 0.1])
    ax.set_zticks([-0.1, -0.05, 0.0, 0.05, 0.1])
    ax.tick_params(labelsize=8, pad=-2)
    ax.view_init(elev=26, azim=-126)
    ax.set_box_aspect((0.85, 1.7, 1.7))
    ax.text2D(0.47, -0.10, label, transform=ax.transAxes, fontsize=12)
    ax.annotate(
        "To Earth",
        xy=(0.09, 0.10),
        xytext=(0.28, 0.19),
        xycoords="axes fraction",
        fontsize=11,
        rotation=-27,
        arrowprops={"arrowstyle": "-|>", "lw": 1.5, "color": "black"},
    )


def main() -> None:
    apply_style()
    system = SYSTEMS["earth_moon"]
    modes = center_modes(system.mu, point="L1")
    corrections = corrected_l1_constant_energy_vertical_staged_corrections(system.mu)
    target_times = (12.87, 12.85, 12.78, 12.66)
    selected = [
        min(
            corrections,
            key=lambda correction: abs(
                correction.mapping_time * system.time_unit_days - target_time
            ),
        )
        for target_time in target_times
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
        style_axis(ax, modes.equilibrium_state[0], label)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
