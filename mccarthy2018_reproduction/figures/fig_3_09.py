"""Figure 3.9: frequency ratio versus mapping time."""

from __future__ import annotations

import matplotlib.pyplot as plt

from _figure_paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.periodic_orbits import constant_energy_periodic_boundaries
from qp_orbits.plot_style import apply_style, save_figure
from qp_orbits.quasi_torus import frequency_ratio_curves
from qp_orbits.quasi_torus import (
    corrected_l1_constant_energy_halo_high_order_corrections,
    corrected_l1_constant_energy_halo_pseudo_arclength_corrections,
    corrected_l1_constant_energy_vertical_staged_corrections,
)


FIGURE_ID = "3.9"
SOURCE_PAGE = 71
REPRO_LEVEL = "shape-match + local numerical"
SYSTEM = "Earth-Moon CR3BP"
NOTES = "Corrected vertical frequency curve and corrected halo continuation through 12.408 days with a proxy tail."


def main() -> None:
    apply_style()
    curves = frequency_ratio_curves(samples=90)
    halo = curves["quasi_halo"]
    system = SYSTEMS["earth_moon"]
    low_halo = corrected_l1_constant_energy_halo_pseudo_arclength_corrections(
        system.mu,
        members=27,
    )
    n15_halo = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=27,
        samples=15,
        max_iterations=48,
        tolerance=5.0e-10,
    )
    n21_halo = corrected_l1_constant_energy_halo_high_order_corrections(
        system.mu,
        members=15,
        samples=21,
        max_iterations=48,
        tolerance=2.0e-10,
    )
    corrected_halo = list(low_halo)
    for branch in (n15_halo, n21_halo):
        cutoff = corrected_halo[-1].mapping_time
        corrected_halo.extend(
            correction for correction in branch if correction.mapping_time > cutoff + 1.0e-10
        )
    corrected_vertical = corrected_l1_constant_energy_vertical_staged_corrections(system.mu)
    boundaries = {
        point.family_label: point
        for point in constant_energy_periodic_boundaries(SYSTEMS["earth_moon"], target_jacobi=3.1389)
    }

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.25), constrained_layout=True)
    axes[0].plot(
        [row["mapping_time_days"] for row in halo],
        [row["frequency_ratio"] for row in halo],
        color="#9a9a9a",
        linestyle="--",
        linewidth=1.0,
    )
    axes[0].plot(
        [correction.mapping_time * system.time_unit_days for correction in corrected_halo],
        [2.0 * 3.141592653589793 / correction.rotation_angle_rad for correction in corrected_halo],
        color="#1f77b4",
        linewidth=1.8,
    )
    halo_boundary = boundaries["quasi_halo"]
    axes[0].scatter(
        [halo_boundary.mapping_time_days],
        [halo_boundary.frequency_ratio],
        color="#16856b",
        s=32,
        zorder=4,
        label="corrected periodic boundary",
    )
    axes[0].set_title("Quasi-Halo Family\nConstant Energy (JC = 3.1389)", fontsize=10, weight="bold")
    axes[0].set_xlabel("Mapping Time [days]")
    axes[0].set_ylabel(r"$\omega_0/\omega_1$")
    axes[0].set_xlim(12.0, 12.5)
    axes[0].set_ylim(5.0, 45.0)
    axes[0].grid(True, alpha=0.24)
    axes[0].legend(loc="upper left", fontsize=7, frameon=False)

    axes[1].plot(
        [correction.mapping_time * system.time_unit_days for correction in reversed(corrected_vertical)],
        [
            2.0 * 3.141592653589793 / correction.rotation_angle_rad
            for correction in reversed(corrected_vertical)
        ],
        color="#1f77b4",
        linewidth=1.8,
    )
    vertical_boundary = boundaries["quasi_vertical"]
    axes[1].scatter(
        [vertical_boundary.mapping_time_days],
        [vertical_boundary.frequency_ratio],
        color="#16856b",
        s=32,
        zorder=4,
        label="corrected periodic boundary",
    )
    axes[1].set_title("Quasi-Vertical Family\nConstant Energy (JC = 3.1389)", fontsize=10, weight="bold")
    axes[1].set_xlabel("Mapping Time [days]")
    axes[1].set_ylabel(r"$\omega_0/\omega_1$")
    axes[1].set_xlim(12.6, 12.9)
    axes[1].set_ylim(15.0, 50.0)
    axes[1].grid(True, alpha=0.24)
    axes[1].legend(loc="upper right", fontsize=7, frameon=False)

    save_figure(fig, FIGURE_ID, PROJECT_ROOT)
    plt.close(fig)


if __name__ == "__main__":
    main()
